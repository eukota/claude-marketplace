---
name: implement
description: Use after plan.md is finished in an AI-assisted interview, to write the shared contract, dispatch agents in parallel to build the plan, integrate their work, and have the candidate review what they produced.
---

# Implement (step 3 of 4)

Budget about 40% of `time`. Speed comes from parallel agents and a contract everyone shares.

## Do

1. **Write the shared contract first.** Copy the Shared contract section of `interview/plan.md` into real files (types, schema, route list) before any agent starts. Everything else depends on it.
2. **Dispatch the agents in parallel,** one per unit in the Work split. Each brief carries:
   - its unit, and the files it owns. It must not edit anything else;
   - the contract files, plus pointers to `prompt.md`, `plan.md` and `best_practices.md`;
   - the real data shapes, constraints and stack, "MVP only", in-memory storage, and a time window shorter than the real one (AI judges time poorly);
   - an instruction to write into files, not chat, and to skip what **Not doing** lists.
   If the plan has one unit, build it with one agent and say why.
3. **Let them run.** Don't iterate on proposals mid-build. Use the time to rehearse the explanation (see `narrate`).
4. **Circle back to every agent,** not only the first. Check each result against the contract.
5. **Integrate:** run the whole app. Fix mismatches at the contract, not by patching one side.
6. **Review the changed files, not the chat.** Check for:
   - invented APIs, fields or library calls that aren't in the real data;
   - scope beyond the MVP;
   - empty, null, duplicate, invalid and failure paths;
   - mismatch with what the interviewer said and what real responses show;
   - secrets, open endpoints or personal data in logs.
7. Save what was dispatched, found and changed to `interview/implement.md`.

## The candidate does the thinking

The candidate says what they found aloud and directs **at least one change** before Claude fixes anything. If something is unclear, ask the AI to explain it and compare it to a pattern the candidate knows.

## Settings

If `interview/config.md` exists, read it and `${CLAUDE_PLUGIN_ROOT}/skills/configure/references/settings.md`. Use `stack` and `ai_tool` so briefs match what is in use and how the tool dispatches agents. Use `level` for how much the briefs spell out (entry) against how much they ask agents to propose and justify (senior). Entry level may stop the review after the first three checks.

## Done when

The contract files exist, every agent's work was checked, the app runs as a whole, and `implement.md` records one candidate-directed change.

Next: `/interview-skills:test`.
