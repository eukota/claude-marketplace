---
name: review
description: Use right after the AI generates code in an AI-assisted interview, when the candidate must read it critically and show they did not accept it blindly.
---

# Review

Accepting AI output unread is the red flag interviewers look for. Reviewing aloud is the signal.

## Do

1. Skim the changed files, not the chat. Look for lists, structure and anything surprising. Ask the AI to summarize parts the candidate skipped.
2. Run through this checklist and write hits to `interview/04-review.md`:
   - **Invented things:** APIs, fields, endpoints or library calls that don't exist in the real data.
   - **Scope creep:** features, layers or abstractions beyond the MVP.
   - **Edge cases:** empty, null, duplicate, invalid and failure paths.
   - **Wrong assumptions:** does it match what the interviewer said and what the real responses show?
   - **Secrets and unsafe defaults:** keys, open endpoints, logged personal data.
3. The candidate says what they found aloud, picks **at least one thing to change**, and directs the AI to change it.
4. If something is unclear, ask the AI to explain it and compare it to a pattern the candidate knows.

## The candidate does the thinking

Claude produces the checklist. The candidate must find and name at least one real issue in their own words before Claude fixes anything.

## Settings

If `interview/config.md` exists, read it and the rules in `${CLAUDE_PLUGIN_ROOT}/skills/configure/references/settings.md`. For this skill: Use `level` to set the depth of the checklist: entry may stop after invented things, scope creep and edge cases, while mid and senior run all five items.

## Done when

`interview/04-review.md` lists what was checked and found, and one change was directed by the candidate.
