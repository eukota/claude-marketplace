---
name: configure
description: Use before a practice run of an AI-assisted interview, or whenever the candidate wants to change how the other interview skills behave, to set time, level, stack, AI tool, voice, narration and which skills to skip in a short config file the other skills read.
---

# Configure

The other skills have sensible defaults. This one fits them to this candidate and this interview in about a minute. It writes one small file, `interview/config.md`, that every other skill reads.

The settings, their allowed values and the rules for applying them are in `${CLAUDE_PLUGIN_ROOT}/skills/configure/references/settings.md`. Read it first.

## Do

1. Check for an existing `interview/config.md`. If there is one, show it and ask what to change. If nothing changes, stop.
2. Ask in two short rounds. Show the default in brackets, but make the candidate answer:
   - **Round 1:** minutes available for the build, and level (entry, mid or senior).
   - **Round 2:** stack, AI tool, voice input (yes or no), narration (short or full), and any skills to skip.
3. Write `interview/config.md` in the format in the settings reference. Create the `interview/` folder if needed.
4. Read it back as one line per setting that says what it changes, for example "time: 45, so each step gets a smaller minute budget and observability builds the smallest dashboard first".
5. Suggest the next step, usually `/interview-skills:prep`.

## The candidate does the thinking

Don't choose the level for them. If they don't know their level, ask what role they are practicing for, default to `mid`, and say that you did. A setting the candidate has to explain, such as why they are skipping a skill, is a setting they understand.

## Done when

`interview/config.md` exists, the candidate has confirmed it, and the one-line-per-setting summary has been read back.
