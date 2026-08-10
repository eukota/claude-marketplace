---
name: pahf-correct
description: Post-action correction step of the PAHF loop. When the user corrects a decision, extract what principle was violated or established and write it to memory.
---

# PAHF Post-Action Correction

When the user corrects you, this is the richest training signal in the system. Extract and store it.

## Steps

1. **Acknowledge the correction** — restate what you did wrong or what was right.
2. **Identify the principle** — what rule or preference does this correction establish?
   - Is it a new principle? ("always X in context Y")
   - Does it modify an existing principle? ("X is true except when Z")
   - Does it reveal a priority? ("X matters more than Y when...")
3. **Write to memory**:
   ```bash
   python3 ~/Development/small-brain-alpha/scripts/memory_write.py \
     --type correction \
     --domain <domain> \
     --decision-id <id if known> \
     --feedback "<user's correction>" \
     --principle "<extracted principle>" \
     --weighting "<new weighting if applicable>"
   ```
4. **Confirm** — tell the user what principle was stored.

## Format

```
Correction received: [what was wrong]
Principle extracted: [the rule this establishes]
Stored: ✓
```

## When to Use

- Any time the user says you got something wrong
- Any time the user explicitly says "remember this" or "always do X"
- Any time the user redirects you mid-task
- After the user resolves a conflict between two options you surfaced
