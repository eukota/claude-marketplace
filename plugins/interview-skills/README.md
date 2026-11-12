# interview-skills

Brief interview skills for candidates in AI-assisted technical interviews.

In these interviews you share your screen, work with an AI coding tool, and are judged on how you use it as much as on what you build. This plugin gives you a small set of short skills, one per stage of the interview. Run them on screen and the interviewer sees a deliberate method instead of improvising: you asked good questions, planned before coding, directed the AI with real data, reviewed what it wrote, and proved it works.

## Purpose

- Make good habits quick enough to use under interview time.
- Make foresight **visible**. Every skill leaves a short, readable file in `interview/` in your project.
- Keep **you** doing the thinking. Each skill makes the candidate decide, push back or add something of their own. The AI supports; it doesn't take over. A skill that did the work for you would defeat its purpose.

## Skills

| Skill | Use it when | Leaves behind |
| --- | --- | --- |
| `clarify` | You've just been given the prompt | `interview/01-clarify.md`: questions, assumptions, scope |
| `plan` | Scope is set, before any code | `interview/02-plan.md`: components, build order, not-doing list |
| `direct` | You're about to ask the AI to write code | `interview/03-brief.md`: the brief, with real data shapes |
| `review` | The AI has just generated code | `interview/04-review.md`: what you checked and found |
| `verify` | You want quick evidence the parts work | `interview/05-verify.md`: tests run, edge cases added, gaps |
| `integration-tests` | You want to show the whole system working | Tests, an observability dashboard, click-to-run buttons, `interview/06-integration.md` |
| `narrate` | You need words for a decision, a mistake or a wrap-up | Prompts to answer aloud |

Invoke them as `/interview-skills:<skill>`, for example `/interview-skills:clarify`.

### `integration-tests` is a meta-skill

It doesn't ship a dashboard. It instructs Claude to **build** integration tests in your project, in your stack, and always to build alongside them:

- an **observability dashboard**: latest results, run history, failures, and a live app-log tail;
- **click-triggered runs**: run all, run one, and a "hammer" button that repeats runs with a tally;
- structured logs in a gitignored `logs/` folder, so results can be read as evidence.

It is only done when it shows evidence: the dashboard loads, a click produces a logged result, and a hammer run completes.

## A typical flow

`clarify` → `plan` → `direct` → *(AI builds)* → `review` → `verify` → `integration-tests` → `narrate`

`narrate` can be used at any step. Skip steps freely; each skill stands on its own.

## Install

```
/plugin marketplace add eukota/claude-marketplace
/plugin install interview-skills@eukota-claude-marketplace
```

## Practice

Try the skills on a practice question before an interview. The full run is about 60 minutes: spend the first 5 to 10 on `clarify`, build the smallest working version, and finish with `integration-tests` and `narrate`.

## Design notes

- **Brief on purpose.** Each skill fits on a page and ends with a clear "done when".
- **Instructions only.** The plugin contains no runtime code, so it adapts to whatever stack you're using.
- **Evidence over claims.** Skills ask for output on screen, not statements that something works.

## Status

Version 0.1.0, first draft. Skill wording will be tuned after practice runs.
