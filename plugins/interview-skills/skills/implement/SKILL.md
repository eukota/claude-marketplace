---
name: implement
description: Use after plan.md is finished in a practice run of an AI-assisted interview, to write the shared contract, dispatch many agents in parallel (the system, an observability dashboard and the clickable tests), integrate their work, and have the candidate review what they produced.
---

# Implement (step 3 of 5)

Budget about 30% of `time`. The build is fast with many agents at once and a contract everyone shares, often about 5 minutes. **Most of this step is the review**, because the candidate has to show they understand what was built.

## Do

1. **Write the shared contract first.** Copy the Shared contract section of `interview/plan.md` into real files (types, schema, route list) before any agent starts. Everything else depends on it.
2. **Dispatch the agents in parallel,** one per unit in the Work split: the system's units, the observability dashboard (see `observability` for the dispatch phrase and what it must deliver), and the clickable tests (see `test`). Each brief carries:
   - its unit, and the files it owns. It must not edit anything else;
   - the contract files, plus pointers to `prompt.md`, `plan.md` and `best_practices.md`;
   - the real data shapes, constraints and stack, "MVP only", in-memory storage, and a time window shorter than the real one (AI judges time poorly);
   - an instruction to write into files, not chat, and to skip what **Not doing** lists.
   If the plan has fewer units, dispatch what it has and say why.
3. **Let them run.** Don't iterate on proposals mid-build. Track every thread, and use the wait to say what each agent owns and what you will look at first (see `narrate`).
4. **Circle back to every agent,** not only the first. Check each result against the contract.
5. **Integrate:** run the system and open the dashboard. Fix mismatches at the contract, not by patching one side.
6. **Review the changed files, not the chat. This is the main event, so give it the most time.** Start with the riskiest part of the plan, then work outward. Check for:
   - invented APIs, fields or library calls that aren't in the real data;
   - scope beyond the MVP;
   - empty, null, duplicate, invalid and failure paths;
   - mismatch with what the interviewer said and what real responses show;
   - secrets, open endpoints or personal data in logs.
7. **Show understanding, in the candidate's own words.** The AI can explain anything the candidate doesn't follow, and the candidate then says it back. Pick at least two:
   - walk one request through the system from end to end, naming the files it touches;
   - explain what each agent's unit does and how it honors the contract;
   - explain a design choice and the alternative that was rejected;
   - point to the part of the code they trust least, and say why.
8. Save what was dispatched, found and changed to `interview/implement.md`.

## The candidate does the thinking

The candidate says what they found aloud and directs **at least one change** before Claude fixes anything. Reading the output and explaining it unaided is the point of the step; asking the AI to explain is fine, repeating it back without understanding is not. If something is unclear, ask the AI to explain it and compare it to a pattern the candidate knows.

## Settings

If `interview/config.md` exists, read it and `${CLAUDE_PLUGIN_ROOT}/skills/configure/references/settings.md`. Use `stack` and `ai_tool` so briefs match what is in use and how the tool dispatches agents. Use `level` for how much the briefs spell out (entry) against how much they ask agents to propose and justify (senior). Entry level may stop the review after the first three checks.

## Done when

The contract files exist, every agent's work was checked, the system runs with the dashboard showing it, the candidate explained at least two things in their own words, and `implement.md` records one candidate-directed change.

Next: `/interview-skills:test`.
