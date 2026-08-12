# pahf

> **Deprecated — superseded by [`small-brain`](../small-brain/).**
> This plugin calls scripts in `~/Development/small-brain-alpha/`, a checkout
> outside this marketplace, so it does not work on any other machine. Use
> `small-brain`, which ships its own scripts and references them through
> `${CLAUDE_PLUGIN_ROOT}`.

Personalized Agents from Human Feedback — PAHF loop for Small Brain.

Runs the three-step PAHF loop as Claude Code skills and rules, backed by a persistent SQLite memory store. No separate client — the loop is wired into Claude's behavior.

## What It Does

Every significant decision follows:
1. **Clarify** — state understanding and surface assumptions before acting
2. **Ground** — check memory for relevant principles or past decisions
3. **Act** — proceed from the grounding
4. **Correct** — when the user corrects output, extract and store the principle

Periodically:
5. **Compress** — extract principles from decisions; extract meta-principles from conflicts

## Primitives

### Skills

- `pahf-clarify` — pre-action clarification step
- `pahf-ground` — ground in memory hierarchy before deciding
- `pahf-correct` — post-action correction; extract and store principles
- `pahf-compress` — run compression loop to promote decisions → principles → meta-principles

### Rules

- `pahf-loop` — behavioral rules for when to run each step automatically

### Hooks

- `session-start.sh` — load active principles into session context at startup

## Memory Backend

Requires `small-brain-alpha` at `~/Development/small-brain-alpha/`.
Memory is stored at `~/.small-brain/memory.db`.

Scripts called by skills/hooks:
- `scripts/memory_query.py` — read from memory hierarchy
- `scripts/memory_write.py` — write decisions and corrections
- `scripts/compress.py` — run compression loop

## Usage

Install the plugin, then use the skills explicitly or let the rules trigger them automatically.

To manually run a step:
- `/pahf-clarify` — before a decision
- `/pahf-ground --domain <domain> --context "<situation>"` — check memory
- `/pahf-correct` — after a correction
- `/pahf-compress` — extract principles from recent decisions
