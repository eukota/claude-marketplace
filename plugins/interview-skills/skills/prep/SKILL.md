---
name: prep
description: Use at the start of a practice run of an AI-assisted interview, when the candidate has just been given the practice prompt, to build prompt.md with the interviewer while a background agent gathers best_practices.md, then trim the research to the scope that will be built.
---

# Prep (step 1 of 5)

Two artifacts, built at the same time: `interview/prompt.md` and `interview/best_practices.md`. Budget about 15% of `time`.

## Do

1. **Start the research first.** Dispatch a background subagent (or a parallel session if the AI tool has no subagents) before anything else. Tell it:
   - the prompt as given, the stack, and that this is a time-boxed interview build;
   - to write **short, succinct bullets**, grouped by topic, to `interview/best_practices.md`. Aim for 15 to 25 bullets: design choices, common pitfalls, and what to skip in a short build.
2. **Meanwhile, build `interview/prompt.md` with the interviewer** (in practice, your instructor, a partner, or the AI playing the role). Restate the prompt in one sentence, aloud. Draft 5 to 8 questions, ordered by how much each narrows the problem: the user, the one core journey, the data that exists, what "done" means in this session, and what is out of scope. Prefer questions that shrink scope. Ask them, and write the answers in as they come. If an API or data source is supplied, call it and paste the real response shapes in, not a description.
3. **Give `prompt.md` a fixed shape:** Goal (one sentence), Interviewer answers, Constraints and assumptions (one line each for anything unanswered), Out of scope, and a closing line: "Follow `best_practices.md`. Where it conflicts with this file, this file wins."
4. **Circle back.** When the research returns, read it. Do not move on before this step is finished.
5. **Trim `best_practices.md`.** Delete every bullet that isn't needed for the smallest version that satisfies `prompt.md`. List what was cut at the bottom. For a cut that changes the agreed scope, confirm it with the interviewer in a sentence.

## The candidate does the thinking

The AI drafts the questions and does the research. The candidate cuts, reorders and adds at least one question of their own, and decides what to trim. Never ask the interviewer's questions for the candidate unread.

## Settings

If `interview/config.md` exists, read it and `${CLAUDE_PLUGIN_ROOT}/skills/configure/references/settings.md`. Use `time` to size the scope so it is finishable, `level` to set the depth of the questions (entry keeps to the core journey, mid adds data and failure cases, senior adds scale, operations and trade-offs), and `stack` for the research brief.

## Done when

Both files exist; `prompt.md` has answers, assumptions and out-of-scope; `best_practices.md` is trimmed with its cut list; and the candidate has said aloud what they are building and what they cut.

Next: `/interview-skills:plan`.
