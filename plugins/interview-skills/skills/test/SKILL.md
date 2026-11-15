---
name: test
description: Use after implementation in an AI-assisted interview, to show the code works with quick checks and edge cases, and to build integration tests together with an observability dashboard and click-triggered test runs every time. This is a meta-skill that instructs Claude what to build.
---

# Test (step 4 of 4)

"It works" needs evidence on screen. Budget about 30% of `time`. This skill tells Claude to **build** the pieces below in the candidate's project, in its stack. Nothing here ships as code; build it fresh and keep it small.

## A. Quick checks of the parts

1. Ask for tests of the **core flows first**, happy path only for speed. Name the kinds wanted (unit, integration, regression) so the intent is visible.
2. Put them in real files and **run them**. Show the output.
3. **Review the test inputs, not only the results.** Check for empty, very long, special characters, wrong types, duplicates and bad requests.
4. The candidate adds **two or more edge cases from their own domain knowledge**, then directs the AI to expand coverage.
5. If a test fails, decide whether the code or the test is wrong before changing either.

## B. Integration tests, dashboard and click-to-run

**Non-negotiable:** whenever integration tests are built, also build the dashboard and the click-triggered runs. Never deliver tests alone.

- **Tests:** exercise the **real running app** through its real interface (HTTP for an API, the browser for a UI), with no mock of the app itself. Reset to seeded data before each run. Cover the core journey end to end, then the failure and conflict paths found in `implement`.
- **Observability:** each test run appends one structured JSON line (run id, test name, pass or fail, duration, error) to `logs/test-runs-latest.jsonl`. The app logs one structured line per request to `logs/app-latest.log`. `logs/` is gitignored. No secrets, tokens or personal data in logs.
- **Dashboard:** one local page, bound to localhost, served by a small process in the candidate's stack. Plain HTML is fine. It shows the latest result per test, run history (pass rate and durations), the failure message for any failing test, and a live tail of the app log. It refreshes itself.
- **Click-triggered runs:** buttons wired to the real tests through an endpoint on the dashboard process: **run all**, **run one**, and **hammer** (repeat N times, with a visible counter and pass or fail tally, and N capped). Every click leaves a result in `logs/test-runs-latest.jsonl` that shows on the page.

Build the tests first, then the dashboard, and say aloud why: "I want to see the system under repeated runs, not just once."

## Settings

If `interview/config.md` exists, read it and `${CLAUDE_PLUGIN_ROOT}/skills/configure/references/settings.md`. Build in `stack`. Use `time` to decide how many cases to add. If `time` is under 45 minutes, build the smallest dashboard first (latest results and run buttons) and add history and the log tail only if time remains. The tests, the logs and the dashboard are never skipped.

## Done when (show the evidence; do not claim it)

1. The test output was shown, and the candidate added two or more edge cases.
2. The dashboard URL loads (show a 200 or the page).
3. One click, or its equivalent request, runs a test, and a new line with that run id appears in `logs/test-runs-latest.jsonl`.
4. The result appears on the dashboard, and a hammer run of a few repeats completes with a correct tally.
5. Report what the logs show, including any failure. Save the URL, how to run it, the evidence and the gaps you are not covering to `interview/test.md`.
