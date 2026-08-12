#!/usr/bin/env python3
"""Generate Meldwerkes status report."""

import sys
import os
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from memory import MemoryStore, Settings, DEFAULT_DB
from pathlib import Path


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=str(DEFAULT_DB))
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args()

    store = MemoryStore(Path(args.db))
    settings = Settings.load_settings() if Path(args.db).exists() else Settings()
    brains = store.get_brains()

    if args.format == "json":
        import json
        report = {"generated_at": datetime.now().isoformat(), "settings": {
            "principle_auto_answer": settings.principle_auto_answer,
            "conflict_resolution": settings.conflict_resolution
        }, "brains": []}
        for b in brains:
            decisions = store.get_decisions(b.id)
            corrections = store.get_corrections(b.id)
            principles = store.get_principles(b.id)
            metas = store.get_meta_principles(b.id)
            confirmed = sum(1 for d in decisions if d.confirmed is True)
            corrected = sum(1 for d in decisions if d.confirmed is False)
            report["brains"].append({
                "id": b.id, "name": b.name, "domain": b.domain,
                "created_at": b.created_at, "description": b.description,
                "decisions": len(decisions), "confirmed": confirmed,
                "corrected": corrected, "correction_rate": corrected / len(decisions) if decisions else 0,
                "principles": [{"principle": p.principle, "confidence": p.confidence} for p in principles],
                "meta_principles": [{"a": m.principle_a, "b": m.principle_b, "weighting": m.weighting} for m in metas]
            })
        print(json.dumps(report, indent=2))
        return

    # Text report
    print(f"Meldwerkes Status Report — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)
    print(f"\nSettings:")
    print(f"  Principle auto-answer: {'on' if settings.principle_auto_answer else 'off'}")
    print(f"  Conflict resolution:   {settings.conflict_resolution}")
    print(f"\nBrains: {len(brains)}")

    for b in brains:
        decisions = store.get_decisions(b.id)
        corrections = store.get_corrections(b.id)
        principles = store.get_principles(b.id)
        metas = store.get_meta_principles(b.id)

        confirmed = sum(1 for d in decisions if d.confirmed is True)
        corrected = sum(1 for d in decisions if d.confirmed is False)
        pending = len(decisions) - confirmed - corrected
        rate = f"{corrected/len(decisions):.0%}" if decisions else "n/a"

        print(f"\n  [{b.name}] — domain: {b.domain}")
        print(f"  Created: {b.created_at[:10]}")
        if b.description:
            print(f"  Description: {b.description}")
        print(f"  Decisions:   {len(decisions)} total | {confirmed} confirmed | {corrected} corrected | {pending} pending")
        print(f"  Correction rate: {rate}")
        print(f"  Principles:  {len(principles)}")
        for p in principles:
            print(f"    - {p.principle} ({p.confidence:.0%} confidence)")
        if metas:
            print(f"  Meta-principles: {len(metas)}")
            for m in metas:
                print(f"    - {m.principle_a} > {m.principle_b} in {m.context}")

    if not brains:
        print("\n  No brains registered yet.")
        print("  Use /meldwerkes-setup to create your first brain.")


if __name__ == "__main__":
    main()
