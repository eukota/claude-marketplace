---
name: configure
description: Use before an AI-assisted interview or practice run, or whenever the candidate wants to change how the other interview skills behave, to set time, level, stack, AI tool, voice, narration and which skills to use in a short config file the other skills read.
---

# Configure

The other skills have sensible defaults. This one fits them to this candidate and this interview in about a minute. It writes one small file, `interview/config.md`, that every other skill reads.

The settings, their allowed values and the rules for applying them are in `${CLAUDE_PLUGIN_ROOT}/skills/configure/references/settings.md`. Read it first.

## Do

1. Check for an existing `interview/config.md`. If there is one, show it and ask what to change. If nothing changes, stop.
2. Ask in two short rounds. Show the default in brackets, but make the candidate answer:
   - **Round 1:** mode (practice or real), minutes available for the build, and level (entry, mid or senior).
   - **Round 2:** stack, AI tool, voice input (yes or no), narration (short or full), and any skills to skip.
3. In a real interview, ask only Round 1 and the stack and AI tool. Use defaults for the rest, and say so.
4. Write `interview/config.md` in the format in the settings reference. Create the `interview/` folder if needed.
5. Read it back as one line per setting that says what it changes, for example "time: 45, so plan will put a minute budget on each step".
6. Suggest the next step, usually `/interview-skills:clarify`.

## The candidate does the thinking

Don't choose mode or level for them. If they don't know their level, ask what the interviewer said or what role it is, default to `mid`, and say that you did. A setting the candidate has to explain, such as why they are skipping a skill, is a setting they understand.

## Done when

`interview/config.md` exists, the candidate has confirmed it, and the one-line-per-setting summary has been read back.
