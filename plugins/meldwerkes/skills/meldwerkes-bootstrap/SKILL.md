---
name: meldwerkes-bootstrap
description: Pretrain a mind from existing Claude Code chat history — extracts durable preferences from past corrections and directives, writes them with their original timestamps, and reports the principles found with decay-adjusted confidence. Use when starting a new mind and wanting it seeded from prior work rather than empty.
---

# Bootstrap a Mind from Chat History

Starting empty means re-teaching preferences already stated many times. This
reads existing transcripts under `~/.claude/projects/`, extracts durable
preferences, and writes them into a brain with the timestamps they were
actually expressed — so temporal decay is meaningful rather than uniform.

## Before running

**Always bootstrap into a fresh brain, never an established one.** The import
is a bulk write of inferred preferences; it should be reviewable and
discardable on its own. Merging into a primary brain before review risks
polluting real accumulated signal with misclassifications.

Check what exists:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/brain.py list
```

If there is no suitable target, create one:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/brain.py create \
  --name "Bootstrap import" --domain general \
  --description "Seeded from chat history; review before trusting"
```

## Process

### 1. Always dry-run first

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/bootstrap.py \
  --brain-id <brain-id> --dry-run
```

This classifies and reports without writing. Show the user the report and let
them judge quality before anything is committed to the store.

If too few principles surface, suggest `--min-confidence 0.3` (default 0.5).
If too many low-quality ones appear, suggest raising it.

### 2. Bound the run if history is large

- `--since YYYY-MM-DD` — skip old transcripts whose preferences may be stale
- `--limit N` — cap exchanges examined

Classification costs one model call per 20 exchanges, so a few hundred turns
is a handful of calls, not hundreds.

### 3. Write, once the dry run looks right

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/bootstrap.py --brain-id <brain-id>
```

### 4. Present the report

The script prints it. Read it back to the user rather than just echoing —
specifically call out:

- **Principles whose effective confidence dropped well below stated
  confidence.** Those are old, and may reflect preferences since changed.
- **The correction/directive/answer mix.** Corrections are the strongest
  signal; a run dominated by `answer` is weaker and worth treating with more
  suspicion.
- **Anything that looks like a project fact rather than a preference.** That
  is the known hard case, and the user is the only one who can tell.

### 5. Offer next steps

- `/pahf-compress` to derive meta-principles from the imported decisions
- `/meldwerkes-report` to review the brain
- Discard and re-run with different thresholds if quality is poor

## Temporal decay

Principle confidence decays exponentially with age. The half-life is
`confidence_half_life_days` in settings (default 180 — confidence halves every
six months). A principle stated confidently two years ago carries little weight
today unless it has been reinforced since.

Set `0` to disable decay entirely:

```python
import json, pathlib
p = pathlib.Path.home() / '.small-brain/settings.json'
s = json.loads(p.read_text()) if p.exists() else {}
s['confidence_half_life_days'] = 180
p.write_text(json.dumps(s, indent=2))
```

## Honest caveats to raise with the user

**Selection bias.** Transcripts over-represent friction — they capture where
things went wrong far more than where they went right. A mind built only from
them skews pessimistic about its owner's own process.

**Fact versus principle.** "Use Postgres here" and "I prefer boring
infrastructure" look identical in text. The classifier is instructed to be
strict, but it will get some wrong in both directions.

**Drift.** Old preferences may have been superseded. Decay handles this
statistically; it does not handle a reversal, where the old principle is not
merely weaker but wrong.

Do not oversell the result. It is a starting point that saves re-teaching, not
a finished model.
