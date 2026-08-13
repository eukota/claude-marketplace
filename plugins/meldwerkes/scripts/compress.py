#!/usr/bin/env python3
"""Compression loop — requires anthropic SDK."""

import argparse
import sys
import os
import json
import uuid
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from memory import MemoryStore, Principle, MetaPrinciple, DEFAULT_DB
from memory import write_session_context
from pathlib import Path

try:
    from anthropic import Anthropic
except ImportError:
    print("Error: anthropic SDK required. Run: pip install anthropic", file=sys.stderr)
    sys.exit(1)

MODEL = "claude-sonnet-4-6"


def extract_principles(store: MemoryStore, brain_id: str, num_recent: int) -> list[Principle]:
    decisions = store.get_decisions(brain_id)[-num_recent:]
    corrections = store.get_corrections(brain_id)

    if not decisions:
        print("No decisions to compress.")
        return []

    recent_ids = {d.id for d in decisions}
    relevant_corrections = [c for c in corrections if c.decision_id in recent_ids]

    dec_text = "\n".join([
        f"- [{d.id[:8]}] ({('confirmed' if d.confirmed else 'corrected' if d.confirmed is False else 'pending')}) "
        f"Context: {d.context}\n  Decision: {d.decision}\n  Grounding: {d.grounding}"
        for d in decisions
    ])
    cor_text = "\n".join([
        f"- [Decision {c.decision_id[:8]}] Feedback: {c.user_feedback}\n  Principle: {c.principle_affected}"
        + (f"\n  New weighting: {c.new_weighting}" if c.new_weighting else "")
        for c in relevant_corrections
    ]) or "No corrections."

    client = Anthropic()
    msg = client.messages.create(
        model=MODEL,
        max_tokens=2000,
        messages=[{"role": "user", "content": f"""Analyze this decision log and extract key principles.

Decisions:
{dec_text}

Corrections:
{cor_text}

Extract 2-5 principles that appear to guide these decisions. Return JSON only:
{{
  "principles": [
    {{
      "principle": "...",
      "supporting_decisions": ["id1", "id2"],
      "conflicting_decisions": ["id3"],
      "confidence": 0.8
    }}
  ]
}}"""}]
    )

    try:
        text = msg.content[0].text
        data = json.loads(text[text.find("{"):text.rfind("}")+1])
        principles = []
        for p in data.get("principles", []):
            principles.append(Principle(
                id=str(uuid.uuid4()),
                brain_id=brain_id,
                timestamp=datetime.now().isoformat(),
                principle=p["principle"],
                confidence=p.get("confidence", 0.5),
                supporting_decisions=p.get("supporting_decisions", []),
                conflicting_decisions=p.get("conflicting_decisions", [])
            ))
        return principles
    except (json.JSONDecodeError, ValueError) as e:
        print(f"Parse error: {e}", file=sys.stderr)
        return []


def extract_meta_principles(store: MemoryStore, brain_id: str) -> list[MetaPrinciple]:
    principles = store.get_principles(brain_id)
    corrections = store.get_corrections(brain_id)
    conflicts = [c for c in corrections if c.new_weighting]

    if len(principles) < 2 or not conflicts:
        print("Need 2+ principles and conflict data for meta-principles.")
        return []

    p_text = "\n".join([f"- {p.principle} ({p.confidence:.0%})" for p in principles])
    c_text = "\n".join([f"- {c.principle_affected}: {c.new_weighting}" for c in conflicts])

    client = Anthropic()
    msg = client.messages.create(
        model=MODEL,
        max_tokens=1500,
        messages=[{"role": "user", "content": f"""Analyze principle conflicts and extract meta-principles.

Principles:
{p_text}

Observed conflict resolutions:
{c_text}

Extract 1-3 meta-principles answering "when X conflicts with Y, which wins?" Return JSON only:
{{
  "meta_principles": [
    {{
      "principle_a": "...",
      "principle_b": "...",
      "weighting": "principle_a > principle_b when ...",
      "context": "..."
    }}
  ]
}}"""}]
    )

    try:
        text = msg.content[0].text
        data = json.loads(text[text.find("{"):text.rfind("}")+1])
        metas = []
        for m in data.get("meta_principles", []):
            metas.append(MetaPrinciple(
                id=str(uuid.uuid4()),
                brain_id=brain_id,
                timestamp=datetime.now().isoformat(),
                principle_a=m["principle_a"],
                principle_b=m["principle_b"],
                weighting=m["weighting"],
                context=m.get("context", "general"),
                times_applied=0
            ))
        return metas
    except (json.JSONDecodeError, ValueError) as e:
        print(f"Parse error: {e}", file=sys.stderr)
        return []


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--brain-id", required=True)
    parser.add_argument("--num-recent", type=int, default=20)
    parser.add_argument("--meta-only", action="store_true")
    parser.add_argument("--detect-split", action="store_true",
                        help="Check if conflict clusters suggest a brain split")
    parser.add_argument("--db", default=str(DEFAULT_DB))
    args = parser.parse_args()

    store = MemoryStore(Path(args.db))

    if args.meta_only:
        metas = extract_meta_principles(store, args.brain_id)
        for m in metas:
            store.save_meta_principle(m)
            print(f"Meta-principle: When '{m.principle_a}' conflicts with '{m.principle_b}':")
            print(f"  {m.weighting} (context: {m.context})")
        if not metas:
            print("No meta-principles extracted.")
        return

    principles = extract_principles(store, args.brain_id, args.num_recent)
    for p in principles:
        store.save_principle(p)
        print(f"Principle: {p.principle} (confidence: {p.confidence:.0%})")
        print(f"  Supporting: {len(p.supporting_decisions)} | Conflicting: {len(p.conflicting_decisions)}")

    write_session_context(Path(args.db))

    if not principles:
        return

    # Check for unresolvable conflict clusters (brain split signal)
    if args.detect_split:
        high_conflict = [p for p in principles if len(p.conflicting_decisions) >= 2 and p.confidence < 0.5]
        if len(high_conflict) >= 2:
            print("\nSPLIT_SIGNAL: Persistent conflict cluster detected.")
            print("These principles consistently conflict and may represent separate viewing angles:")
            for p in high_conflict:
                print(f"  - {p.principle}")
            print("Consider splitting into a second brain.")


if __name__ == "__main__":
    main()
