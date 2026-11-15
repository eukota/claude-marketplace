# interview-skills

Brief interview skills for candidates in AI-assisted technical interviews.

In these interviews you share your screen, work with an AI coding tool, and are judged on how you use it as much as on what you build. This plugin gives you a small set of short skills, one per stage of the interview. Run them on screen and the interviewer sees a deliberate method instead of improvising: you asked good questions, planned before coding, ran many agents at once against a shared contract, made the system observable, and proved it works.

## Purpose

- Make good habits quick enough to use under interview time.
- Make foresight **visible**. Every skill leaves a short, readable file in `interview/` in your project.
- Keep **you** doing the thinking. Each skill makes the candidate decide, push back or add something of their own. The AI supports; it doesn't take over. A skill that did the work for you would defeat its purpose.

## The five steps

The interview is five steps. Each leaves a short file in `interview/` that the interviewer can see.

| Step | Skill | What happens | Artifacts |
| --- | --- | --- | --- |
| 1 | `prep` | A background agent gathers best practices while you build the prompt with the interviewer, then you trim the research to the scope you'll build | `prompt.md`, `best_practices.md` |
| 2 | `plan` | A plan that follows both, with a plain-language summary, a diagram, a shared contract and a work split for many parallel agents, including a dashboard unit and a clickable-tests unit | `plan.md` |
| 3 | `implement` | The contract first, then many agents at once: the system, an observability dashboard and the clickable tests. You integrate, then review the code and explain it in your own words | `implement.md` |
| 4 | `test` | Run the clickable tests while watching the system operate on the dashboard, add your own edge cases, and iterate on what breaks | `test.md`, `logs/` |
| 5 | `commentary` | A short spoken close on what you would do if this were built for real, tied to what you chose not to do | `commentary.md` |

Three more skills work alongside them:

| Skill | Use it when | Leaves behind |
| --- | --- | --- |
| `configure` | Before you start, or when you want to change the settings | `interview/config.md`: time, level, stack, tool, voice, narration, skipped skills |
| `observability` | You plan or dispatch the dashboard agent | The dispatch phrase and what the dashboard must show |
| `narrate` | Any time you need words for a decision or a mistake | Prompts to answer aloud |

Invoke them as `/interview-skills:<skill>`, for example `/interview-skills:prep`.

### Reviewing is where you show understanding

The build with parallel agents is fast. Reading the output takes time, and that time is the point: you explain the code in your own words, trace a request end to end, and name what you trust least. The AI can explain anything you don't follow, but you have to say it back.

### Each step makes you decide

The AI drafts, researches and builds. In every step there is a point where **you** must cut, push back or add something of your own before the step is done. That is the part the interviewer is watching, and no setting removes it.

### Many agents at once

`plan` splits the work into units that don't share files and defines a shared contract first (routes, data shapes, what the system reports about itself, and the test scenarios). `implement` writes the contract to files and then dispatches one agent per unit at once. The dispatch is part of the demonstration: orchestrating many agents while still tracking and integrating each one.

### Observability, planned then rendered

The candidate names observability while planning ("add an observability dashboard to the plan that shows the system operating") and then renders it: a parallel agent builds a dashboard that shows requests and events as they happen. The interviewer sees foresight, the vocabulary and the result on screen. `observability` holds the dispatch phrase and what the dashboard must deliver. It doesn't ship code; Claude builds it fresh in your stack.

### `test` is clickable and watchable

The tests are a few meaningful demonstrations you click and watch on the dashboard, each one tied to the plan's riskiest parts. They run against the real running system, reset the data, and log a result. The step ends only with evidence: a click, activity on the dashboard, and a logged result.

### `commentary` is the close

Say what you would do for real, such as looping reviewer and fixer agents to tighten file size and security, and tie each item to a deliberate cut. You say it and don't do it.

### `configure` is a meta-skill

It asks a few questions and writes `interview/config.md`, which every other skill reads. It sets how much time you have (shared out across the five steps), your level, your stack and AI tool, whether you use voice, how much narration you want, and which skills to skip. In a real interview, the interviewer's instructions win over any setting. The settings and rules are in `skills/configure/references/settings.md`. `configure` is optional: without a config file every skill uses its defaults.

## A typical flow

`configure` → `prep` → `plan` → `implement` (with `observability`) → `test` → `commentary`, with `narrate` at any point.

Default budget for a 60-minute build: prep 9 minutes, plan 9, implement 18, test 18, commentary 6. Within `implement`, the build is often about 5 minutes and the rest is reviewing the code, where you show you understand it. If a step runs over, cut scope in the next one; don't skip its artifact.

## Install

```
/plugin marketplace add eukota/claude-marketplace
/plugin install interview-skills@eukota-claude-marketplace
```

## Practice

Try the skills on a practice question before an interview. The full run is about 60 minutes: run `prep` first, then work through the steps and finish with `commentary`.

## Design notes

- **Brief on purpose.** Each skill fits on a page and ends with a clear "done when".
- **Instructions only.** The plugin contains no runtime code, so it adapts to whatever stack you're using.
- **Evidence over claims.** Skills ask for output on screen, not statements that something works.

## Status

Version 0.3.0, first draft. Skill wording will be tuned after practice runs.
