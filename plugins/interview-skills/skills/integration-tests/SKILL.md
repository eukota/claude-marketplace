---
name: integration-tests
description: Use when the candidate in an AI-assisted interview wants integration tests for their app. This is a meta-skill; it instructs Claude to build the integration tests plus an observability dashboard with click-triggered test runs, every time.
---

# Integration tests, with a dashboard and click-to-run

Integration tests are where a candidate demonstrates the whole system working. This skill tells Claude to **build** the pieces below in the candidate's project, in the language and framework already there. Nothing here ships as code; build it fresh and keep it small.

**Non-negotiable:** whenever integration tests are built, also build the dashboard and the click-triggered runs. Never deliver tests alone.

## 1. The tests

- Exercise the **real running app** through its real interface (HTTP for an API, the browser for a UI). Do not mock the app itself.
- Reset to seeded data before each run so runs are repeatable.
- Cover the core journey end to end, then the failure and conflict paths the candidate found in `review` and `verify`.

## 2. Observability

- Test runs append **structured results** (one JSON object per line: run id, test name, pass or fail, duration, error message) to `logs/test-runs-latest.jsonl`.
- The app logs one structured line per request to `logs/app-latest.log`.
- Both files are in a gitignored `logs/` folder. Keep secrets, tokens and personal data out of them.

## 3. The dashboard

One local page, bound to localhost, served by a small process in the candidate's stack. Plain HTML is fine; no new framework. It shows:

- the latest result for each test, and the last run's overall state;
- run history: pass rate and durations across runs;
- the failure message for any failing test;
- a live tail of the app log.

It refreshes itself (polling is fine).

## 4. Click-triggered runs

Buttons on the dashboard, wired to the real tests through an endpoint on the dashboard process:

- **Run all** and **run one** per test;
- **Hammer:** repeat the run N times, with a visible counter and pass or fail tally. Cap N so it can't run away. Resetting data between runs is the default.

Make every click leave a result in `logs/test-runs-latest.jsonl` that shows up on the page.

## 5. Interview time

Tell the AI this is an MVP and time-boxed. Build tests first, then the dashboard, and say aloud why: "I want to see the system under repeated runs, not just once."

## Settings

If `interview/config.md` exists, read it and the rules in `${CLAUDE_PLUGIN_ROOT}/skills/configure/references/settings.md`. For this skill: Build in `stack`. If `time` is under 45 minutes, build the smallest dashboard first (latest results and run buttons) and add history and the log tail only if time remains. The tests, the logs and the dashboard are never skipped.

## Done when (show the evidence; do not claim it)

1. The dashboard URL loads (show a 200 or the page itself).
2. One click, or its equivalent request, runs a test, and a new line with that run id appears in `logs/test-runs-latest.jsonl`.
3. The result appears on the dashboard, and a hammer run of a few repeats completes with a correct tally.
4. Report what the logs show, including any failure. Save a short note to `interview/06-integration.md` with the URL, how to run it, and the evidence.
