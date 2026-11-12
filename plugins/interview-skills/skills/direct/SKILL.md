---
name: direct
description: Use when the candidate in an AI-assisted interview is about to ask the AI to write code, to build a brief that carries the plan, constraints and real data shapes so the AI does not invent them.
---

# Direct

The brief is where the candidate shows they are in control. Vague prompts get invented data models.

## Do

1. Build the brief from `interview/02-plan.md`. Include:
   - **Goal** in one sentence and the **MVP** boundary.
   - **Constraints:** language and framework already in use, in-memory storage, a shorter time window than the real one (AI is poor at judging time).
   - **Real shapes:** paste actual API responses or schema, not a description. If an API or data source is supplied, call it first and use what comes back.
   - **Skipping on purpose:** the Not-doing list, so it isn't gold-plated.
2. Tell the AI to write **into files**, not chat, so the candidate can review and edit the real code.
3. For a large build, let the AI move fast and review after. Don't iterate on proposals during implementation.
4. Offer parallel work only when components have a clean boundary (for example API and UI) and the candidate can track both and integrate them.
5. Save the brief to `interview/03-brief.md` before sending.

## The candidate does the thinking

The candidate states the constraints. If they don't know a real shape yet, the next step is to go find out, not to let the AI guess.

## Done when

The brief names real shapes and constraints, and the AI is writing to files.
