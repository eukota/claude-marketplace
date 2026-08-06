#!/usr/bin/env bash
# PAHF SessionStart hook — inject active principles into session context

MEMORY_SCRIPT="$HOME/Development/small-brain-alpha/scripts/memory_query.py"

if [ ! -f "$MEMORY_SCRIPT" ]; then
  exit 0
fi

# Get principles for all domains
PRINCIPLES=$(python3 "$MEMORY_SCRIPT" --all-principles 2>/dev/null)

if [ -z "$PRINCIPLES" ]; then
  exit 0
fi

# Output as system message injected into session context
cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "PAHF Memory loaded:\n$PRINCIPLES"
  }
}
EOF
