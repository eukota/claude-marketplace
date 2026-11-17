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
| `/meldwerkes-bootstrap` | Survey chat history, propose minds, then create and import |
| `/meldwerkes-review` | Review principles; reinforce, weaken, revise, retire |
| `/meldwerkes-calibrate` | Test how well the mind predicts you; r, calibration, per-domain |
| `/meldwerkes-capture` | Turn learning on/off; check whether it is recording |
| `/meldwerkes-auto` | Automatic learning: turn on/off, status, review proposed principles, undo a run |
| `/meldwerkes-history` | Checkpoints, retract a time range, restore |
| `/meldwerkes-report` | Status report: brains, decisions, principles, stats |
| `/pahf-compress` | Run distillation loop; detect brain split signals |
| `/meldwerkes-export` | Export a brain to portable JSON |
| `/meldwerkes-import` | Import a brain (provisional or full trust) |

## Automatic learning

Capture records every prompt, but classifying prompts into decisions and distilling
them into principles used to be manual. With automatic learning on, a background
run does both:

- A `SessionEnd` hook (and a `SessionStart` fallback for sessions that died) starts
  `scripts/auto.py` detached, at most every 6 hours and only once 20 or more new
  prompts are waiting. The hook returns in milliseconds and never fails a turn.
- The run classifies up to 200 prompts (using your Claude subscription via
  `claude -p`; no API key), writes decisions and corrections, and distils
  principles when a mind has 5 or more new decisions, or 14 days have passed.
- **Propose mode (default once enabled):** new principles wait in a queue; nothing
  changes what Claude is told until you accept it with `/meldwerkes-auto`.
  **Apply mode** saves them directly. Both take a checkpoint first.
- Secret-looking lines are removed before any model call and are never stored or
  logged. The loop's own model calls are not captured back into the store.

It is **off until you run `/meldwerkes-auto`** (`auto.py enable`), because it
sends your prompts, scrubbed, to a model. Where to look and how to undo:

| What | Where |
|---|---|
| Run log (one line per run, no prompt text) | `~/.small-brain/logs/auto-latest.log` |
| Status: backlog, last run, proposals, weekly correction rate | `auto.py status` |
| Undo one run | `history.py retract --run-id <id>` |
| Roll the whole store back | `/meldwerkes-history` |

### Does the multi-mind structure earn its keep?

The design rests on the Fourier analogy: a decision function is better approximated
by several domain minds plus a learned orchestrator than by one pooled mind. The
analogy is a heuristic, so the plugin tests it. Once enough labelled exchanges
exist, a held-out set is fixed once (`heldout.json`, never regenerated, drawn only
from exchanges no principle was distilled from). `eval_fourier.py run` then predicts
whether you would object to an assistant action using a pooled mind versus the live
minds. Multi-mind is declared the winner only if it beats pooled by more than the
run-to-run noise; otherwise the verdict is `tie: keep the simpler structure`.
The ground truth is a proxy (see the script), so read the comparison, not the
absolute correlation. The second measure is the weekly correction rate, shown in
`auto.py status` and `/meldwerkes-report`.

## Settings

Two toggles (configured during setup or via `/meldwerkes-setup`):

- **Principle auto-answer** — when `on`, principles are applied silently without confirming with you first.
- **Conflict resolution** — when `auto`, orchestrator resolves conflicts via principles; when `manual`, always asks you.

Hard floor: if principles can't resolve a conflict, it always escalates to you regardless of settings.

## Control

Learning is on by default and can be turned off at any time — `/meldwerkes-capture`.
The guard lives in the storage layer, so a paused capture cannot be bypassed.

Every mutating operation snapshots the store first, so learning can be rolled
back: `/meldwerkes-history` retracts a time range or restores any checkpoint.
Restore checkpoints the current state before overwriting, so undo is itself
undoable.

## Temporal decay

Principle confidence decays exponentially with age — `confidence_half_life_days`
in settings, default 180. A principle halves in weight every six months unless
reaffirmed.

Decay only forgets; `/meldwerkes-review` is the other half. Confirming a
principle resets its clock, so what stays true stays strong and what goes
unexamined fades. Set the half-life to `0` to disable decay entirely.

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

---

Design thinking, future directions, and open questions live with the project
docs rather than here: [eukota/ai-projects → projects/meldwerkes](https://github.com/eukota/ai-projects/tree/main/projects/meldwerkes).
