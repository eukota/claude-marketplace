---
name: pahf-ground
description: Ground a decision in memory before acting. Checks past decisions and extracted principles for relevant prior context, then proceeds from the highest applicable abstraction level.
---

# PAHF Grounding in Memory

Before deciding, walk the memory hierarchy top-down to find the most relevant prior context.

## Memory Hierarchy (top-down)

1. **Meta-principles** — How to weight conflicting principles. Check first.
2. **Principles** — Extracted patterns (e.g., "minimize state", "optimize for human experience"). Check second.
3. **Decisions** — Past specific decisions and their outcomes. Check third.
4. **Raw corrections** — Direct user corrections to past decisions. Check last.

## Steps

1. Run: `python3 ~/Development/small-brain-alpha/scripts/memory_query.py --domain <domain> --context "<context>"`
2. Read the returned matches — principles, past decisions, corrections.
3. Pick the **highest abstraction level** that applies:
   - Meta-principle applies → proceed from meta-principle, state it
   - Principle applies → proceed from principle, state it
   - Past decision applies → ground there, state the prior decision
   - Nothing applies → note "no prior context" and proceed with clarification
4. State what you found and how it informs your approach.

## Format

```
Memory check for: [context summary]
Found: [principle / past decision / none]
Grounding: [how this shapes the decision]
```

## When to Use

- After pahf-clarify, before acting
- When the user corrects you (check what principle this correction establishes)
- When making decisions in a domain the brain has been trained on
