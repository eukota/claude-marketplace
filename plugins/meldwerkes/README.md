# meldwerkes

Multi-agent cognitive architecture that builds a personalized decision model through PAHF loops, distillation, and multi-brain orchestration.

## What It Does

Runs three loops passively as you work:

1. **PAHF loop** (per action) — clarify → ground in memory → act → correct. Input is passive: gathered from normal conversation as you answer questions.
2. **Distillation loop** (periodic) — compresses decisions into principles, principles into meta-principles. Detects conflict clusters and asks if a second brain should be split off.
3. **Multi-brain loop** (when 2+ brains exist) — brains vote blind, orchestrator resolves via principles, escalates to you when it can't.

## Getting Started

```
/meldwerkes-setup
```

Creates your first brain, configures settings, verifies memory store.

## Skills

| Skill | Purpose |
|---|---|
| `/meldwerkes-setup` | Create a brain, configure settings |
| `/meldwerkes-report` | Status report: brains, decisions, principles, stats |
| `/pahf-compress` | Run distillation loop; detect brain split signals |
| `/meldwerkes-export` | Export a brain to portable JSON |
| `/meldwerkes-import` | Import a brain (provisional or full trust) |

## Settings

Two toggles (configured during setup or via `/meldwerkes-setup`):

- **Principle auto-answer** — when `on`, principles are applied silently without confirming with you first.
- **Conflict resolution** — when `auto`, orchestrator resolves conflicts via principles; when `manual`, always asks you.

Hard floor: if principles can't resolve a conflict, it always escalates to you regardless of settings.

## Memory

Stored at `~/.small-brain/memory.db` (SQLite).
Settings at `~/.small-brain/settings.json`.

Four-tier hierarchy per brain:
1. Raw corrections
2. Decisions (confirmed/corrected/pending)
3. Principles (with confidence scores)
4. Meta-principles (conflict resolution rules)

## Export / Import

Brains are portable. Export a brain to JSON, import it on another machine or share it. Imported brains default to provisional trust (70% confidence) until verified through use.

## Requirements

- Python 3.9+
- `anthropic` SDK (for distillation loop only): `pip install anthropic`
- All other features use stdlib only
