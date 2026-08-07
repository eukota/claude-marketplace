---
name: small-brain-export
description: Export a brain to a portable JSON file for backup, sharing, or transfer.
---

# Small Brain Export

1. **List brains:**
   ```bash
   python3 ~/.claude/plugins/small-brain/scripts/brain.py list
   ```

2. **Ask which brain to export and where to save it.**

3. **Run export:**
   ```bash
   python3 ~/.claude/plugins/small-brain/scripts/export_brain.py \
     --brain-id <brain-id> \
     --output <path/to/output.json>
   ```

4. **Confirm** what was exported: brain name, decision count, principle count, file path.
