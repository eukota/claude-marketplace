---
name: plan
description: Use after prep is finished and before any code is written in an AI-assisted interview, to produce plan.md that follows prompt.md and best_practices.md, splits the work so many agents can build in parallel, including an observability dashboard and the clickable tests, and is trimmed by the candidate.
---

# Plan (step 2 of 5)

One artifact: `interview/plan.md`. Budget about 15% of `time`. A plan the candidate has pushed back on beats a long plan they accepted.

## Do

1. **Start from the artifacts.** Read `interview/prompt.md` and `interview/best_practices.md`. If either is missing, run `prep` first. Say the framing aloud: "AI could design for hours, but this is an interview, so I'm asking for a quick plan."
2. **Ask for a plan that follows them,** with these sections, in this order and short:
   1. **Summary:** five lines or fewer, in plain language a non-engineer could follow.
   2. **Diagram:** one picture of the components and the main flow, as a Mermaid block (or ASCII if it won't render).
   3. **Shared contract:** the routes, data shapes and names every part must agree on, what the system **reports about itself** (the event shape the dashboard reads), and the **test scenarios** the clickable tests will run. This is defined first, so the pieces fit.
   4. **Work split:** units that can be built in parallel: the system's units, plus an **observability dashboard** unit and a **clickable tests** unit (see `observability` and `test`). Each lists the files it owns, with no file in two units. If the boundaries aren't clean, say so and plan fewer units.
   5. **Build order and minute budget** for each unit.
   6. **Riskiest part,** and **Not doing** (auth, persistence, polish).
   7. **Observability and tests:** say in a sentence that the system will be observable and why, and name the riskiest behaviors the clickable tests will demonstrate.
3. **Review and trim.** The candidate reads the Summary and Diagram aloud, then **pushes back at least once:** remove something, reprioritize, or reject an approach with a reason. Cross-check against "Out of scope" in `prompt.md`. If a cut changes the agreed scope, confirm it with the interviewer.
4. Record what changed from the first draft at the bottom of `plan.md`.

## The candidate does the thinking

Claude drafts. The candidate decides what stays. If the candidate hasn't changed anything, the review isn't finished.

## Settings

If `interview/config.md` exists, read it and `${CLAUDE_PLUGIN_ROOT}/skills/configure/references/settings.md`. Use `time` for the minute budget, `stack` to name the components, and `level` to set how much the plan weighs trade-offs (senior) against a single working path (entry).

## Done when

`plan.md` has all seven sections, the work split has no overlapping files, and one change the candidate made is recorded.

Next: `/interview-skills:implement`.
