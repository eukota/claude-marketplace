---
allowed-tools: Bash(python3:*)
description: Report Claude plan usage trends and whether to upgrade
---

## Your Task

Run the usage report and interpret it for the user.

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/usage-report.py" $ARGUMENTS
```

`$ARGUMENTS` may contain `--days N` (default 30). If the user asked for a
different span in plain language ("last week", "this quarter"), translate it
to `--days`.

If the script reports that no log exists, tell the user the status line
integration is not installed yet and point them at `/usage-install`. Do not
fabricate numbers — the report is only as good as the logged history.

After showing the output, read the numbers using the `reading-usage-trends`
skill: explain *which* signal drove the verdict and what would change it.
Keep the interpretation to a few sentences; the table already carries the
detail.
