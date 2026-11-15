---
name: observability
description: Use during a practice run of an AI-assisted interview when the candidate plans or dispatches the agent that builds the observability dashboard, to give the dispatch phrasing and say what the dashboard must show so the system's activity is visible as it happens.
---

# Observability

Naming observability out loud and then rendering it on screen is the signal. This skill is the moment the candidate asks for the dashboard, and what it must deliver. Nothing here ships as code; Claude builds it fresh, in the candidate's stack, as one parallel agent.

## When

- In `plan`, the dashboard is its own unit in the work split, and the contract says what the system reports about itself.
- In `implement`, it is dispatched alongside the system's units.

## The dispatch phrase

Offer this as a prompt for the candidate to say in their own words:

> "Also dispatch a parallel agent to build out an observability dashboard that shows the system operating, so I can add integration tests I can watch."

## What the dashboard must deliver

- **Live activity.** Each request and event the system handles appears as it happens, in order: what came in, what the system did, what went out.
- **State you can read.** The current data or status the demo depends on, updated as it changes.
- **Results from the tests.** The latest result per clickable test, with the failure message when one fails (see `test`).
- **Readable at a glance** on a shared screen. One local page, bound to localhost, in the stack already in use. Plain is fine.

## What it needs from the system

The system emits one structured line per request or event (time, what happened, outcome) to a gitignored `logs/` folder, and the dashboard reads from that. No secrets, tokens or personal data in logs. The contract in `plan.md` defines the event shape first so the dashboard agent and the system agents agree.

## Settings

If `interview/config.md` exists, read it and `${CLAUDE_PLUGIN_ROOT}/skills/configure/references/settings.md`. Build in `stack`. If `time` is under 45 minutes, build the smallest version first (live activity and latest results) and add the rest only if time remains. Observability is never skipped.

## The candidate does the thinking

The candidate says why the system needs to be observable before the AI builds it, and decides what the dashboard must show for this app.

## Done when

The dashboard loads, and a request to the running system appears on it as it happens. Show that on screen.
