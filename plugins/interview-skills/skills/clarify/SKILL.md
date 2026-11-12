---
name: clarify
description: Use at the start of an AI-assisted interview, when the candidate has just been given a prompt and needs to turn it into clarifying questions, stated assumptions, and a scope narrow enough to finish in the time available.
---

# Clarify

The prompt is deliberately vague. Questions are the first thing the interviewer scores.

## Do

1. Restate the prompt in one sentence. The candidate says it aloud.
2. Draft **5 to 8 questions** for the interviewer, ordered by how much each one narrows the problem. Cover: who the user is, what the one core journey is, what data exists, what "done" looks like in this session, and what is explicitly out of scope.
3. Prefer questions that **shrink scope** over questions that grow it. The candidate controls the narrative by choosing a problem they can complete.
4. Write what the candidate will **assume** if the interviewer doesn't answer, one line each.
5. Save to `interview/01-clarify.md` in the candidate's project (create the folder). Keep it under one screen. Screen-shared, it is the proof of foresight.

## The candidate does the thinking

Offer a draft, then have the candidate cut, reorder and add at least one question of their own. Never ask the interviewer's questions for them without the candidate reading them first.

## Settings

If `interview/config.md` exists, read it and the rules in `${CLAUDE_PLUGIN_ROOT}/skills/configure/references/settings.md`. For this skill: Use `time` to size the scope so it is finishable in that many minutes, and `level` to set the depth of the questions: entry keeps to the core journey, mid adds data and failure cases, senior adds scale, operations and trade-offs.

## Done when

The file exists with questions, assumptions and a one-line scope statement, and the candidate has asked the top questions aloud.
