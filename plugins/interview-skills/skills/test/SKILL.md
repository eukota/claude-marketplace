---
name: test
description: Use after implementation in an AI-assisted interview, to bring the system, the observability dashboard and the clickable tests together, run the tests while watching the system operate, add the candidate's own edge cases, and iterate on what breaks.
---

# Test (step 4 of 5)

The tests are a set of clickable demonstrations, watched on the dashboard as the system operates. Budget about 30% of `time`. Most of the building happened in `implement`; this step is where it comes together and gets proven.

## What the tests are

Few and meaningful. Each clickable test is a demonstration of a behavior that matters, taken from the plan's riskiest parts and the scenarios in its contract. Each one runs against the **real running system** (through HTTP for an API, the browser for a UI), resets to seeded data first so it repeats, and has a name, what it checks, and its latest result. Click one to run it; "run all" runs every one. Hammering (repeat runs with a tally) is an optional extra if time remains.

## Do

1. **Bring it together.** Start the system, the dashboard and the tests. Fix mismatches at the contract.
2. **Run the clickable tests while the dashboard is on screen.** Say what you expect before each click, then watch the activity appear and the result land.
3. **Check the tests themselves.** Look at the inputs, not only the results: empty, very long, special characters, wrong types, duplicates and bad requests.
4. **The candidate adds two or more edge cases of their own** as new clickable tests, then reruns.
5. **Iterate on what breaks.** Decide whether the code or the test is wrong before changing either. Rerun and show the fix.
6. Save the evidence and the gaps to `interview/test.md`.

If the dashboard or the tests were not built in `implement`, build them now with `observability` before running anything.

## The candidate does the thinking

The candidate chooses which behaviors deserve a test, predicts the result before each click, and adds their own edge cases.

## Settings

If `interview/config.md` exists, read it and `${CLAUDE_PLUGIN_ROOT}/skills/configure/references/settings.md`. Use `stack` for the test tooling in the project. Use `time` to decide how many cases to add. The clickable tests, the logs and the dashboard are never skipped.

## Done when (show the evidence; do not claim it)

1. A click runs a test and the activity appears on the dashboard as it happens.
2. The same events and the result appear in the log file, with a run id.
3. At least two candidate edge cases were added and run, and one failure (if any) was understood and fixed.
4. Report what the logs show, including failures. List the gaps you are not covering in `interview/test.md`.

Next: `/interview-skills:commentary`.
