---
name: commentary
description: Use at the end of a practice run of an AI-assisted interview, after the build and tests, when the candidate wants a short spoken close on what they would do if this were built for real, tied to what they chose not to do.
---

# Commentary (step 5 of 5)

A short, spoken close. The candidate says what the real version of this work would include and that the cuts were deliberate. Budget about 10% of `time`. Say it; don't do it, because the time is gone.

## Do

1. Read `interview/plan.md` (the **Not doing** list) and `interview/test.md` (the gaps). These are the sources.
2. Draft 3 to 5 items for the candidate to say, ordered by what would matter most for **this** app. Each is a technique with a reason, not "more testing". Examples to draw from, if they fit:
   - **Reviewer and fixer agents, looped** several times to tighten file size, security and performance.
   - Dependency and secrets audits.
   - Load or concurrency testing against the dashboard's own numbers.
   - Persistent storage, migrations and backups.
   - CI running the same clickable tests on every change.
   - Error handling, alerting and real monitoring behind the dashboard.
   - Accessibility and documentation.
3. Tie each item to a specific cut ("I left out auth to protect time; for real, I'd add it first").
4. The candidate says it aloud in their own words, and picks the order.
5. Save the list to `interview/commentary.md`.

## The candidate does the thinking

Claude drafts the list. The candidate removes what doesn't fit, adds at least one item of their own, and decides the order.

## Settings

If `interview/config.md` exists, read it and `${CLAUDE_PLUGIN_ROOT}/skills/configure/references/settings.md`. `level` sets the depth: entry names two or three items, senior adds trade-offs and sequencing. `narration: short` keeps each item to one sentence.

## Done when

`commentary.md` exists, the candidate has said 3 to 5 items aloud, and each one connects to a deliberate cut.
