#!/usr/bin/env python3
"""Import a brain from a portable JSON export."""

import argparse
import json
import sys
import os
import uuid
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from memory import MemoryStore, Brain, Decision, Correction, Principle, MetaPrinciple, DEFAULT_DB
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("file", help="Export JSON file to import")
    parser.add_argument("--trust", choices=["provisional", "full"], default="provisional",
                        help="Trust level for imported principles (default: provisional)")
    parser.add_argument("--rename", help="Override brain name on import")
    parser.add_argument("--db", default=str(DEFAULT_DB))
    args = parser.parse_args()

    with open(args.file) as f:
        data = json.load(f)

    if data.get("small_brain_export") != "1.0":
        print("Error: unrecognized export format.", file=sys.stderr)
        sys.exit(1)

    store = MemoryStore(Path(args.db))
    b_data = data["brain"]
    mem = data["memory"]

    # Create brain with new ID to avoid collisions
    new_brain_id = str(uuid.uuid4())
    brain = Brain(
        id=new_brain_id,
        name=args.rename or b_data["name"],
        domain=b_data["domain"],
        created_at=b_data["created_at"],
        description=b_data.get("description", "")
    )
    with __import__("sqlite3").connect(store.db_path) as conn:
        conn.execute("INSERT INTO brains VALUES (?, ?, ?, ?, ?)",
                     (brain.id, brain.name, brain.domain, brain.created_at, brain.description))

    # Map old IDs to new ones
    id_map = {}

    for d in mem.get("decisions", []):
        new_id = str(uuid.uuid4())
        id_map[d["id"]] = new_id
        decision = Decision(
            id=new_id, brain_id=new_brain_id, timestamp=d["timestamp"],
            context=d["context"], decision=d["decision"], grounding=d["grounding"],
            confirmed=d.get("confirmed")
        )
        store.save_decision(decision)

    for c in mem.get("corrections", []):
        new_id = str(uuid.uuid4())
        correction = Correction(
            id=new_id, decision_id=id_map.get(c["decision_id"], c["decision_id"]),
            brain_id=new_brain_id, timestamp=c["timestamp"],
            user_feedback=c["user_feedback"], principle_affected=c["principle_affected"],
            new_weighting=c.get("new_weighting")
        )
        store.save_correction(correction)

    # Apply provisional confidence discount if trust is provisional
    confidence_multiplier = 0.7 if args.trust == "provisional" else 1.0

    for p in mem.get("principles", []):
        principle = Principle(
            id=str(uuid.uuid4()), brain_id=new_brain_id, timestamp=p["timestamp"],
            principle=p["principle"],
            confidence=p["confidence"] * confidence_multiplier,
            supporting_decisions=[id_map.get(x, x) for x in p.get("supporting_decisions", [])],
            conflicting_decisions=[id_map.get(x, x) for x in p.get("conflicting_decisions", [])]
        )
        store.save_principle(principle)

    for m in mem.get("meta_principles", []):
        meta = MetaPrinciple(
            id=str(uuid.uuid4()), brain_id=new_brain_id, timestamp=m["timestamp"],
            principle_a=m["principle_a"], principle_b=m["principle_b"],
            weighting=m["weighting"], context=m["context"], times_applied=0
        )
        store.save_meta_principle(meta)

    stats = data.get("stats", {})
    trust_note = " (confidence discounted 30% — provisional trust)" if args.trust == "provisional" else ""
    print(f"Imported brain '{brain.name}' (domain: {brain.domain}){trust_note}")
    print(f"  {stats.get('total_decisions', '?')} decisions, {stats.get('principles', '?')} principles")
    print(f"  New brain ID: {new_brain_id}")
    if args.trust == "provisional":
        print("  Tip: use /small-brain-report to review, then run /pahf-compress to re-evaluate confidence.")


if __name__ == "__main__":
    main()
