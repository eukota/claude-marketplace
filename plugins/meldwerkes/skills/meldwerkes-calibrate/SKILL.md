---
name: meldwerkes-calibrate
description: Test how well a mind predicts its owner — proposes questions, predicts each answer from existing principles before the user responds, then scores agreement with correlation, calibration error, and a per-domain breakdown. Use when the user wants to check whether the model actually knows them, or to seed mind × domain weights.
---

# Calibration Run

Ask the user a set of questions, predict each answer *before* they give it, then
score the two against each other. This is the measurement instrument: it says
whether the accumulated principles actually predict their owner, and where they
do not.

## The rule that makes this valid

**Commit every prediction to the file before showing the user the question.**

If you see their answer first, your "prediction" is a rationalization and the
entire run is worthless. Write predictions down, then ask.

## Process

### 1. Read the existing principles

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/review.py list --brain-id <brain-id>
```

### 2. Compose 20–30 questions across three kinds

Aim for ~60% validation, ~25% coverage, ~15% conflict. Below about 15
validation questions the correlation is too noisy to act on.

**validation** — a principle makes a confident prediction. These are scored.

**coverage** — no principle applies. Deliberately probe domains the mind has
never seen its owner decide in. Not scored; these map the blind spots, which
is the self-model gap.

**conflict** — two principles predict differently. Not scored; a disagreement
is a finding, possibly meaning the domain should split into separate minds.

Every question must be answerable on a **1–7 scale**, because correlation is
only meaningful on continuous data. Not "would you refactor this?" but "how
strongly would you refactor before shipping — 1 ship as-is, 7 refactor fully?"

Anchor both ends explicitly, or the user and the model are answering different
questions.

### 3. Write predictions first

```json
[{"kind": "validation", "domain": "code-review",
  "question": "How strongly would you...? (1 = ..., 7 = ...)",
  "predicted": 5, "confidence": 0.8, "principle_id": "abc123", "actual": null}]
```

`confidence` should be the principle's own effective (decayed) confidence, not
your impression. `domain` drives the per-domain breakdown, so keep the
vocabulary consistent across runs.

### 4. Ask the user

A few at a time, conversationally. Do not show your predictions. Do not hint at
them by how you phrase the question — a leading question tests your phrasing,
not the mind.

Fill in each `actual` as answers arrive.

### 5. Score and present

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/calibrate.py score --input <file>.json
```

Read the report back with interpretation, not just numbers:

- **r** — agreement on validation questions. Above ~0.7 is strong, 0.4–0.7
  moderate, below 0.4 means the principles are not predicting.
- **MAE** — average miss in scale points. More interpretable than r; report both.
- **ECE** — whether confidence is honest. A 0.9-confidence principle that is
  right 60% of the time is worse than a 0.6 one that is right 60%, because it
  will be trusted. This is the number r cannot give you.
- **Per-domain** — where the mind knows its owner and where it does not. These
  are candidate weights for the mind × domain matrix.
- **Coverage gaps** — domains worth capturing deliberately.
- **Conflicts** — possible split points.

### 6. Act on the result

- Domains with low r → the principles there are wrong or too general. Offer
  `/meldwerkes-review` to weaken or revise them.
- High ECE → confidence values are not meaningful yet; say so plainly rather
  than letting them be trusted.
- Coverage gaps → suggest working in those domains with capture on.

## Honest framing

**Validation questions derive from the principles being tested**, so r is
optimistic — it measures internal consistency more than predictive power. Say
this when reporting. A single run's r is a weak claim; **r falling across
repeated runs is the real signal**, and r rising as principles accumulate is
the thing worth celebrating.

Do not present a first run as a score of how well the model knows them. Present
it as a baseline.
