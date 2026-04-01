# plugin-builder

Tools for building Claude marketplace plugins.

## What Should I Build?

```mermaid
flowchart TD
    Start([What do you want to build?]) --> External

    External{Needs access to an\nexternal system or API?}
    External -- Yes --> MCP([MCP Server\nConnect Claude to external tools,\nAPIs, or data sources])
    External -- No --> AlwaysOn

    AlwaysOn{Should it be\nalways on?}
    AlwaysOn -- Yes --> Event
    AlwaysOn -- No --> Autonomous

    Event{Triggered by a\nClaude Code event?}
    Event -- Yes --> Hook([Hook\nFire shell commands on\nClaude Code events])
    Event -- No --> Rule([Rule\nEnforce policies and\nbehavioral constraints])

    Autonomous{Complex autonomous\nmulti-step task?}
    Autonomous -- Yes --> Agent([Agent\nSpecialized subagent for\nindependent focused tasks])
    Autonomous -- No --> Reusable

    Reusable{Reusable process or\ndomain expertise?}
    Reusable -- Yes --> Skill([Skill\nPackaged workflow or\nbest-practice guidance])
    Reusable -- No --> Command([Command\nQuick slash command\nshortcut for users])
```

Not sure? Use the `choose-primitive` skill — it will ask you a few questions and guide you to the right answer.

## Skills

### `choose-primitive`

Guides you to the right Claude primitive for what you want to build. Asks a few questions about your goal and recommends between: skill, command, rule, hook, agent, or MCP server.

**Use when:** You know you want to build something but aren't sure which primitive fits.
