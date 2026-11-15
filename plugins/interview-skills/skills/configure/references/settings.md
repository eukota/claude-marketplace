# Settings

The interview skills read `interview/config.md` in the candidate's project. If it is missing, use the defaults below and mention `/interview-skills:configure` once. Never block a skill because the file is missing.

## File format

Plain `key: value` lines, short enough to show on screen:

```
mode: practice
time: 60
level: mid
stack: Python, FastAPI
ai_tool: Claude Code
voice: no
narration: full
skip: none
```

## Settings

| Key | Values | Default | Used by |
| --- | --- | --- | --- |
| `mode` | `practice`, `real` | `practice` | all skills |
| `time` | minutes for the build segment | `60` | prep, plan, implement, test, commentary |
| `level` | `entry`, `mid`, `senior` | `mid` | prep, plan, implement, commentary |
| `stack` | free text: language and framework | whatever is already in the project | prep, plan, implement, observability, test |
| `ai_tool` | free text | the tool in use | implement |
| `voice` | `yes`, `no` | `no` | narrate |
| `narration` | `short`, `full` | `full` | narrate, commentary |
| `skip` | comma-separated skill names (`prep`, `plan`, `implement`, `observability`, `test`, `commentary`, `narrate`), or `none` | `none` | all skills |

## Time split

The five steps share `time`. Suggested split, used by each step skill to set its budget:

| Step | Share | Of 60 minutes |
| --- | --- | --- |
| `prep` | 15% | 9 |
| `plan` | 15% | 9 |
| `implement` | 30% | 18 |
| `test` | 30% | 18 |
| `commentary` | 10% | 6 |

`implement` is about 5 minutes of building and the rest review, because the candidate has to show they understand the output. `observability` is built inside `implement`; `narrate` has no budget. If a step runs over, cut scope in the next step instead of skipping its artifact.

## Rules for every skill

- **Real interviews.** When `mode` is `real`, the interviewer's instructions win over any setting. If they conflict, follow the interviewer and say so.
- **Skipped skills.** If the skill being run is in `skip`, tell the candidate and ask whether to run it anyway. The candidate decides.
- **Unknown values.** Treat a value you don't recognise as the default, and say you did.
- **The thinking stays with the candidate.** No setting removes the parts where the candidate must decide, push back or add something of their own.
- **No secrets.** Don't write keys, tokens or personal data into the config file.
- **Evidence still required.** Settings change how much a skill does, not whether it shows evidence that something works.
