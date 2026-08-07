---
name: small-brain-setup
description: Set up Small Brain — create the first brain, configure settings, verify the memory store is ready.
---

# Small Brain Setup

## Steps

1. **Check for existing brains:**
   ```bash
   python3 ~/.claude/plugins/small-brain/scripts/brain.py list
   ```

2. **If no brains exist**, ask the user:
   - What domain should the first brain cover? (e.g., "software engineering", "SRE", "product decisions")
   - What name should it have?

3. **Create the brain:**
   ```bash
   python3 ~/.claude/plugins/small-brain/scripts/brain.py create \
     --name "<name>" \
     --domain "<domain>" \
     --description "<one sentence>"
   ```

4. **Show current settings:**
   ```bash
   cat ~/.small-brain/settings.json 2>/dev/null || echo "Using defaults"
   ```
   Defaults: `principle_auto_answer: true`, `conflict_resolution: auto`

5. **Ask if they want to change settings.** If yes:
   ```bash
   python3 -c "
   import json, pathlib
   s = {'principle_auto_answer': <true/false>, 'conflict_resolution': '<auto/manual>'}
   p = pathlib.Path.home() / '.small-brain/settings.json'
   p.parent.mkdir(exist_ok=True)
   p.write_text(json.dumps(s, indent=2))
   print('Settings saved.')
   "
   ```

6. **Confirm setup complete.** Tell the user:
   - Brain ID (first 8 chars)
   - Memory location: `~/.small-brain/memory.db`
   - How to check status: `/small-brain-report`
   - The loop is now running passively — no mode to enter
