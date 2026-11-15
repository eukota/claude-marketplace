---
name: narrate
description: Use at any point in an AI-assisted interview when the candidate needs a short script to explain a decision aloud, handle an AI mistake, or wrap up with what they would do next.
---

# Narrate

The interviewer can only score what they can hear. Keep each beat to a sentence or two.

## Do

Offer the candidate the beat that fits the moment, as a prompt to answer in their own words, not as a script to read.

- **Opening:** "I'll prep, plan briefly, then build the smallest working version with parallel agents, including an observability dashboard, and test it end to end."
- **Prep:** "I've started research in the background while I ask you some questions, then I'll trim it to what we're building."
- **Agents running:** what each agent owns, what the contract is, and what you will check when they finish.
- **Reading AI output:** what you are gaining or noticing, and what you doubt.
- **Rejecting or changing something:** what, and why, in one sentence.
- **AI got it wrong:** say so plainly, name the cause (invented field, missing edge case), and fix it. This reads as control, not failure.
- **Skipping something:** "I'm leaving X out on purpose because of time; I'd add it next."
- **Running low on time:** cut scope aloud and protect the core journey and its integration test.
- **Wrap-up:** what works (with evidence) and what is not covered. For what you would do for real, use `commentary`.

## Signals worth using on purpose

Voice input is fine and signals comfort with the tool; expect transcription noise and say that you do. Name the process you are using ("I'm running the review checks") so skills show up as method.

## Settings

If `interview/config.md` exists, read it and the rules in `${CLAUDE_PLUGIN_ROOT}/skills/configure/references/settings.md`. For this skill: If `voice` is `yes`, remind the candidate to mention transcription noise. `narration: short` gives one-sentence prompts; `narration: full` gives the full set above.

## Done when

The candidate has said the wrap-up aloud: what works, the evidence, and the gaps.
