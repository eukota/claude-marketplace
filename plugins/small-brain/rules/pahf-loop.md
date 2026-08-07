---
name: pahf-loop
description: Behavioral rules for the Small Brain PAHF loop — passive input capture, grounding, correction handling, and when to escalate.
---

# Small Brain PAHF Loop Rules

## Core Behavior

Small Brain operates passively. You do not announce that you are running the PAHF loop. You run it as part of normal conversation.

## Before Acting on a Significant Request

1. Check if any loaded principles apply to this situation (see SessionStart context).
2. If a principle applies and `principle_auto_answer` is **on**: apply it silently, note it briefly ("grounding in your principle: X").
3. If `principle_auto_answer` is **off**: surface the principle and confirm before applying.
4. If no principle applies: ask a clarifying question naturally, as part of the conversation.

## When the User Corrects You

When the user says you got something wrong, redirects you, or states a preference:

1. Acknowledge the correction briefly.
2. Identify what principle this establishes or modifies.
3. Write it to memory immediately:
   ```bash
   python3 ~/.claude/plugins/small-brain/scripts/write.py correction \
     --brain-id <brain-id> \
     --decision-id <decision-id-if-known> \
     --feedback "<what user said>" \
     --principle "<extracted principle>" \
     --weighting "<new weighting if applicable>"
   ```
4. Confirm: "Stored: [principle]"

Do this quietly. One line. Do not over-explain.

## When Writing a Decision to Memory

After making a significant decision, log it:
```bash
python3 ~/.claude/plugins/small-brain/scripts/write.py decision \
  --brain-id <brain-id> \
  --context "<what the situation was>" \
  --decision "<what you decided>" \
  --grounding "<which principle or 'none'>"
```

## When the UserPromptSubmit Hook Returns CAPTURE_SIGNAL

The hook may return a signal like: `CAPTURE_SIGNAL: user prefers X over Y`

When you see this in your context, write it as a correction to the active brain. Use the most relevant `--decision-id` if one exists, otherwise use `--decision-id unknown`.

## Escalation Rules

- If `conflict_resolution` is **auto** and principles resolve a multi-brain conflict: resolve silently.
- If `conflict_resolution` is **manual**: always surface the conflict with all positions.
- If principles **cannot** resolve a conflict: always escalate to user regardless of settings.

## What NOT to Do

- Do not announce "I am now running the PAHF loop."
- Do not ask permission before storing a correction — store it, then confirm briefly.
- Do not over-clarify simple, unambiguous requests.
- Do not surface principles that are not relevant to the current situation.
