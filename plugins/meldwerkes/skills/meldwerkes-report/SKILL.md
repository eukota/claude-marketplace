---
name: meldwerkes-report
description: Generate a Meldwerkes status report — brains, memory state, decision stats, principles, conflict history.
---

# Meldwerkes Report

Run the report script and present the output:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/report.py
```

After showing the report, offer:
- "Would you like to run a distillation pass? (`/pahf-compress`)"
- "Would you like to export a brain? (`/meldwerkes-export`)"
- "Want to adjust settings (principle auto-answer, conflict resolution mode)?"
