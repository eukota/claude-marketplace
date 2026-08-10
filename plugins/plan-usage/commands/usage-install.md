---
allowed-tools: Bash(cat:*), Bash(python3:*), Read, Edit, Write
description: Wire the plan-usage status line into settings.json
---

## Your Task

Install the account-usage status line. Claude Code's `statusLine` is a
`settings.json` field — plugins cannot declare one — so this command wires it
up explicitly.

### 1. Read the current settings

Read `~/.claude/settings.json`. Note whether a `statusLine` is already set.

### 2. Decide how to proceed

- **No `statusLine` set** — add one pointing at this plugin's script:

  ```json
  "statusLine": {
    "type": "command",
    "command": "\"${CLAUDE_PLUGIN_ROOT}/scripts/statusline.sh\""
  }
  ```

  `${CLAUDE_PLUGIN_ROOT}` is not expanded inside `settings.json`, so resolve
  it to the plugin's absolute path before writing.

- **A `statusLine` already exists** — do not overwrite it. Show the user their
  current one, then offer two options: replace it with this plugin's version,
  or keep theirs and copy in just the logging block (lines under the comment
  `# Log account usage to a JSONL history`) plus the `rate_limits` parsing at
  the top. The logging block is independent of the rendering, so it grafts
  onto any existing status line.

### 3. Confirm before writing

Editing `settings.json` changes behavior on every session. Show the exact diff
and get agreement before applying it.

### 4. Verify

The status line only receives `rate_limits` for Claude.ai subscribers, and
only after the first model response of a session. Tell the user the second
line will appear on their next message, and that the log at
`~/.claude/usage-log.jsonl` (override with `CLAUDE_USAGE_LOG`) begins filling
from that point. There is no backfill — the report needs about two weeks of
history before its verdict is worth acting on.
