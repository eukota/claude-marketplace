# interview-skills

A practice and teaching tool for learning how to work with AI in AI-assisted technical interviews.

> **This is for practice, not for the interview itself.** You use it on practice questions, before the interview, to learn a method. You are not meant to run it, or rely on it, in a real interview. In the real interview you do the steps yourself, from what you learned, with whatever tool the interviewer provides. Nothing in this plugin requires or assumes that it is available on the day.

In AI-assisted interviews you share your screen, work with an AI coding tool, and are judged on how you use it as much as on what you build. This plugin walks you through one practice run, one skill per stage: ask good questions, plan before coding, run many agents at once against a shared contract, make the system observable, and prove it works. By the end you should be able to do each step without the plugin and explain why you do it.

Terms: in these skills, "the candidate" is you, the learner, and "the interviewer" is whoever plays that role in practice: your instructor, a partner, or the AI.

## Purpose

- Teach a repeatable method for each stage of an AI-assisted interview, so the habits are quick enough to use under interview time without the plugin.
- Make your thinking **visible** to you and your instructor. Every skill leaves a short, readable file in `interview/` in your project, so you can review what you did and why.
- Keep **you** doing the thinking. Each skill makes the learner decide, push back or add something of their own. The AI supports; it doesn't take over. A skill that did the work for you would defeat its purpose.
- Teach the ideas, not a script. The example phrasings in `narrate` and `observability` are prompts for practice. In an interview, use your own words.

## The five steps

A practice run is five steps. Each leaves a short file in `interview/` for you and your instructor to review.

| Step | Skill | What happens | Artifacts |
| --- | --- | --- | --- |
| 1 | `prep` | A background agent gathers best practices while you build the prompt with the interviewer, then you trim the research to the scope you'll build | `prompt.md`, `best_practices.md` |
| 2 | `plan` | A plan that follows both, with a plain-language summary, a diagram, a shared contract and a work split for many parallel agents, including a dashboard unit and a clickable-tests unit | `plan.md` |
| 3 | `implement` | The contract first, then many agents at once: the system, an observability dashboard and the clickable tests. You integrate, then review the code and explain it in your own words | `implement.md` |
| 4 | `test` | Run the clickable tests while watching the system operate on the dashboard, add your own edge cases, and iterate on what breaks | `test.md`, `logs/` |
| 5 | `commentary` | A short spoken close on what you would do if this were built for real, tied to what you chose not to do | `commentary.md` |

Four more skills work alongside them:

| Skill | Use it when | Leaves behind |
| --- | --- | --- |
| `practice` | You say "I'm going to practice an interview question". The coach: sets up a clean run, picks the question and the interviewer, then walks you through the five steps and asks what you decided in each | `interview/practice.md`: the question, time per step against budget, your decision per step, your reflection |
| `configure` | Before you start, or when you want to change the settings | `interview/config.md`: time, level, stack, tool, voice, narration, skipped skills |
| `observability` | You plan or dispatch the dashboard agent | The dispatch phrase and what the dashboard must show |
| `narrate` | Any time you need words for a decision or a mistake | Prompts to answer aloud |

Start with `practice` and it walks you through the rest. You can also invoke any skill directly as `/interview-skills:<skill>`, for example `/interview-skills:prep`.

### Reviewing is where you show understanding

The build with parallel agents is fast. Reading the output takes time, and that time is the point: you explain the code in your own words, trace a request end to end, and name what you trust least. The AI can explain anything you don't follow, but you have to say it back.

### Each step makes you decide

The AI drafts, researches and builds. In every step there is a point where **you** must cut, push back or add something of your own before the step is done. That is the part that builds your own skill, and no setting removes it. In a real interview it is also the part the interviewer is watching for.

### Many agents at once

`plan` splits the work into units that don't share files and defines a shared contract first (routes, data shapes, what the system reports about itself, and the test scenarios). `implement` writes the contract to files and then dispatches one agent per unit at once. The dispatch is part of the demonstration: orchestrating many agents while still tracking and integrating each one.

### Observability, planned then rendered

The candidate names observability while planning ("add an observability dashboard to the plan that shows the system operating") and then renders it: a parallel agent builds a dashboard that shows requests and events as they happen. You practice the foresight, the vocabulary and the result on screen. `observability` holds the dispatch phrase and what the dashboard must deliver. It doesn't ship code; Claude builds it fresh in your stack.

### `test` is clickable and watchable

The tests are a few meaningful demonstrations you click and watch on the dashboard, each one tied to the plan's riskiest parts. They run against the real running system, reset the data, and log a result. The step ends only with evidence: a click, activity on the dashboard, and a logged result.

### `commentary` is the close

Say what you would do for real, such as looping reviewer and fixer agents to tighten file size and security, and tie each item to a deliberate cut. You say it and don't do it.

### `configure` is a meta-skill

It asks a few questions and writes `interview/config.md`, which every other skill reads. It sets how much time you have (shared out across the five steps), your level, your stack and AI tool, whether you use voice, how much narration you want, and which skills to skip. The settings and rules are in `skills/configure/references/settings.md`. `configure` is optional: without a config file every skill uses its defaults.

## A typical flow

`practice` runs `configure` → `prep` → `plan` → `implement` (with `observability`) → `test` → `commentary`, with `narrate` at any point.

Default budget for a 60-minute build: prep 9 minutes, plan 9, implement 18, test 18, commentary 6. Within `implement`, the build is often about 5 minutes and the rest is reviewing the code, where you show you understand it. If a step runs over, cut scope in the next one; don't skip its artifact.

## Install

```
/plugin marketplace add eukota/claude-marketplace
/plugin install interview-skills@eukota-claude-marketplace
```

## Practice

Try the skills on a practice question well before an interview. Say "I'm going to practice an interview question" in a fresh session in an empty folder, and `practice` coaches you through the full run, about 60 minutes. Then do another practice question **without** the plugin, from memory, and compare what you did to the files from the first run. The goal is that you no longer need it.

## Design notes

- **Brief on purpose.** Each skill fits on a page and ends with a clear "done when".
- **Instructions only.** The plugin contains no runtime code, so it adapts to whatever stack you're using.
- **Evidence over claims.** Skills ask for output on screen, not statements that something works.

## Status

Version 0.4.0, first draft. Skill wording will be tuned after practice runs.
