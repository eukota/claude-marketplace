#!/usr/bin/env python3
"""Query Small Brain memory — called by session-start hook and pahf-ground skill."""

import argparse
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from memory import MemoryStore, DEFAULT_DB
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--brain-id", help="Brain ID to query")
    parser.add_argument("--context", help="Match context against decisions/principles")
    parser.add_argument("--all-principles", action="store_true", help="All principles across all brains")
    parser.add_argument("--list-brains", action="store_true", help="List all brains")
    parser.add_argument("--db", default=str(DEFAULT_DB))
    args = parser.parse_args()

    store = MemoryStore(Path(args.db))

    if args.list_brains:
        brains = store.get_brains()
        if not brains:
            print("No brains registered.")
        for b in brains:
            print(f"[{b.id[:8]}] {b.name} (domain: {b.domain}) — created {b.created_at[:10]}")
        return

    if args.all_principles:
        principles = store.get_all_principles()
        if not principles:
            sys.exit(0)
        brains = {b.id: b for b in store.get_brains()}
        lines = []
        for p in principles:
            brain_name = brains.get(p.brain_id, None)
            label = brain_name.name if brain_name else p.brain_id[:8]
            lines.append(f"[{label}] {p.principle} (confidence: {p.confidence:.0%})")
        meta = []
        for b in store.get_brains():
            for m in store.get_meta_principles(b.id):
                meta.append(f"[meta/{b.name}] When {m.principle_a} conflicts with {m.principle_b}: {m.weighting}")
        if meta:
            lines.extend(meta)
        print("\n".join(lines))
        return

    brain_id = args.brain_id
    context = args.context or ""
    results = []

    if brain_id:
        principles = store.get_principles(brain_id)
        decisions = store.get_decisions(brain_id)
        for p in principles:
            if not context or any(w in context.lower() for w in p.principle.lower().split()):
                results.append(f"Principle: {p.principle} (confidence: {p.confidence:.0%})")
        for d in decisions[-10:]:
            if context and context.lower() in d.context.lower():
                status = "confirmed" if d.confirmed else ("corrected" if d.confirmed is False else "pending")
                results.append(f"Past decision [{d.id[:8]}] ({status}): {d.context[:60]} → {d.decision[:60]}")
    else:
        # Query across all brains
        brains = store.get_brains()
        for brain in brains:
            principles = store.get_principles(brain.id)
            for p in principles:
                if not context or any(w in context.lower() for w in p.principle.lower().split()):
                    results.append(f"[{brain.name}] Principle: {p.principle} (confidence: {p.confidence:.0%})")

    print("\n".join(results) if results else "No prior context found.")


if __name__ == "__main__":
    main()
