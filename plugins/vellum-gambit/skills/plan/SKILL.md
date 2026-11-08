---
name: plan
description: Use after requirements are clarified in an AI-assisted interview and before any code is written, when the candidate needs a short, time-boxed design they have shaped themselves.
---

# Plan

A plan the candidate has pushed back on beats a long plan they accepted. Budget 5 to 10 minutes.

## Do

1. Start from the clarified scope (`interview/01-clarify.md`). If it doesn't exist, run `clarify` first.
2. Say the framing aloud: "AI could design for hours, but this is an interview, so I'm asking for a quick plan."
3. Ask for a plan that fits one screen: components, the main data shape, the 4 to 6 steps in build order, and the riskiest part.
4. Name the process wanted ("a short plan", "brainstorm the options") instead of letting it expand.
5. The candidate **reads critically, then pushes back at least once**: remove something, reprioritize, or reject an approach with a reason. Record the change.
6. Add an explicit **Not doing** list (auth, persistence, polish). Skipping on purpose reads as intent, not negligence.
7. Save to `interview/02-plan.md`.

## Defaults for interview time

MVP only, in-memory storage, one core journey first, and the test plan decided now: integration tests over the real running app (see `integration-tests`).

## Done when

The file has components, build order, the riskiest part, a Not-doing list, and one change the candidate made to the AI's first draft.
