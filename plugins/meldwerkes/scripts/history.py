#!/usr/bin/env python3
"""Checkpoints, retraction, and capture control.

A model you cannot roll back is one you can only accept. This provides the undo:
snapshot before every mutation, retract a time range, restore any snapshot.

Retraction cascades. Principles are derived from decisions, so removing a day's
decisions must also remove principles whose support that day provided —
otherwise the store keeps conclusions whose evidence is gone, which is worse
than keeping both.

Usage:
  python3 history.py status
  python3 history.py capture --on | --off
  python3 history.py checkpoint --label "before experiment"
  python3 history.py list
  python3 history.py retract --since 2026-08-11 [--brain-id <id>] [--dry-run]
  python3 history.py restore --snapshot <name>
"""

import argparse
import json
import os
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from memory import (MemoryStore, DEFAULT_DB, CHECKPOINT_DIR,
                    checkpoint, list_checkpoints, restore_checkpoint)


def parse_since(value: str) -> str:
    """Accept YYYY-MM-DD, or shorthand like 1d / 12h."""
    v = value.strip().lower()
    if v.endswith("d") and v[:-1].isdigit():
        return (datetime.now() - timedelta(days=int(v[:-1]))).isoformat()
    if v.endswith("h") and v[:-1].isdigit():
        return (datetime.now() - timedelta(hours=int(v[:-1]))).isoformat()
    return datetime.fromisoformat(v).isoformat()


def cmd_status(args):
    s = MemoryStore.load_settings()
    snaps = list_checkpoints()
    print(f"Capture        : {'ON — recording' if s.capture_enabled else 'OFF — nothing is being written'}")
    print(f"Answer mode    : principle_auto_answer={'on' if s.principle_auto_answer else 'off'}")
    print(f"Decay half-life: {s.confidence_half_life_days:g} days")
    print(f"Checkpoints    : {len(snaps)}" + (f" (latest {snaps[0].name})" if snaps else ""))


def cmd_capture(args):
    s = MemoryStore.load_settings()
    if args.on == args.off:
        sys.exit("Specify exactly one of --on / --off")
    s.capture_enabled = bool(args.on)
    MemoryStore.save_settings(s)
    print("Capture ON — decisions and corrections will be recorded." if s.capture_enabled
          else "Capture OFF — nothing will be written until re-enabled.\n"
               "Note: Claude Code still writes its own transcripts, so a later\n"
               "bootstrap could import this period unless you exclude it.")


def cmd_checkpoint(args):
    dest = checkpoint(Path(args.db), args.label or "manual")
    print(f"Checkpoint saved: {dest.name}" if dest else "No store to checkpoint yet.")


def cmd_list(args):
    snaps = list_checkpoints()
    if not snaps:
        print("No checkpoints yet.")
        return
    print(f"{len(snaps)} checkpoint(s) in {CHECKPOINT_DIR}\n")
    for p in snaps:
        stamp, _, label = p.stem.partition("__")
        try:
            when = datetime.strptime(stamp, "%Y%m%dT%H%M%S").strftime("%Y-%m-%d %H:%M")
        except ValueError:
            when = stamp
        print(f"  {p.name:<46} {when}  {label.replace('-', ' ')}")


def _counts(db, since, brain_id):
    where = "timestamp >= ?"
    params = [since]
    if brain_id:
        where += " AND brain_id = ?"
        params.append(brain_id)
    out = {}
    with sqlite3.connect(db) as conn:
        for table in ("decisions", "corrections", "principles", "meta_principles"):
            try:
                out[table] = conn.execute(
                    f"SELECT COUNT(*) FROM {table} WHERE {where}", params).fetchone()[0]
            except sqlite3.OperationalError:
                out[table] = 0
    return out


def cmd_retract(args):
    db = Path(args.db)
    if not db.exists():
        sys.exit("No store found.")
    since = parse_since(args.since)
    counts = _counts(db, since, args.brain_id)
    total = sum(counts.values())

    print(f"Retracting everything recorded since {since[:19]}"
          + (f" in brain {args.brain_id[:8]}" if args.brain_id else " (all brains)"))
    for k, v in counts.items():
        print(f"  {k:<16} {v}")
    if not total:
        print("\nNothing in that window.")
        return
    if args.dry_run:
        print("\nDRY RUN — nothing removed.")
        return

    snap = checkpoint(db, f"pre-retract-{args.since}")
    where = "timestamp >= ?"
    params = [since]
    if args.brain_id:
        where += " AND brain_id = ?"
        params.append(args.brain_id)
    with sqlite3.connect(db) as conn:
        for table in ("meta_principles", "principles", "corrections", "decisions"):
            try:
                conn.execute(f"DELETE FROM {table} WHERE {where}", params)
            except sqlite3.OperationalError:
                pass

    print(f"\nRemoved {total} record(s).")
    print(f"Checkpoint before this change: {snap.name if snap else 'none'}")
    print("Undo with:  history.py restore --snapshot " + (snap.name if snap else "<name>"))
    print("\nPrinciples derived partly from earlier evidence were removed along")
    print("with the window. Run /pahf-compress to re-derive from what remains.")


def cmd_restore(args):
    db = Path(args.db)
    target = CHECKPOINT_DIR / args.snapshot
    if not target.exists():
        sys.exit(f"No such checkpoint: {args.snapshot}\nList them with: history.py list")
    restore_checkpoint(target, db)
    print(f"Restored {target.name}.")
    print("The pre-restore state was itself checkpointed, so this is reversible.")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status")
    cap = sub.add_parser("capture")
    cap.add_argument("--on", action="store_true"); cap.add_argument("--off", action="store_true")
    cp = sub.add_parser("checkpoint"); cp.add_argument("--label")
    sub.add_parser("list")
    rt = sub.add_parser("retract")
    rt.add_argument("--since", required=True, help="YYYY-MM-DD, or 1d / 12h")
    rt.add_argument("--brain-id"); rt.add_argument("--dry-run", action="store_true")
    rs = sub.add_parser("restore"); rs.add_argument("--snapshot", required=True)
    ap.add_argument("--db", default=str(DEFAULT_DB))
    args = ap.parse_args()
    {"status": cmd_status, "capture": cmd_capture, "checkpoint": cmd_checkpoint,
     "list": cmd_list, "retract": cmd_retract, "restore": cmd_restore}[args.cmd](args)


if __name__ == "__main__":
    main()
