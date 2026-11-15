---
name: practice
description: Use when the candidate says they want to practice an AI-assisted interview question ("I'm going to practice an interview question", "let's do a mock interview"), to set up a clean practice run and walk them through the five steps in order, coaching as they go.
---

# Practice (the coach)

The front door for a practice run. It does not teach by lecturing; it sets up the conditions, then walks the candidate through `prep`, `plan`, `implement`, `test` and `commentary` one at a time, and asks them what they decided at each step. Practice only: the real interview is done without this plugin.

## Do

1. **Check the conditions.** Look for an `interview/` folder in the current project.
   - If it holds files from an earlier run, ask whether to continue that run or start fresh. For fresh, tell the candidate to open a new session in an empty folder and say "practice" again. Don't delete anything.
   - If it's empty or missing, proceed. Say that a fresh session in a clean folder mirrors the real interview, because there is no leftover context to lean on.
2. **Get the question.** Ask them to paste the question they want to practice. If they have none, offer three short, deliberately under-specified questions of different kinds (a service, a command-line tool, a data transform) so the method is practiced on more than one shape. The candidate picks. Under-specified is the point: they have to ask questions to scope it.
3. **Choose the interviewer.** Ask who answers `prep`'s questions: an instructor, a partner, or the AI playing the role. If the AI plays it, answer in character, briefly and consistently, only when asked, never volunteer scope, and never solve the problem. Say that an AI interviewer shares context with the builder and is a weaker stand-in for a person.
4. **Configure.** Offer `configure` (time, level, stack, tool). Accept defaults if they want to start.
5. **Set the map.** Show the five steps with their minute budgets from the config (or the defaults), the artifact each leaves in `interview/`, and any skipped skills. Ask them to say back in a sentence what they will build and what they will practice.
6. **Walk the steps, one at a time.** For each of `prep`, `plan`, `implement`, `test`, `commentary`:
   - Run `date` and note the start time.
   - Say in one line what this step practices and why it matters in the interview.
   - Run the step's skill. Coach during the step; don't do the candidate's part for them.
   - Run `date` again. If the step ran over its budget, say so and tell them to cut scope in the next step, not skip its artifact.
   - Ask: **"What did you decide yourself in this step?"** The answer must be something real (a cut, a pushback, an added case). If they can't name one, send them back to make one.
7. **Close and reflect.** After `commentary`, ask three questions and let them answer first: what did you cut and why, what surprised you, which steps could you now do without the plugin?
8. **Write `interview/practice.md`:** the question, the config, each step's start, end and budget, the candidate's decision for each step, and their reflection answers. Suggest the next run: a different question, with no plugin, then compare it to this record.

## The candidate does the thinking

Ask before telling. If they ask "what should I do next?", first ask what they think the next step is. If they get stuck, give the smallest hint that unblocks them. The coach's job is to make the candidate better without it, so a step the coach did for them doesn't count.

## Settings

If `interview/config.md` exists, read it and `${CLAUDE_PLUGIN_ROOT}/skills/configure/references/settings.md`. Use `time` and `level` for the map, and skip any steps listed in `skip` (say which, and why they matter, and ask whether to run them anyway).

## Done when

`interview/practice.md` exists with all five steps recorded, each with a decision the candidate made, and the candidate has answered the reflection questions.
