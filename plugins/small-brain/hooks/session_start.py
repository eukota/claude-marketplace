#!/usr/bin/env python3
"""SessionStart hook — inject active principles into session context."""

import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "../scripts"))

try:
    from memory import MemoryStore, Settings, DEFAULT_DB
    from pathlib import Path

    store = MemoryStore(DEFAULT_DB)
    settings = Settings.load_settings()
    brains = store.get_brains()

    if not brains:
        sys.exit(0)

    lines = ["## Small Brain Active"]
    lines.append(f"Brains: {len(brains)} | Principle auto-answer: {'on' if settings.principle_auto_answer else 'off'} | Conflict resolution: {settings.conflict_resolution}")
    lines.append("")

    for brain in brains:
        principles = store.get_principles(brain.id)
        metas = store.get_meta_principles(brain.id)
        if not principles:
            continue
        lines.append(f"**{brain.name}** (domain: {brain.domain})")
        for p in principles[:5]:  # Top 5 by confidence
            lines.append(f"  - {p.principle} ({p.confidence:.0%})")
        for m in metas:
            lines.append(f"  - [meta] {m.principle_a} > {m.principle_b} in {m.context}")

    context = "\n".join(lines)

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": context
        }
    }))

except Exception:
    sys.exit(0)
