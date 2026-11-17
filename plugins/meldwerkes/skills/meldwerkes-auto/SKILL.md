---
name: meldwerkes-auto
description: Turn Meldwerkes automatic learning on or off, see what it has learned, and review the principles it proposes. Use when the user wants Meldwerkes to learn without running commands, asks whether it is learning, wants to review or accept proposed principles, or wants to undo an automatic run.
---

# Automatic Learning

Meldwerkes records every prompt you type. With automatic learning on, a background
run turns those prompts into decisions and queues distilled principles for your
review. It is **off until you turn it on**, because it sends your prompts (with
secret-looking lines removed) to a model.

## Status

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/auto.py status
```

Report it plainly: mode, whether capture is on, how many prompts are waiting,
the last run, and how many proposals await review.

## Turn on / off

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/auto.py enable            # propose: principles wait for review (default)
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/auto.py enable --mode apply   # principles take effect immediately
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/auto.py disable
```

Recommend `propose`. Move to `apply` only after the proposals you accepted have
been mostly right. Both modes checkpoint before every run.

## First run: look before you drain

If a backlog has built up, preview one batch first. It writes nothing:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/auto.py run --dry-run --auth subscription
```

Show the user the batch estimate and the kinds histogram, and ask whether the
classification looks sane before the first real run. Each real run handles at
most 200 prompts, oldest first, so a large backlog drains over several runs.

## Review proposals

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/review.py proposals list
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/review.py proposals accept --id <prefix>
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/review.py proposals reject --id <prefix>
```

Read each proposal to the user and let them decide. Never accept with `--all`
unless they ask.

## Undo a run

Run ids are in `~/.small-brain/logs/auto-latest.log`.

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/history.py retract --run-id <id>
```

This removes that run's decisions, exchanges and proposals. Principles already
accepted from it stay until reviewed with `/meldwerkes-review`. To roll the whole
store back instead, use `/meldwerkes-history`.

## Test the multi-mind thesis

Once the loop has recorded enough labelled exchanges, a fixed held-out set is
created automatically (`~/.small-brain/heldout.json`, never regenerated). This
compares one pooled mind against the separate minds on that set:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/eval_fourier.py run --repeats 3 --auth subscription
```

It makes many model calls (up to 100 held-out items, two arms, three repeats), so
confirm with the user first. The verdict is `multi-mind` only when it beats pooled
by more than the run-to-run noise; otherwise `tie: keep the simpler structure`;
or `insufficient data` below 30 items or 5 corrections. Ground truth is a proxy
(a correction scores 7, a "none" scores 1), so trust the comparison, not the
absolute correlation. Results are in `~/.small-brain/logs/eval-latest.log` and
shown in `/meldwerkes-report`, along with the weekly correction rate.

## What it never does

- It never changes or retires a principle you have already accepted.
- It never runs while capture is off (`/meldwerkes-capture`).
- It never records its own model calls.
