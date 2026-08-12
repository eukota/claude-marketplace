#!/usr/bin/env python3
"""Write decisions and corrections to Meldwerkes memory."""

import argparse
import sys
import os
import uuid
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from memory import MemoryStore, Decision, Correction, DEFAULT_DB
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="type", required=True)

    dec = subparsers.add_parser("decision")
    dec.add_argument("--brain-id", required=True)
    dec.add_argument("--context", required=True)
    dec.add_argument("--decision", required=True)
    dec.add_argument("--grounding", default="none")

    cor = subparsers.add_parser("correction")
    cor.add_argument("--brain-id", required=True)
    cor.add_argument("--decision-id", required=True)
    cor.add_argument("--feedback", required=True)
    cor.add_argument("--principle", required=True)
    cor.add_argument("--weighting")

    con = subparsers.add_parser("confirm")
    con.add_argument("--decision-id", required=True)

    parser.add_argument("--db", default=str(DEFAULT_DB))
    args = parser.parse_args()

    store = MemoryStore(Path(args.db))

    if args.type == "decision":
        d = Decision(
            id=str(uuid.uuid4()),
            brain_id=args.brain_id,
            timestamp=datetime.now().isoformat(),
            context=args.context,
            decision=args.decision,
            grounding=args.grounding,
            confirmed=None
        )
        store.save_decision(d)
        print(f"decision:{d.id}")

    elif args.type == "correction":
        c = Correction(
            id=str(uuid.uuid4()),
            decision_id=args.decision_id,
            brain_id=args.brain_id,
            timestamp=datetime.now().isoformat(),
            user_feedback=args.feedback,
            principle_affected=args.principle,
            new_weighting=getattr(args, "weighting", None)
        )
        store.save_correction(c)
        print(f"correction:{c.id}")

    elif args.type == "confirm":
        store.confirm_decision(args.decision_id, True)
        print(f"confirmed:{args.decision_id}")


if __name__ == "__main__":
    main()
