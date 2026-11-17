#!/usr/bin/env python3
"""Automatic learning loop: drain captured prompts into decisions and proposals.

Capture (hooks/capture_prompt.py) appends every prompt to pending.jsonl. This
script classifies them, writes decisions, and queues distilled principles for
review. It is started detached and throttled by a SessionEnd hook, so it never
sits in the path of a turn.
"""

import hashlib
import json
import os
import sys
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import memory
import bootstrap
import compress
import llm
import scrub

MIN_NEW_ROWS = 20
MIN_HOURS_BETWEEN_RUNS = 6
FALLBACK_HOURS = 24


def pending_path() -> Path:
    return memory.DATA_DIR / "pending.jsonl"


# ------------------------------------------------------------------- intake

def read_new(pending: Path, offset: int):
    """Parse complete lines after `offset`. Returns (rows, new_offset).

    A trailing line without a newline is still being written, so it is left
    for the next run rather than skipped or half-parsed. A malformed complete
    line is skipped and the offset moves past it.
    """
    try:
        data = Path(pending).read_bytes()
    except FileNotFoundError:
        return [], 0
    if offset > len(data):
        offset = 0  # file was truncated or replaced; start over
    rows, pos = [], offset
    while True:
        nl = data.find(b"\n", pos)
        if nl == -1:
            break
        raw = data[pos:nl]
        pos = nl + 1
        try:
            row = json.loads(raw)
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        if isinstance(row, dict) and row.get("prompt"):
            row["_end"] = pos  # byte offset just past this line, for partial-run cursors
            rows.append(row)
    return rows, pos


def _cursor_file() -> Path:
    return memory.DATA_DIR / "auto-cursor.json"


def load_cursor() -> int:
    try:
        return int(json.loads(_cursor_file().read_text()).get("offset", 0))
    except Exception:
        return 0


def save_cursor(offset: int) -> None:
    memory.DATA_DIR.mkdir(parents=True, exist_ok=True)
    _cursor_file().write_text(json.dumps({"offset": offset}))


def should_run(new_rows: int, last_run_at: Optional[str], now: datetime,
               *, fallback: bool = False) -> bool:
    """Throttle: enough new prompts and enough time since the last run.

    The fallback check (SessionStart) covers sessions that died without a
    SessionEnd: any backlog at all counts once the last run is over a day old.
    """
    last = None
    if last_run_at:
        try:
            last = datetime.fromisoformat(last_run_at)
        except ValueError:
            last = None
    age = None if last is None else now - last
    if fallback:
        return new_rows > 0 and (age is None or age >= timedelta(hours=FALLBACK_HOURS))
    return new_rows >= MIN_NEW_ROWS and (age is None or age >= timedelta(hours=MIN_HOURS_BETWEEN_RUNS))


# --------------------------------------------------------------------- lock

class RunLock:
    """PID lock file: one processor at a time; a dead holder's lock is replaced."""

    def __init__(self):
        self.path = memory.DATA_DIR / "auto.lock"
        self.held = False

    def acquire(self) -> bool:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        for _ in range(2):
            try:
                fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            except FileExistsError:
                if self._holder_alive():
                    return False
                try:
                    self.path.unlink()
                except FileNotFoundError:
                    pass
                continue
            with os.fdopen(fd, "w") as f:
                f.write(str(os.getpid()))
            self.held = True
            return True
        return False

    def _holder_alive(self) -> bool:
        try:
            pid = int(self.path.read_text().strip())
            os.kill(pid, 0)
            return True
        except (ValueError, FileNotFoundError):
            return False
        except ProcessLookupError:
            return False
        except PermissionError:
            return True  # exists, owned by someone else

    def release(self) -> None:
        if self.held:
            try:
                self.path.unlink()
            except FileNotFoundError:
                pass
            self.held = False

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, *exc):
        self.release()


# ------------------------------------------------------------------ pairing

@dataclass
class Exchange:
    timestamp: str
    session_id: str
    user: str
    assistant: str
    paired: bool


def transcripts_root() -> Path:
    return Path(os.environ.get("MELDWERKES_TRANSCRIPTS")
                or Path.home() / ".claude" / "projects")


def _user_turns(path: Path):
    """[(cleaned user text, assistant text just before it)] for real typed prompts."""
    turns, last_assistant = [], ""
    for line in path.read_text(errors="ignore").splitlines():
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        typ = d.get("type")
        if typ not in ("user", "assistant"):
            continue
        text = bootstrap._text_of(d.get("message", {}).get("content"))
        if typ == "assistant":
            if text:
                last_assistant = text
            continue
        if text and d.get("promptSource"):
            turns.append((text, last_assistant))
    return turns


def pair_with_transcripts(rows: list, projects_root: Path) -> list:
    """Attach the assistant message each captured prompt was answering.

    Matching is by prompt text, not timestamp: pending rows carry local time and
    transcripts carry UTC. Identical prompts pair in order. A prompt with no
    transcript is kept, marked unpaired.
    """
    turns_by_session, used = {}, defaultdict(set)
    out = []
    for row in rows:
        sid = row.get("session_id") or ""
        prompt = row.get("prompt", "")
        if sid not in turns_by_session:
            files = list(Path(projects_root).glob(f"*/{sid}.jsonl")) if sid else []
            turns_by_session[sid] = _user_turns(files[0]) if files else None
        turns = turns_by_session[sid]
        assistant, paired = "", False
        if turns is not None:
            wanted = bootstrap._clean(prompt)[:4000]
            for i, (text, before) in enumerate(turns):
                if i not in used[sid] and text[:len(wanted)] == wanted:
                    used[sid].add(i)
                    assistant, paired = before, True
                    break
        out.append(Exchange(row.get("timestamp", ""), sid, prompt, assistant, paired))
    return out


# ----------------------------------------------------------------- classify

KINDS = ("correction", "directive", "answer", "none")


@dataclass
class Counts:
    read: int = 0
    scrubbed: int = 0
    internal: int = 0
    classified: dict = field(default_factory=dict)
    decisions: int = 0
    corrections: int = 0
    unrouted: int = 0
    failed_batches: int = 0
    stopped: bool = False


def exchange_id(ex: Exchange) -> str:
    """Deterministic, so a run that crashed after writing can be retried safely."""
    key = f"{ex.session_id}|{ex.timestamp}|{ex.user}"
    return "ex:" + hashlib.sha1(key.encode("utf-8", "replace")).hexdigest()[:16]


def _classify_batch(completer, batch):
    """{n: item} for a batch, or None when the model failed or returned nothing usable."""
    try:
        raw = bootstrap.classify(completer, batch)
    except Exception as e:  # CLI failure, timeout, API error
        print(f"  ! classify failed: {e}", file=sys.stderr)
        return None
    if not isinstance(raw, list) or not raw:
        return None
    return {it.get("n"): it for it in raw if isinstance(it, dict)}


def process_exchanges(store, completer, exchanges, run_id, *, min_confidence=0.6, max_batches=10, stop=None):
    """Classify exchanges and write what they reveal.

    Returns (Counts, handled): `handled` is how many of the input exchanges are
    fully dealt with, so the caller advances its cursor only that far. A failed
    batch stops the run there; earlier batches stay written. `stop`, if given, is
    checked after each model call and before anything is written; when it returns
    true the run ends there (used to honor the capture toggle mid-run).
    """
    counts = Counts(read=len(exchanges))
    brains = {b.domain: b for b in store.get_brains()}
    existing = {e["id"] for e in store.get_exchanges()}
    handled, model_batches = 0, 0

    for start in range(0, len(exchanges), bootstrap.BATCH):
        chunk = exchanges[start:start + bootstrap.BATCH]
        todo = []
        for e in chunk:
            if scrub.is_internal_prompt(e.user):
                counts.internal += 1
                continue
            eid = exchange_id(e)
            if eid in existing:
                continue
            user, dropped_u = scrub.scrub(e.user)
            asst, dropped_a = scrub.scrub(e.assistant)
            counts.scrubbed += dropped_u + dropped_a
            if user.strip():
                todo.append((e, user, asst, eid))

        if todo:
            if model_batches >= max_batches:
                break
            model_batches += 1
            by_n = _classify_batch(completer, [(e.timestamp, a, u, e.session_id) for e, u, a, _ in todo])
            if by_n is None:
                counts.failed_batches += 1
                break
            if stop and stop():
                counts.stopped = True
                break
            for i, (e, user, asst, eid) in enumerate(todo, 1):
                _write_item(store, counts, run_id, e, user, asst, eid, by_n.get(i) or {},
                            brains, min_confidence)
        handled += len(chunk)
    return counts, handled


def _write_item(store, counts, run_id, e, user, asst, eid, item, brains, min_confidence):
    kind = item.get("kind") if item.get("kind") in KINDS else "none"
    domain = (item.get("domain") or "general").strip().lower()
    principle = item.get("principle")
    try:
        conf = float(item.get("confidence") or 0)
    except (TypeError, ValueError):
        conf = 0.0
    if not e.paired:
        conf = min(conf, 0.5)  # without what it answered, a "correction" is a guess

    brain = brains.get(domain)
    decision_id = None
    if kind != "none" and principle and conf >= min_confidence:
        if brain is None:
            counts.unrouted += 1
        else:
            decision_id = str(uuid.uuid4())
            store.save_decision(memory.Decision(
                id=decision_id, brain_id=brain.id, timestamp=e.timestamp,
                context=f"[auto {run_id}] {asst[:400]}", decision=user[:400], grounding="none",
                confirmed=False if kind == "correction" else None))
            store.record_run_item(run_id, "decision", decision_id)
            counts.decisions += 1
            if kind == "correction":
                cid = str(uuid.uuid4())
                store.save_correction(memory.Correction(
                    id=cid, decision_id=decision_id, brain_id=brain.id, timestamp=e.timestamp,
                    user_feedback=user[:600], principle_affected=principle))
                store.record_run_item(run_id, "correction", cid)
                counts.corrections += 1

    store.save_exchange(
        id=eid, run_id=run_id, timestamp=e.timestamp, session_id=e.session_id,
        brain_id=brain.id if brain else None, domain=domain, kind=kind, confidence=conf,
        assistant=asst[:600], user=user[:900], decision_id=decision_id, paired=int(e.paired))
    store.record_run_item(run_id, "exchange", eid)
    counts.classified[kind] = counts.classified.get(kind, 0) + 1


# -------------------------------------------------------------- distillation

DISTILL_MIN_ITEMS = 5
DISTILL_MAX_DAYS = 14


def _naive(ts: str) -> Optional[datetime]:
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).replace(tzinfo=None)
    except (ValueError, AttributeError):
        return None


def _last_distilled(store, brain_id: str) -> Optional[datetime]:
    stamps = [_naive(p.timestamp) for p in store.get_principles(brain_id)]
    stamps += [_naive(p.created_at) for st in ("proposed", "accepted", "rejected")
               for p in store.get_proposals(status=st, brain_id=brain_id)]
    stamps = [t for t in stamps if t]
    return max(stamps) if stamps else None


def due_for_distill(store, brain_id: str, now: datetime) -> bool:
    """5+ decisions since the last distillation, or 14 days with any new one."""
    last = _last_distilled(store, brain_id)
    new = [d for d in store.get_decisions(brain_id)
           if last is None or (_naive(d.timestamp) or datetime.min) > last]
    if len(new) >= DISTILL_MIN_ITEMS:
        return True
    return bool(new) and last is not None and (now - last) >= timedelta(days=DISTILL_MAX_DAYS)


def distill(store, completer, brain_id: str, run_id: str, mode: str, *,
            exclude_ids: frozenset = frozenset(), now: Optional[datetime] = None, num_recent: int = 20):
    """Distil principles (and meta-principles) for one mind.

    mode "propose": queue them as proposals. mode "apply": checkpoint, then save
    them directly. Returns the proposals created (empty in apply mode).
    """
    now = now or datetime.now()
    compress.COMPLETER = completer
    principles = compress.extract_principles(store, brain_id, num_recent, exclude_ids)
    metas = compress.extract_meta_principles(store, brain_id)
    created = []
    if mode == "apply":
        memory.checkpoint(store.db_path, f"pre-apply-{run_id}")
        for p in principles:
            store.save_principle(p)
        for m in metas:
            store.save_meta_principle(m)
        return created
    for p in principles:
        created.append(memory.Proposal(
            id=str(uuid.uuid4()), brain_id=brain_id, kind="principle",
            payload={"principle": p.principle, "confidence": p.confidence,
                     "supporting_decisions": p.supporting_decisions,
                     "conflicting_decisions": p.conflicting_decisions},
            status="proposed", run_id=run_id, created_at=now.isoformat()))
    for m in metas:
        created.append(memory.Proposal(
            id=str(uuid.uuid4()), brain_id=brain_id, kind="meta",
            payload={"principle_a": m.principle_a, "principle_b": m.principle_b,
                     "weighting": m.weighting, "context": m.context},
            status="proposed", run_id=run_id, created_at=now.isoformat()))
    for pr in created:
        store.save_proposal(pr)
        store.record_run_item(run_id, "proposal", pr.id)
    return created


# ------------------------------------------------------------------ one run

MAX_BATCHES = 10


def log_path() -> Path:
    return memory.DATA_DIR / "logs" / "auto-latest.log"


def append_log(line: str) -> None:
    path = log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a") as f:
        f.write(line + "\n")


def _capture_off() -> bool:
    return not memory.MemoryStore.load_settings().capture_enabled


def run_once(db_path, completer, *, dry_run: bool = False, now: Optional[datetime] = None,
             max_batches: int = MAX_BATCHES) -> dict:
    """One pass: read new prompts, classify, write decisions, queue proposals.

    Never logs or stores prompt text beyond the scrubbed exchange rows. Returns a
    dict with at least "status": ok | partial | idle | disabled | capture-off | locked.
    """
    now = now or datetime.now()
    settings = memory.MemoryStore.load_settings()
    if settings.auto_mode == "off":
        return {"status": "disabled"}
    if not settings.capture_enabled:
        return {"status": "capture-off"}

    lock = RunLock()
    if not lock.acquire():
        return {"status": "locked"}
    previous_env = os.environ.get(scrub.INTERNAL_ENV)
    os.environ[scrub.INTERNAL_ENV] = "1"  # our own `claude -p` calls must not be captured
    try:
        store = memory.MemoryStore(Path(db_path))
        cursor = load_cursor()
        all_rows, end_offset = read_new(pending_path(), cursor)
        if not all_rows:
            return {"status": "idle"}
        window = all_rows[: max_batches * bootstrap.BATCH]

        if dry_run:
            return _dry_run(completer, all_rows, window)

        run_id = now.strftime("%Y%m%dT%H%M%S") + "-" + uuid.uuid4().hex[:6]
        started = time.monotonic()
        snap = memory.checkpoint(Path(db_path), f"pre-auto-{run_id}")
        store.start_run(run_id)
        errors = 0
        try:
            exchanges = pair_with_transcripts(window, transcripts_root())
            counts, handled = process_exchanges(
                store, completer, exchanges, run_id, max_batches=max_batches, stop=_capture_off)
            if handled == len(all_rows):
                save_cursor(end_offset)
            elif handled > 0:
                save_cursor(window[handled - 1]["_end"])

            proposals = 0
            if not counts.failed_batches and not counts.stopped:
                for brain in store.get_brains():
                    try:
                        if due_for_distill(store, brain.id, now):
                            proposals += len(distill(store, completer, brain.id, run_id,
                                                     settings.auto_mode, now=now))
                    except Exception as e:
                        errors += 1
                        print(f"  ! distill failed for {brain.name}: {e}", file=sys.stderr)
            memory.write_session_context(Path(db_path))
        except Exception:
            store.finish_run(run_id, status="error", errors=1, checkpoint=snap.name if snap else None)
            append_log(f"{now.isoformat()} run={run_id} status=error checkpoint={snap.name if snap else '-'}")
            raise

        if counts.stopped:
            status = "capture-off"
        elif counts.failed_batches or errors:
            status = "partial"
        else:
            status = "ok"
        errors += counts.failed_batches
        store.finish_run(run_id, rows_read=counts.read, scrubbed=counts.scrubbed,
                         classified_json=json.dumps(counts.classified), decisions=counts.decisions,
                         proposals=proposals, errors=errors, checkpoint=snap.name if snap else None,
                         status=status)
        append_log(f"{now.isoformat()} run={run_id} status={status} read={counts.read} "
                   f"handled={handled} scrubbed={counts.scrubbed} internal={counts.internal} "
                   f"classified={json.dumps(counts.classified, sort_keys=True)} decisions={counts.decisions} "
                   f"proposals={proposals} errors={errors} checkpoint={snap.name if snap else '-'} "
                   f"duration={time.monotonic() - started:.1f}s")
        return {"status": status, "run_id": run_id, "counts": counts, "handled": handled,
                "proposals": proposals}
    finally:
        if previous_env is None:
            os.environ.pop(scrub.INTERNAL_ENV, None)
        else:
            os.environ[scrub.INTERNAL_ENV] = previous_env
        lock.release()


def _dry_run(completer, all_rows, window) -> dict:
    """Classify one batch, write nothing: batch estimate plus a kind histogram."""
    exchanges = pair_with_transcripts(window[:bootstrap.BATCH], transcripts_root())
    batch = []
    for e in exchanges:
        if scrub.is_internal_prompt(e.user):
            continue
        user, _ = scrub.scrub(e.user)
        asst, _ = scrub.scrub(e.assistant)
        if user.strip():
            batch.append((e.timestamp, asst, user, e.session_id))
    by_n = _classify_batch(completer, batch) if batch else {}
    histogram = {}
    for i in range(1, len(batch) + 1):
        kind = (by_n or {}).get(i, {}).get("kind", "none")
        histogram[kind] = histogram.get(kind, 0) + 1
    return {"status": "dry-run", "dry_run": True, "rows": len(all_rows),
            "batches": -(-len(all_rows) // bootstrap.BATCH), "histogram": histogram}


# ------------------------------------------------------------------- status

def status_text(store, now: Optional[datetime] = None) -> str:
    settings = memory.MemoryStore.load_settings()
    rows, _ = read_new(pending_path(), load_cursor())
    last = store.last_run()
    lines = [
        f"auto_mode: {settings.auto_mode}",
        f"capture: {'on' if settings.capture_enabled else 'off'}",
        f"backlog: {len(rows)} unprocessed prompt(s), about {-(-len(rows) // bootstrap.BATCH)} batch(es)",
    ]
    if last:
        lines.append(f"last run: {last['run_id']} {last['status']} started {last['started_at']} "
                     f"decisions={last['decisions']} proposals={last['proposals']} errors={last['errors']}")
    else:
        lines.append("last run: none")
    lines.append(f"proposals awaiting review: {len(store.get_proposals())}")
    lines.append("correction rate (7d): n/a")
    return "\n".join(lines)


# ---------------------------------------------------------------------- CLI

def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description="Meldwerkes automatic learning loop")
    ap.add_argument("--db", default=str(memory.DEFAULT_DB))
    sub = ap.add_subparsers(dest="cmd", required=True)
    rn = sub.add_parser("run")
    rn.add_argument("--dry-run", action="store_true")
    llm.add_auth_arg(rn)
    sub.add_parser("status")
    en = sub.add_parser("enable")
    en.add_argument("--mode", choices=["propose", "apply"], default="propose")
    sub.add_parser("disable")
    args = ap.parse_args(argv)

    if args.cmd in ("enable", "disable"):
        settings = memory.MemoryStore.load_settings()
        settings.auto_mode = args.mode if args.cmd == "enable" else "off"
        memory.MemoryStore.save_settings(settings)
        print(f"auto_mode: {settings.auto_mode}")
        return 0
    store = memory.MemoryStore(Path(args.db))
    if args.cmd == "status":
        print(status_text(store))
        return 0
    completer = llm.Completer(llm.resolve_auth(args.auth))
    result = run_once(args.db, completer, dry_run=args.dry_run)
    shown = {k: v for k, v in result.items() if k != "counts"}
    if "counts" in result:
        shown["counts"] = result["counts"].__dict__
    print(json.dumps(shown, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
