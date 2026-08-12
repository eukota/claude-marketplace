#!/usr/bin/env python3
"""Bootstrap a mind from existing Claude Code chat history.

Walks transcript JSONL, pairs each real user turn with the assistant turn it
responded to, classifies the pair, and writes decisions and corrections into a
brain using the ORIGINAL transcript timestamps — so temporal decay reflects
when a preference was actually expressed, not when it was imported.

Signal quality, strongest first (see projects/meldwerkes/notes.md):
  1. corrections   — contrastive: the rejected and preferred option together
  2. directives    — explicit statements of preference
  3. answers       — real, but mixed with local project facts

Usage:
  python3 bootstrap.py --brain-id <id> --dry-run
  python3 bootstrap.py --brain-id <id> --since 2026-01-01 --limit 500
"""

import argparse
import json
import os
import sys
import uuid
from collections import Counter
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from memory import (MemoryStore, Decision, Correction, DEFAULT_DB,
                    effective_confidence)

TRANSCRIPT_DIR = Path.home() / ".claude" / "projects"
MODEL = "claude-sonnet-4-6"  # matches compress.py
BATCH = 20

CLASSIFY_PROMPT = """You are extracting durable preferences from a developer's chat history.

For each numbered exchange below, decide whether the USER message reveals a
DURABLE PREFERENCE — something that would apply again in a future, different
situation — or merely a LOCAL FACT about one task.

  "I prefer explicit error handling over clever abstractions"  -> durable
  "use Postgres for this project"                              -> local fact
  "no, don't refactor the whole file, just fix the bug"        -> durable
  "the file is at src/main.py"                                 -> local fact

Classify each as exactly one of:
  correction — the user pushed back on what the assistant did
  directive  — an unprompted statement of preference or rule
  answer     — an answer to the assistant's question that reveals a preference
  none       — no durable preference (local facts, questions, chitchat, tasks)

Return ONLY a JSON array, one object per exchange, in order:
[{"n": 1, "kind": "correction", "principle": "one sentence, stated as a general preference", "confidence": 0.0-1.0}]

Use kind "none" with principle null when nothing durable is revealed. Be strict:
most messages are "none". Confidence reflects how clearly the message states a
preference that would generalize.

EXCHANGES:
"""


def iter_transcripts(root: Path, since: datetime | None):
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
    """Content is a string, or a list of blocks. Extract human-authored text."""
    if isinstance(content, str):
        return _clean(content)
    if isinstance(content, list):
        parts = [b.get("text", "") for b in content
                 if isinstance(b, dict) and b.get("type") == "text"]
        return _clean("\n".join(p for p in parts if p))
    return ""


def _clean(text: str) -> str:
    """Strip the transcript's display formatting (prompt marker, padding)."""
    return "\n".join(l.lstrip("\u276f ").rstrip() for l in text.splitlines()).strip()


def classify(client, batch):
    numbered = []
    for i, (_, asst, user, _) in enumerate(batch, 1):
        a = (asst[-600:] + "…") if len(asst) > 600 else asst
        u = (user[:900] + "…") if len(user) > 900 else user
        numbered.append(f"--- {i} ---\nASSISTANT: {a or '(start of conversation)'}\nUSER: {u}")
    resp = client.messages.create(
        model=MODEL, max_tokens=4096,
        messages=[{"role": "user", "content": CLASSIFY_PROMPT + "\n\n".join(numbered)}],
    )
    raw = "".join(b.text for b in resp.content if b.type == "text").strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1].lstrip("json").strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        print("  ! could not parse model output for this batch; skipping", file=sys.stderr)
        return []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--brain-id", required=True,
                    help="Write into this brain. Use a FRESH brain so the "
                         "import can be reviewed or discarded independently.")
    ap.add_argument("--transcripts", default=str(TRANSCRIPT_DIR))
    ap.add_argument("--since", help="Only exchanges on/after YYYY-MM-DD")
    ap.add_argument("--limit", type=int, help="Cap exchanges examined")
    ap.add_argument("--min-confidence", type=float, default=0.5)
    ap.add_argument("--dry-run", action="store_true",
                    help="Classify and report; write nothing")
    ap.add_argument("--db", default=str(DEFAULT_DB))
    args = ap.parse_args()

    root = Path(os.path.expanduser(args.transcripts))
    if not root.exists():
        sys.exit(f"No transcripts at {root}")

    since = datetime.fromisoformat(args.since) if args.since else None
    store = MemoryStore(Path(args.db))
    brain = store.get_brain(args.brain_id)
    if not brain:
        sys.exit(f"Brain {args.brain_id} not found. Create one with brain.py create.")

    exchanges = list(iter_transcripts(root, since))
    if args.limit:
        exchanges = exchanges[:args.limit]
    if not exchanges:
        sys.exit("No user turns found in transcripts.")

    print(f"Scanning {len(exchanges)} user turns from {root}")
    print(f"Target brain: {brain.name} ({brain.domain})")
    if args.dry_run:
        print("DRY RUN — nothing will be written\n")

    try:
        from anthropic import Anthropic
    except ImportError:
        sys.exit("anthropic SDK required: pip install anthropic")
    client = Anthropic()

    kinds = Counter()
    learned = []
    for i in range(0, len(exchanges), BATCH):
        batch = exchanges[i:i + BATCH]
        print(f"  classifying {i + 1}-{i + len(batch)} of {len(exchanges)}…", end="\r")
        for item in classify(client, batch):
            n = item.get("n", 0)
            if not (1 <= n <= len(batch)):
                continue
            kind, principle = item.get("kind", "none"), item.get("principle")
            conf = float(item.get("confidence") or 0)
            kinds[kind] += 1
            if kind == "none" or not principle or conf < args.min_confidence:
                continue
            ts, asst, user, source = batch[n - 1]
            learned.append({"timestamp": ts, "kind": kind, "principle": principle,
                            "confidence": conf, "user": user, "source": source})

            if args.dry_run:
                continue
            # Original timestamps preserved: decay should measure when the
            # preference was expressed, not when it was imported.
            d = Decision(id=str(uuid.uuid4()), brain_id=brain.id, timestamp=ts,
                         context=f"[bootstrap {source}] {asst[:400]}",
                         decision=user[:400], grounding="none",
                         confirmed=False if kind == "correction" else None)
            store.save_decision(d)
            if kind == "correction":
                store.save_correction(Correction(
                    id=str(uuid.uuid4()), decision_id=d.id, brain_id=brain.id,
                    timestamp=ts, user_feedback=user[:600],
                    principle_affected=principle))
    print(" " * 70, end="\r")
    report(brain, exchanges, kinds, learned, args)


def report(brain, exchanges, kinds, learned, args):
    dates = sorted(e[0] for e in exchanges if e[0])
    span = f"{dates[0][:10]} to {dates[-1][:10]}" if dates else "unknown"
    half_life = MemoryStore.load_settings().confidence_half_life_days
    now = datetime.now().isoformat()

    print("\n" + "=" * 72)
    print(f"BOOTSTRAP REPORT — {brain.name}")
    print("=" * 72)
    print(f"Transcript span     : {span}")
    print(f"User turns examined : {len(exchanges)}")
    print(f"Classified          : " + ", ".join(f"{k}={v}" for k, v in kinds.most_common()) or "none")
    print(f"Principles extracted: {len(learned)} (min confidence {args.min_confidence})")
    print(f"Confidence half-life: {half_life:g} days")
    if args.dry_run:
        print("Mode                : DRY RUN — nothing written")

    if not learned:
        print("\nNothing met the confidence threshold. Try --min-confidence 0.3.")
        return

    # Decay-adjusted, so stale principles sort down even if stated confidently
    for p in learned:
        p["effective"] = effective_confidence(p["confidence"], p["timestamp"], half_life, now)
    learned.sort(key=lambda p: p["effective"], reverse=True)

    print("\n" + "-" * 72)
    print("ESTABLISHED PRINCIPLES  (stated → effective after decay)")
    print("-" * 72)
    for p in learned:
        age = ""
        try:
            days = (datetime.fromisoformat(now) - datetime.fromisoformat(
                p["timestamp"].replace("Z", "+00:00")).replace(tzinfo=None)).days
            age = f"{days}d ago"
        except (ValueError, TypeError):
            pass
        print(f"\n  [{p['kind']:<10}] {p['confidence']:.2f} → {p['effective']:.2f}   {age}")
        print(f"  {p['principle']}")

    stale = [p for p in learned if p["effective"] < p["confidence"] * 0.5]
    print("\n" + "-" * 72)
    print(f"{len(stale)} principle(s) have decayed below half their stated confidence.")
    print("Review those before trusting them — they may reflect preferences you")
    print("have since changed.")
    print("\nCaveats worth holding: transcripts over-represent friction, so a mind")
    print("built only from them skews toward what went wrong. Review this list")
    print("before merging into a primary brain.")
    if not args.dry_run:
        print(f"\nWritten to brain {brain.id}. Run /pahf-compress to derive")
        print("meta-principles from the imported decisions.")


if __name__ == "__main__":
    main()
