---
name: meldwerkes-review
description: Review accumulated principles with the user and apply reinforcement — confirm what is still true (resetting temporal decay), weaken what is partly wrong, reword what is clumsily stated, retire what was never right. Use when the user asks to review, prune, reaffirm, or check what the model believes about them.
---

# Review and Reinforce Principles

Temporal decay only forgets. This is the other half: the user's chance to say
"still true," which resets a principle's clock, or "not any more," which does
not.

Run it periodically, or whenever the user wants to see what the model currently
believes about them.

## Process

### 1. Show what needs review

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/review.py list --brain-id <brain-id>
```

Omit `--brain-id` to review across all minds.

Output is sorted by the **gap between stated and current confidence** — the
principles most eroded by time come first, because those are the ones where a
human decision actually changes something.

### 2. Walk them with the user, one at a time

Do not dump the whole list and ask for a verdict on all of it. Take the stale
ones in order and, for each, show the principle, its age, and its stated versus
current confidence. Then ask which of four applies:

| User says | Action | Effect |
|---|---|---|
| Still true | `reinforce` | Clock resets to now, confidence +0.05 |
| Partly true / less than it was | `weaken` | Confidence −0.25, kept with history intact |
| Right idea, wrong wording | `revise --text "..."` | Text replaced, id and supporting decisions preserved |
| Never true / no longer true | `retire` | Deleted |

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/review.py reinforce --principle-id <id>
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/review.py weaken    --principle-id <id>
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/review.py revise    --principle-id <id> --text "..."
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/review.py retire    --principle-id <id>
```

An 8-character id prefix works — that is what `list` prints.

### 3. Prefer weaken over retire

Retiring deletes. Weakening keeps the principle and its provenance while
recording that it holds less than it did. A preference someone has drifted away
from is different from one that was always wrong, and only the second deserves
deletion. When the user is ambivalent, weaken.

### 4. Summarize

Report what changed: how many reinforced, weakened, revised, retired. If a
cluster of related principles all weakened together, say so — that is a signal
their thinking has shifted in a domain, which is more interesting than any
single principle and worth naming.

## Judgment while reviewing

**Do not lead the witness.** Present the principle as recorded and let the user
judge. Asking "this still holds, right?" produces agreement rather than
information, and agreement that was manufactured is worse than no signal — it
resets the decay clock on something untrue.

**Watch for principles that were project facts.** Bootstrap imports and
imperfect extraction both produce these. "Use Postgres" is not a principle. If
one appears, suggest retiring it.

**Old does not mean wrong.** A principle can be two years old and completely
current. Decay is a prompt to *ask*, not evidence of staleness. Say so if the
user seems to be retiring things merely for being old.

**Reinforcement is a real edit.** It resets the clock, so a principle
reinforced carelessly will outlive one that is true. Take the same care
confirming as retiring.
