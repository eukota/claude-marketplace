#!/usr/bin/env python3
"""Record each user turn for later classification. Never blocks.

This replaces a type:"prompt" UserPromptSubmit hook. Prompt-type hooks are
*gates* — the evaluating model returns ok:true/false and a false blocks the
turn. A passive classifier phrased as a gate therefore stopped every message
that was not a preference statement, which is most of them.

Capture must never be able to interrupt work. So this is a command hook that
appends the turn to a pending file and exits 0 unconditionally: any failure
loses one signal rather than blocking the user.

Classification happens later, in batch, by the same code path bootstrap uses.
That also removes a model call from every keystroke-driven turn.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0

    prompt = (payload.get("prompt") or "").strip()
    if not prompt:
        return 0

    try:
        from memory import MemoryStore, DATA_DIR
        if not MemoryStore.load_settings().capture_enabled:
            return 0
    except Exception:
        # If settings cannot be read, fail closed: record nothing rather than
        # recording against a capture toggle the user may have turned off.
        return 0

    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(DATA_DIR / "pending.jsonl", "a") as f:
            f.write(json.dumps({
                "timestamp": datetime.now().isoformat(),
                "prompt": prompt[:4000],
                "session_id": payload.get("session_id"),
                "cwd": payload.get("cwd"),
            }) + "\n")
    except Exception:
        pass

    return 0


if __name__ == "__main__":
    sys.exit(main())
