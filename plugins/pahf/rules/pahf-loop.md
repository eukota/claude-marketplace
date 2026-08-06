---
name: pahf-loop
description: Behavioral rules for the PAHF loop — when to clarify, ground, correct, and compress automatically.
---

# PAHF Loop Rules

## Core Loop

Every significant action follows this sequence:
1. **Clarify** (pahf-clarify) — before acting on an ambiguous or consequential request
2. **Ground** (pahf-ground) — before deciding, check memory for relevant principles or past decisions
3. **Act** — proceed from the grounding
4. **Correct** (pahf-correct) — if the user corrects the output, extract and store the principle

## When to Auto-Clarify

Trigger pahf-clarify before:
- Writing code that makes a design decision
- Taking an action with side effects (commit, push, deploy, delete)
- Responding to an underspecified request where multiple interpretations exist
- Making a call that touches a domain the brain has learned preferences for

Do NOT over-clarify. Simple, clear requests do not need a clarify step.

## When to Auto-Ground

Trigger pahf-ground before:
- Any decision in a domain where principles exist in memory
- Any decision where a past correction is relevant
- When the user is asking for a recommendation (not just execution)

## When to Auto-Correct

Trigger pahf-correct whenever:
- The user says you got something wrong
- The user says "remember this", "always do X", "never do Y"
- The user redirects you mid-task with an explanation
- The user explicitly resolves a conflict you surfaced

## When to Compress

Compress when:
- The user explicitly requests it
- A session ends with 5+ decisions logged
- The user asks "what have you learned?" or "what principles do you have?"

## What NOT to Do

- Do not clarify before simple, unambiguous tasks
- Do not pause to ground if no memory exists for the domain yet
- Do not over-explain the PAHF loop to the user — run it quietly, surface only what matters
- Do not ask for permission to store corrections — store them and confirm briefly
