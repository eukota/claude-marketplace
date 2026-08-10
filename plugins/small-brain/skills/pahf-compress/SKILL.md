---
name: pahf-compress
description: Run the distillation loop — extract principles from recent decisions and corrections, detect brain split signals.
---

# PAHF Compress (Distillation Loop)

## Steps

1. **List brains and ask which to compress (or all):**
   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/brain.py list
   ```

2. **Run compression with split detection:**
   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/compress.py \
     --brain-id <brain-id> \
     --num-recent 20 \
     --detect-split
   ```

3. **Show extracted principles** to the user. Ask: are any of these wrong or weighted incorrectly?

4. **If user corrects a principle**, write the correction and re-run.

5. **If `SPLIT_SIGNAL` appears in output**, surface it to the user:
   > "The distillation loop found two principle clusters that keep conflicting. This may mean they represent different viewing angles — for example, your SRE thinking vs. your maker thinking. Should I create a second brain for one of these clusters?"
   
   If yes: use `/small-brain-setup` to create the new brain, then note which principles migrate to it.

6. **Run meta-principle extraction** if 2+ principles exist:
   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/compress.py \
     --brain-id <brain-id> \
     --meta-only
   ```

7. **Show the final memory state.**
