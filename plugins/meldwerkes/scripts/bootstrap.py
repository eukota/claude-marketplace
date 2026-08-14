#!/usr/bin/env python3
"""Bootstrap minds from existing Claude Code chat history — in two phases.

  survey  Read transcripts, classify what is there, cluster by domain, and
          write an editable PLAN. Creates nothing.
  apply   Read the plan, create the minds it describes, and import the signals
          into them.

The plan file exists so the structure can be inspected and changed before any
mind is created. Rename a domain, merge two, drop one, or point a domain at an
existing brain — then apply. Bootstrap is the one moment the whole corpus is
visible at once, which is a better position for clustering than incremental
observation ever gets; the plan is where that view becomes editable.

Signal quality, strongest first:
  1. corrections — contrastive: the rejected and preferred option together
  2. directives  — explicit statements of preference
  3. answers     — real, but mixed with local project facts

Usage:
  python3 bootstrap.py survey --out plan.json [--since 2026-06-01] [--limit 400]
  python3 bootstrap.py apply  --plan plan.json [--dry-run]
"""

import argparse
import json
import os
import sys
import uuid
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from memory import (MemoryStore, Decision, Correction, DEFAULT_DB,
                    effective_confidence, checkpoint)
import llm

TRANSCRIPT_DIR = Path.home() / ".claude" / "projects"
BATCH = 20

CLASSIFY_PROMPT = """You are extracting durable preferences from a developer's chat history.

For each numbered exchange, decide whether the USER message reveals a DURABLE
PREFERENCE — something that would apply again in a future, different situation
— or merely a LOCAL FACT about one task.

  "I prefer explicit error handling over clever abstractions"  -> durable
  "use Postgres for this project"                              -> local fact
  "no, don't refactor the whole file, just fix the bug"        -> durable
  "the file is at src/main.py"                                 -> local fact

Classify each as exactly one of:
  correction — the user pushed back on what the assistant did
  directive  — an unprompted statement of preference or rule
  answer     — an answer to the assistant's question revealing a preference
  none       — no durable preference (facts, questions, chitchat, task requests)

Also assign a DOMAIN: a short lowercase slug for the area of judgment this
belongs to (e.g. code-review, architecture, writing, testing, tooling,
teaching, product). Infer it from the subject matter, not the project name.
Use "general" only when genuinely cross-cutting. Prefer reusing a domain you
have already used in this batch over inventing a near-synonym.

Return ONLY a JSON array, one object per exchange, in order:
[{"n": 1, "kind": "correction", "domain": "code-review",
  "principle": "one sentence, stated as a general preference",
  "confidence": 0.0-1.0}]

Use kind "none" with principle null when nothing durable is revealed. Be
strict: most messages are "none".

EXCHANGES:
"""


# ---------------------------------------------------------------- transcripts

def iter_transcripts(root: Path, since):
    """Yield (timestamp, assistant_text, user_text, source) for real user turns."""
    for f in sorted(root.rglob("*.jsonl")):
        last_assistant = ""
        for line in f.read_text(errors="ignore").splitlines():
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            typ = d.get("type")
            if typ not in ("user", "assistant"):
                continue
            text = _text_of(d.get("message", {}).get("content"))
            if typ == "assistant":
                if text:
                    last_assistant = text
                continue
            # Real user prompts carry promptSource; tool results and synthetic
            # turns do not. Skip anything that is not a person typing.
            if not text or not d.get("promptSource"):
                continue
            ts = d.get("timestamp", "")
            if since and ts:
                try:
                    if datetime.fromisoformat(ts.replace("Z", "+00:00")).replace(tzinfo=None) < since:
                        continue
                except ValueError:
                    pass
            yield ts, last_assistant, text, f.stem


def _text_of(content):
    if isinstance(content, str):
        return _clean(content)
    if isinstance(content, list):
        parts = [b.get("text", "") for b in content
                 if isinstance(b, dict) and b.get("type") == "text"]
        return _clean("\n".join(p for p in parts if p))
    return ""


def _clean(text: str) -> str:
    """Strip the transcript's display formatting (prompt marker, padding)."""
    return "\n".join(l.lstrip("❯ ").rstrip() for l in text.splitlines()).strip()


def classify(completer, batch):
    numbered = []
    for i, (_, asst, user, _) in enumerate(batch, 1):
        a = (asst[-600:] + "…") if len(asst) > 600 else asst
        u = (user[:900] + "…") if len(user) > 900 else user
        numbered.append(f"--- {i} ---\nASSISTANT: {a or '(start of conversation)'}\nUSER: {u}")
    raw = llm.strip_fence(
        completer.complete(CLASSIFY_PROMPT + "\n\n".join(numbered), max_tokens=4096))
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        print("  ! unparseable model output for this batch; skipped", file=sys.stderr)
        return []


# --------------------------------------------------------------------- survey

def cmd_survey(args):
    root = Path(os.path.expanduser(args.transcripts))
    if not root.exists():
        sys.exit(f"No transcripts at {root}")
    since = datetime.fromisoformat(args.since) if args.since else None

    exchanges = list(iter_transcripts(root, since))
    if args.limit:
        exchanges = exchanges[:args.limit]
    if not exchanges:
        sys.exit("No user turns found.")

    print(f"Surveying {len(exchanges)} user turns from {root}")
    print("Nothing will be created — this phase only proposes.\n")

    # Settle auth before the first billable call, not on failure partway in.
    batches = (len(exchanges) + BATCH - 1) // BATCH
    print(f"This will make {batches} model calls ({BATCH} exchanges per call).")
    completer = llm.Completer(llm.resolve_auth(args.auth))

    kinds, signals = Counter(), []
    for i in range(0, len(exchanges), BATCH):
        batch = exchanges[i:i + BATCH]
        print(f"  classifying {i + 1}-{i + len(batch)} of {len(exchanges)}…", end="\r")
        for item in classify(completer, batch):
            n = item.get("n", 0)
            if not (1 <= n <= len(batch)):
                continue
            kind = item.get("kind", "none")
            kinds[kind] += 1
            conf = float(item.get("confidence") or 0)
            principle = item.get("principle")
            if kind == "none" or not principle or conf < args.min_confidence:
                continue
            ts, asst, user, source = batch[n - 1]
            signals.append({
                "timestamp": ts, "kind": kind, "confidence": conf,
                "domain": (item.get("domain") or "general").strip().lower(),
                "principle": principle,
                "user": user[:600], "assistant": asst[:400], "source": source,
            })
    print(" " * 70, end="\r")

    by_domain = defaultdict(list)
    for s in signals:
        by_domain[s["domain"]].append(s)

    # Domains with too little signal cannot support a mind of their own; they
    # are proposed as merged rather than silently dropped.
    domains = {}
    for dom, group in by_domain.items():
        domains[dom] = {
            "count": len(group),
            "corrections": sum(1 for g in group if g["kind"] == "correction"),
            "create": len(group) >= args.min_signals,
            "brain_name": dom.replace("-", " ").title(),
            "brain_id": None,   # set this to import into an existing mind instead
        }

    dates = sorted(e[0] for e in exchanges if e[0])
    plan = {
        "created_at": datetime.now().isoformat(),
        "source": str(root),
        "span": [dates[0][:10], dates[-1][:10]] if dates else None,
        "examined": len(exchanges),
        "kinds": dict(kinds),
        "min_signals_for_own_mind": args.min_signals,
        "domains": domains,
        "signals": signals,
    }
    Path(args.out).write_text(json.dumps(plan, indent=2))
    report_survey(plan, args.out)


def report_survey(plan, out_path):
    print("=" * 72)
    print("SURVEY — what is in your history")
    print("=" * 72)
    print(f"Span      : {' to '.join(plan['span']) if plan['span'] else 'unknown'}")
    print(f"Examined  : {plan['examined']} user turns")
    print(f"Classified: " + ", ".join(f"{k}={v}" for k, v in
                                      sorted(plan["kinds"].items(), key=lambda kv: -kv[1])))
    print(f"Signals   : {len(plan['signals'])}")

    doms = sorted(plan["domains"].items(), key=lambda kv: -kv[1]["count"])
    if not doms:
        print("\nNo durable preferences found. Try --min-confidence 0.3.")
        return

    print("\n" + "-" * 72)
    print("SUGGESTED MINDS")
    print("-" * 72)
    print(f"{'domain':<22}{'signals':>9}{'corrections':>13}   proposed")
    for dom, d in doms:
        proposal = f"create '{d['brain_name']}'" if d["create"] else "too few — merge or skip"
        print(f"  {dom:<20}{d['count']:>9}{d['corrections']:>13}   {proposal}")

    by_dom = defaultdict(list)
    for s in plan["signals"]:
        by_dom[s["domain"]].append(s)
    print("\n" + "-" * 72)
    print("SAMPLE PRINCIPLES PER DOMAIN")
    print("-" * 72)
    for dom, d in doms[:6]:
        print(f"\n  [{dom}]")
        for s in sorted(by_dom[dom], key=lambda s: -s["confidence"])[:3]:
            print(f"    {s['confidence']:.2f}  {s['principle'][:66]}")

    print("\n" + "=" * 72)
    print(f"Plan written to {out_path}")
    print("=" * 72)
    print("Edit it before applying. In particular you can:")
    print("  • set  create: false   to skip a domain")
    print("  • change brain_name    to rename a proposed mind")
    print("  • set  brain_id        to import into an existing mind instead")
    print("  • edit a signal's domain to move it between minds")
    print("\nThen:  bootstrap.py apply --plan " + out_path + " --dry-run")


# ---------------------------------------------------------------------- apply

def cmd_apply(args):
    plan = json.loads(Path(args.plan).read_text())
    store = MemoryStore(Path(args.db))
    domains = plan["domains"]
    signals = plan["signals"]

    active = {d: cfg for d, cfg in domains.items()
              if cfg.get("create") or cfg.get("brain_id")}
    if not active:
        sys.exit("No domains marked for creation. Set create: true on at least one.")

    skipped = [s for s in signals if s["domain"] not in active]
    importing = [s for s in signals if s["domain"] in active]

    print(f"Plan: {len(active)} mind(s), {len(importing)} signal(s)"
          + (f", {len(skipped)} skipped" if skipped else ""))
    for dom, cfg in sorted(active.items(), key=lambda kv: -domains[kv[0]]["count"]):
        target = f"existing {cfg['brain_id'][:8]}" if cfg.get("brain_id") else f"new '{cfg['brain_name']}'"
        print(f"  {dom:<22} {domains[dom]['count']:>4} signals -> {target}")
    if args.dry_run:
        print("\nDRY RUN — nothing created or written.")
        return

    snap = checkpoint(Path(args.db), "pre-bootstrap")
    if snap:
        print(f"\nCheckpoint: {snap.name}")

    ids = {}
    for dom, cfg in active.items():
        if cfg.get("brain_id"):
            ids[dom] = cfg["brain_id"]
        else:
            b = store.create_brain(cfg["brain_name"], dom,
                                   f"Bootstrapped from chat history {plan.get('span')}")
            ids[dom] = b.id
            print(f"  created {b.name} ({b.id[:8]})")

    written = Counter()
    for s in importing:
        bid = ids[s["domain"]]
        # Original timestamps: decay should measure when a preference was
        # expressed, not when it was imported.
        d = Decision(id=str(uuid.uuid4()), brain_id=bid, timestamp=s["timestamp"],
                     context=f"[bootstrap {s['source']}] {s['assistant'][:400]}",
                     decision=s["user"][:400], grounding="none",
                     confirmed=False if s["kind"] == "correction" else None)
        store.save_decision(d)
        written[s["domain"]] += 1
        if s["kind"] == "correction":
            store.save_correction(Correction(
                id=str(uuid.uuid4()), decision_id=d.id, brain_id=bid,
                timestamp=s["timestamp"], user_feedback=s["user"][:600],
                principle_affected=s["principle"]))

    print("\n" + "=" * 72)
    print("IMPORTED")
    print("=" * 72)
    for dom, n in written.most_common():
        print(f"  {dom:<22} {n:>4} decisions -> {ids[dom][:8]}")
    if skipped:
        print(f"\n  {len(skipped)} signal(s) skipped (domains not marked for creation)")
    print("\nNo principles exist yet — imported material is decisions and")
    print("corrections. Run /pahf-compress per mind to derive principles:")
    for dom, bid in ids.items():
        print(f"  compress.py --brain-id {bid} --detect-split   # {dom}")
    if snap:
        print(f"\nUndo everything:  history.py restore --snapshot {snap.name}")


def main():
    ap = argparse.ArgumentParser()
    # --db must live on each subcommand: a parent-level optional declared after
    # add_subparsers is only accepted *before* the subcommand name.
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--db", default=str(DEFAULT_DB))
    sub = ap.add_subparsers(dest="cmd", required=True)

    sv = sub.add_parser("survey", parents=[common], help="analyze history and propose minds")
    sv.add_argument("--out", default="bootstrap-plan.json")
    sv.add_argument("--transcripts", default=str(TRANSCRIPT_DIR))
    sv.add_argument("--since", help="Only exchanges on/after YYYY-MM-DD")
    sv.add_argument("--limit", type=int)
    sv.add_argument("--min-confidence", type=float, default=0.5)
    sv.add_argument("--min-signals", type=int, default=15,
                    help="Signals a domain needs to justify its own mind")
    llm.add_auth_arg(sv)

    ap_ = sub.add_parser("apply", parents=[common], help="create the minds the plan describes")
    ap_.add_argument("--plan", required=True)
    ap_.add_argument("--dry-run", action="store_true")

    args = ap.parse_args()
    (cmd_survey if args.cmd == "survey" else cmd_apply)(args)


if __name__ == "__main__":
    main()
