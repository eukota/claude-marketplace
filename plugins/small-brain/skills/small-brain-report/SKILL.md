---
name: small-brain-report
description: Generate a Small Brain status report — brains, memory state, decision stats, principles, conflict history.
---

# Small Brain Report

Run the report script and present the output:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/report.py
```

After showing the report, offer:
- "Would you like to run a distillation pass? (`/pahf-compress`)"
- "Would you like to export a brain? (`/small-brain-export`)"
- "Want to adjust settings (principle auto-answer, conflict resolution mode)?"
