# interview-skills

Brief interview skills for candidates in AI-assisted technical interviews.

In these interviews you share your screen, work with an AI coding tool, and are judged on how you use it as much as on what you build. This plugin gives you a small set of short skills, one per stage of the interview. Run them on screen and the interviewer sees a deliberate method instead of improvising: you asked good questions, planned before coding, ran agents in parallel against a shared contract, reviewed what they wrote, and proved it works.

## Purpose

- Make good habits quick enough to use under interview time.
- Make foresight **visible**. Every skill leaves a short, readable file in `interview/` in your project.
- Keep **you** doing the thinking. Each skill makes the candidate decide, push back or add something of their own. The AI supports; it doesn't take over. A skill that did the work for you would defeat its purpose.

## The four steps

The interview is four steps. Each leaves a short file in `interview/` that the interviewer can see.

| Step | Skill | What it builds | Artifacts |
| --- | --- | --- | --- |
| 1 | `prep` | A background agent gathers best practices while you build the prompt with the interviewer, then you trim the research to the scope you'll build | `prompt.md`, `best_practices.md` |
| 2 | `plan` | A plan that follows both, with a plain-language summary, a diagram, a shared contract and a work split for parallel agents, reviewed and trimmed by you | `plan.md` |
| 3 | `implement` | The contract first, then agents in parallel, then integration and your review of what they wrote | `implement.md` |
| 4 | `test` | Quick checks and edge cases, then integration tests with an observability dashboard and click-to-run buttons | `test.md`, `logs/` |

Two more skills work alongside them:

| Skill | Use it when | Leaves behind |
| --- | --- | --- |
| `configure` | Before you start, or when you want to change the settings | `interview/config.md`: time, level, stack, tool, voice, narration, skipped skills |
| `narrate` | Any time you need words for a decision, a mistake, or a wrap-up | Prompts to answer aloud |

Invoke them as `/interview-skills:<skill>`, for example `/interview-skills:prep`.

### Each step makes you decide

The AI drafts, researches and builds. In every step there is a point where **you** must cut, push back or add something of your own before the step is done. That is the part the interviewer is watching, and no setting removes it.

### Parallel by design

`plan` splits the work into units that don't share files and defines a shared contract (routes, data shapes, names) first. `implement` writes the contract to files, then dispatches one agent per unit. If the boundaries aren't clean, the plan says so and uses one agent.

### `test` is a meta-skill

It doesn't ship a dashboard. It instructs Claude to **build** integration tests in your project, in your stack, and always to build alongside them:

- an **observability dashboard**: latest results, run history, failures, and a live app-log tail;
- **click-triggered runs**: run all, run one, and a "hammer" button that repeats runs with a tally;
- structured logs in a gitignored `logs/` folder, so results can be read as evidence.

It is only done when it shows evidence: the dashboard loads, a click produces a logged result, and a hammer run completes.

### `configure` is a meta-skill

It asks a few questions and writes `interview/config.md`, which every other skill reads. It sets how much time you have (shared out across the four steps), your level, your stack and AI tool, whether you use voice, how much narration you want, and which skills to skip. In a real interview, the interviewer's instructions win over any setting. The settings and rules are in `skills/configure/references/settings.md`. `configure` is optional: without a config file every skill uses its defaults.

## A typical flow

`configure` → `prep` → `plan` → `implement` → `test`, with `narrate` at any point.

Default budget for a 60-minute build: prep 9 minutes, plan 9, implement 24, test 18. If a step runs over, cut scope in the next one; don't skip its artifact.

## Install

```
/plugin marketplace add eukota/claude-marketplace
/plugin install interview-skills@eukota-claude-marketplace
```

## Practice

Try the skills on a practice question before an interview. The full run is about 60 minutes: run `prep` first, then work through the four steps and finish with `narrate`.

## Design notes

- **Brief on purpose.** Each skill fits on a page and ends with a clear "done when".
- **Instructions only.** The plugin contains no runtime code, so it adapts to whatever stack you're using.
- **Evidence over claims.** Skills ask for output on screen, not statements that something works.

## Status

Version 0.3.0, first draft. Skill wording will be tuned after practice runs.
