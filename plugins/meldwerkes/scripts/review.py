#!/usr/bin/env python3
"""Review principles and apply reinforcement.

Decay alone only forgets. Review is where the user pushes back against it —
confirming what is still true (resetting its clock), weakening what is
partly wrong, retiring what was never right, and rewording what was clumsily
stated.

Usage:
  python3 review.py list --brain-id <id>              # what needs review, stalest first
  python3 review.py reinforce --principle-id <id>
  python3 review.py weaken    --principle-id <id> [--penalty 0.25]
  python3 review.py revise    --principle-id <id> --text "..."
  python3 review.py retire    --principle-id <id>
"""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from memory import MemoryStore, DEFAULT_DB, effective_confidence
from memory import write_session_context


def age_days(timestamp: str) -> float:
    try:
        then = datetime.fromisoformat(timestamp.replace("Z", "+00:00")).replace(tzinfo=None)
    except (ValueError, AttributeError):
        return 0.0
    return max((datetime.now() - then).total_seconds() / 86400.0, 0.0)


def cmd_list(store, args):
    principles = (store.get_principles(args.brain_id) if args.brain_id
                  else store.get_all_principles())
    if not principles:
        print("No principles yet. Use /pahf-compress or /meldwerkes-bootstrap first.")
        return

    half_life = MemoryStore.load_settings().confidence_half_life_days
    rows = []
    for p in principles:
        eff = effective_confidence(p.confidence, p.timestamp, half_life)
        rows.append((p, eff, age_days(p.timestamp), p.confidence - eff))

    # Stalest first: the largest gap between what was stated and what survives
    # is what most needs a human to confirm or drop it.
    rows.sort(key=lambda r: r[3], reverse=True)

    print(f"{len(rows)} principle(s)   half-life {half_life:g}d\n")
    print(f"{'id':<10}{'stated':>7}{'now':>7}{'age':>8}   principle")
    print("-" * 78)
    for p, eff, age, _ in rows:
        print(f"{p.id[:8]:<10}{p.confidence:>7.2f}{eff:>7.2f}{age:>7.0f}d   {p.principle[:44]}")

    stale = [r for r in rows if r[1] < r[0].confidence * 0.5]
    if stale:
        print(f"\n{len(stale)} below half their stated confidence — review these first:")
        for p, eff, age, _ in stale:
            print(f"  {p.id[:8]}  ({age:.0f}d)  {p.principle}")
    else:
        print("\nNothing has decayed below half. The mind is current.")


def main():
    ap = argparse.ArgumentParser()
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--db", default=str(DEFAULT_DB))
    sub = ap.add_subparsers(dest="cmd", required=True)

    ls = sub.add_parser("list", parents=[common]);         ls.add_argument("--brain-id")
    rf = sub.add_parser("reinforce", parents=[common]);    rf.add_argument("--principle-id", required=True)
    rf.add_argument("--boost", type=float, default=0.05)
    wk = sub.add_parser("weaken", parents=[common]);       wk.add_argument("--principle-id", required=True)
    wk.add_argument("--penalty", type=float, default=0.25)
    rv = sub.add_parser("revise", parents=[common]);       rv.add_argument("--principle-id", required=True)
    rv.add_argument("--text", required=True)
    rt = sub.add_parser("retire", parents=[common]);       rt.add_argument("--principle-id", required=True)

    args = ap.parse_args()
    store = MemoryStore(Path(args.db))

    if args.cmd == "list":
        return cmd_list(store, args)

    # Accept an 8-char prefix, since that is what `list` displays
    pid = args.principle_id
    if len(pid) < 36:
        matches = [p.id for p in store.get_all_principles() if p.id.startswith(pid)]
        if len(matches) != 1:
            sys.exit(f"{'No' if not matches else 'Ambiguous'} principle id: {pid}")
        pid = matches[0]

    if args.cmd == "reinforce":
        ok = store.reinforce_principle(pid, args.boost)
        print(f"Reinforced {pid[:8]} — clock reset, confidence +{args.boost}" if ok
              else f"Not found: {pid[:8]}")
    elif args.cmd == "weaken":
        ok = store.weaken_principle(pid, args.penalty)
        print(f"Weakened {pid[:8]} — confidence -{args.penalty}" if ok
              else f"Not found: {pid[:8]}")
    elif args.cmd == "revise":
        ok = store.revise_principle(pid, args.text)
        print(f"Revised {pid[:8]}" if ok else f"Not found: {pid[:8]}")
    elif args.cmd == "retire":
        ok = store.retire_principle(pid)
        print(f"Retired {pid[:8]}" if ok else f"Not found: {pid[:8]}")

    # Injected context is precomputed, so it must be re-rendered on mutation.
    write_session_context(Path(args.db))


if __name__ == "__main__":
    main()
