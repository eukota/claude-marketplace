---
name: meldwerkes-bootstrap
description: Pretrain minds from existing Claude Code chat history in two phases — survey what domains are present and propose a set of minds, then create them and import. Use when starting from scratch and wanting the model seeded from prior work rather than empty.
---

# Bootstrap Minds from Chat History

Starting empty means re-teaching preferences already stated many times. This
reads existing transcripts, works out what domains of judgment are present,
proposes a set of minds, and — once the user approves — creates them.

Two phases, deliberately. **Bootstrap is the one moment the whole corpus is
visible at once**, which is a far better position for deciding how judgment
clusters than incremental observation ever gets. The plan file between the
phases is where that view becomes editable.

## Phase 1 — Survey

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/bootstrap.py survey --out bootstrap-plan.json
```

Creates nothing. It classifies each real user turn, assigns a **domain**, and
clusters the results into suggested minds.

Bound it if history is large: `--since YYYY-MM-DD`, `--limit N`. Adjust
`--min-confidence` (default 0.5) if too few or too many signals surface, and
`--min-signals` (default 15) to change how much evidence a domain needs before
it justifies its own mind.

**Auth is chosen before the first billable call.** The survey prints how many
model calls it will make, then asks which credentials to use:

| Choice | What it uses | What it costs |
|---|---|---|
| subscription | `claude -p`, the user's Claude Code login | subscription usage limits; no API key |
| api | `ANTHROPIC_API_KEY` via the anthropic SDK | billed to the API account, separately |

Pass `--auth subscription` or `--auth api` to skip the prompt. Left as `ask`
(the default) it prompts on a TTY and auto-detects when piped, preferring the
subscription. **Default to subscription unless the user says otherwise** — it
needs no key and no credit balance, and most users have it already.

**Present the survey to the user and stop.** Walk them through:

- Which domains appeared, and how much signal each has
- Which have enough to stand alone, and which are proposed for merging
- The sample principles per domain — these are the fastest way to judge whether
  the classifier understood their work

Ask whether the proposed split matches how they actually think. They will know
things the clustering cannot: that two domains are really one, that a domain is
a project rather than a kind of judgment, that a small cluster matters more
than its count suggests.

## Phase 2 — Edit the plan, then apply

The plan is JSON and meant to be edited. Offer to make these changes for them:

| To do this | Change |
|---|---|
| Skip a domain | `"create": false` |
| Rename a mind | `"brain_name": "..."` |
| Import into an existing mind | `"brain_id": "<id>"` |
| Move signals between minds | edit that signal's `"domain"` |
| Merge two domains | set both signals' `domain` to the same value |

Always dry-run before writing:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/bootstrap.py apply --plan bootstrap-plan.json --dry-run
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/bootstrap.py apply --plan bootstrap-plan.json
```

Apply checkpoints the store first and prints the undo command. Surface that to
the user — it is the difference between a reversible import and a leap.

## After applying

**No principles exist yet.** Bootstrap imports decisions and corrections;
principles come from compression. The apply output prints the exact command per
mind:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/compress.py --brain-id <id> --detect-split --auth subscription
```

Run it per mind, then `/meldwerkes-review` to look at what was derived, and
`/meldwerkes-calibrate` once there are principles worth testing.

## Judgment

**Do not apply a plan the user has not looked at.** The whole point of two
phases is that the structure is inspectable before it is built. Applying a
survey straight through defeats it.

**Domains are kinds of judgment, not projects.** If the survey produces domains
that are really repo names, the classifier keyed on the wrong thing — say so
and suggest merging them into judgment-shaped domains instead.

**Small domains are not automatically noise.** A domain with six signals may be
a real area the user rarely discusses in chat. Ask rather than assuming the
threshold was right.

## Caveats to state plainly

**Selection bias.** Transcripts over-represent friction — they capture where
things went wrong far more than where they went right. A mind built only from
them skews pessimistic.

**Fact versus principle.** "Use Postgres here" and "I prefer boring
infrastructure" look identical in text. The classifier is instructed to be
strict, and will still get some wrong in both directions.

**Drift.** Old preferences may have been superseded. Original timestamps are
preserved so decay handles this statistically, but decay cannot handle a
reversal — where the old principle is not weaker but wrong.
