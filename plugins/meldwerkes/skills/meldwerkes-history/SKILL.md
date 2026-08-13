---
name: meldwerkes-history
description: Checkpoint, retract, and restore the accumulated model — remove a time range of learning (a bad day, a paused period that got recorded anyway), list snapshots, and roll back to any of them. Use when the user wants to undo learning, remove recent decisions, or recover from a change that made the model worse.
---

# History and Retraction

A model you cannot roll back is one you can only accept. This is the undo.

Every mutating operation snapshots the store first, so nothing here is a
one-way door — including restore, which checkpoints the current state before
overwriting it.

## Show what exists

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/history.py status
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/history.py list
```

## Checkpoint before anything risky

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/history.py checkpoint --label "before bootstrap"
```

Bootstrap, compression, and retraction checkpoint automatically. Do it manually
before an experiment whose effect on the model is unknown.

## Retract a time range

**Always dry-run first**, and show the counts before removing anything:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/history.py retract --since 1d --dry-run
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/history.py retract --since 1d
```

`--since` accepts `YYYY-MM-DD`, or shorthand `1d` / `12h`. Add `--brain-id` to
confine it to one mind.

**Retraction cascades to derived principles.** Principles inferred during that
window go with it — keeping conclusions whose evidence has been removed is
worse than removing both. After retracting, suggest `/pahf-compress` to
re-derive from what remains.

## Restore

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/history.py restore --snapshot <name>
```

## Judgment

**Confirm the window before removing.** "The last day" is ambiguous near
midnight, and a retraction that takes more than intended is not obviously
recoverable to someone who does not know checkpoints exist. State the counts
and the cutoff timestamp, get agreement, then run it.

**Prefer retraction over starting over.** Users who think the model has gone
wrong often want to wipe it. Usually a bad window is the problem, and the rest
of the accumulated signal is fine and expensive to rebuild. Ask what changed
and when, and retract that instead.

**Always surface the checkpoint name after a retraction.** It is the undo, and
it is useless if the user does not know it exists.

**Point at `/meldwerkes-review` for single principles.** Retraction is a blunt
instrument for time ranges. One wrong principle should be weakened or retired,
not removed by deleting the day around it.
