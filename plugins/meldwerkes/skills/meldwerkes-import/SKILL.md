---
name: meldwerkes-import
description: Import a brain from a portable JSON export. Supports provisional trust (confidence discounted) or full trust.
---

# Meldwerkes Import

1. **Ask for the export file path.**

2. **Ask trust level:**
   - **Provisional** (default): principles imported at 70% of original confidence. Treated as "to be verified."
   - **Full**: principles imported at full confidence. Use when importing your own brain from another machine.

3. **Optionally rename** the brain on import (useful if a brain with that name already exists).

4. **Run import:**
   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/import_brain.py \
     <path/to/export.json> \
     --trust <provisional|full> \
     [--rename <new-name>]
   ```

5. **Show what was imported.** If provisional, remind the user:
   > "These principles are marked provisional. As you use this brain and confirm/correct decisions, confidence will adjust to reflect your actual preferences."
