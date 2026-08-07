#!/usr/bin/env python3
"""Export a brain to a portable JSON file."""

import argparse
import json
import sys
import os
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from memory import MemoryStore, DEFAULT_DB
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--brain-id", required=True)
    parser.add_argument("--output", help="Output file path (default: <brain-name>-export.json)")
    parser.add_argument("--db", default=str(DEFAULT_DB))
    args = parser.parse_args()

    store = MemoryStore(Path(args.db))
    brain = store.get_brain(args.brain_id)
    if not brain:
        print(f"Brain {args.brain_id} not found.", file=sys.stderr)
        sys.exit(1)

    decisions = store.get_decisions(args.brain_id)
    corrections = store.get_corrections(args.brain_id)
    principles = store.get_principles(args.brain_id)
    metas = store.get_meta_principles(args.brain_id)

    export = {
        "small_brain_export": "1.0",
        "exported_at": datetime.now().isoformat(),
        "brain": {
            "id": brain.id,
            "name": brain.name,
            "domain": brain.domain,
            "created_at": brain.created_at,
            "description": brain.description
        },
        "memory": {
            "decisions": [
                {"id": d.id, "timestamp": d.timestamp, "context": d.context,
                 "decision": d.decision, "grounding": d.grounding, "confirmed": d.confirmed}
                for d in decisions
            ],
            "corrections": [
                {"id": c.id, "decision_id": c.decision_id, "timestamp": c.timestamp,
                 "user_feedback": c.user_feedback, "principle_affected": c.principle_affected,
                 "new_weighting": c.new_weighting}
                for c in corrections
            ],
            "principles": [
                {"id": p.id, "timestamp": p.timestamp, "principle": p.principle,
                 "confidence": p.confidence, "supporting_decisions": p.supporting_decisions,
                 "conflicting_decisions": p.conflicting_decisions}
                for p in principles
            ],
            "meta_principles": [
                {"id": m.id, "timestamp": m.timestamp, "principle_a": m.principle_a,
                 "principle_b": m.principle_b, "weighting": m.weighting,
                 "context": m.context, "times_applied": m.times_applied}
                for m in metas
            ]
        },
        "stats": {
            "total_decisions": len(decisions),
            "confirmed": sum(1 for d in decisions if d.confirmed is True),
            "corrected": sum(1 for d in decisions if d.confirmed is False),
            "principles": len(principles),
            "meta_principles": len(metas)
        }
    }

    output_path = args.output or f"{brain.name}-export.json"
    with open(output_path, "w") as f:
        json.dump(export, f, indent=2)

    print(f"Exported brain '{brain.name}' to {output_path}")
    print(f"  {len(decisions)} decisions, {len(principles)} principles, {len(metas)} meta-principles")


if __name__ == "__main__":
    main()
