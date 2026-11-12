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
| `time` | minutes for the build segment | `60` | clarify, plan, verify, integration-tests |
| `level` | `entry`, `mid`, `senior` | `mid` | clarify, plan, direct, review |
| `stack` | free text: language and framework | whatever is already in the project | plan, direct, verify, integration-tests |
| `ai_tool` | free text | the tool in use | direct |
| `voice` | `yes`, `no` | `no` | narrate |
| `narration` | `short`, `full` | `full` | narrate |
| `skip` | comma-separated skill names, or `none` | `none` | all skills |

## Rules for every skill

- **Real interviews.** When `mode` is `real`, the interviewer's instructions win over any setting. If they conflict, follow the interviewer and say so.
- **Skipped skills.** If the skill being run is in `skip`, tell the candidate and ask whether to run it anyway. The candidate decides.
- **Unknown values.** Treat a value you don't recognise as the default, and say you did.
- **The thinking stays with the candidate.** No setting removes the parts where the candidate must decide, push back or add something of their own.
- **No secrets.** Don't write keys, tokens or personal data into the config file.
- **Evidence still required.** Settings change how much a skill does, not whether it shows evidence that something works.
