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

## Mind, not brain

The terminology is deliberate where it appears. *Brain* emulation belongs to a
different tradition — neurons, connectomes, substrate-level simulation,
bottom-up. Its fidelity question is whether you have modeled the hardware.

Language models do not operate at that level and will not by this route. They
work over tokens and meaning, which is the functional level: dispositions,
judgment, what someone would decide and why. That is a *mind*, and it is
substrate-independent by construction.

The distinction decides what can be evaluated. Brain-level fidelity is
inaccessible here. Mind-level fidelity is behaviorally testable: does it decide
the way its owner decides, and can it say why.

It also explains what this is not. A log of events is neither brain nor mind —
it sits below both, recording activity rather than disposition. Recall layers
do not become minds by accumulating more.

(Inside the system, a *brain* remains the concrete thing on disk: one store of
decisions, corrections, and principles. The modest noun fits the artifact; the
ambitious one describes the level being modeled.)

## Where this could go

Meldwerkes is early, and the substrate it builds — a derived model of how one
person decides — is more general than the plugin around it. Some directions it
could take, and what each would actually require:

**A sharper assistant.** The nearest one. Principles ground the agent's choices
so it stops re-litigating settled preferences. Needs nothing new; it is what the
PAHF loop already does, just with more accumulated signal.

**A mirror.** The conflict clustering is arguably more useful to the *person*
than to the agent. A system that can say "your stated preference here
contradicts what you decided there" is doing something no notebook does. Would
need the conflicts surfaced deliberately rather than only used internally to
split brains.

**A portable identity layer.** Export/import already means the model is not
bound to Claude Code. Pointed at another agent, another tool, or a future
assistant, the same principles should still apply. Needs the export format
treated as a stable contract rather than an implementation detail.

**A model that can act.** The far end: a brain accurate enough to make routine
calls on its owner's behalf, with provenance good enough to audit afterward.
Needs everything above, plus a much higher bar on the two things that are cheap
to defer and expensive to retrofit — traceability from decision back to
evidence, and calibration about what it does not know.

**A team mind.** Multi-brain orchestration was built for one person's
inconsistency across domains, but the same machinery could model where a *team*
agrees and where it does not. A different product, reachable from the same
foundation.

### What a mind has that this does not, yet

Naming the level honestly also names the gaps. A mind is more than judgment,
and each missing piece is a plausible growth direction rather than an
embarrassment:

**Perception.** Input arrives only as conversation — what the owner said and
corrected. A mind takes in the world directly. The nearer version here is
reading the artifacts themselves (the code, the document, the diff) rather than
only the discussion about them, forming principles from what it observed rather
than what it was told.

**Episodic memory.** Decisions and corrections are stored with timestamps and
context, but they function as *evidence* — fuel for deriving principles — not
as experience that can be recalled. "The time we tried this and it broke" is
not something the system can currently say. Retrieval as narrative is a
different capability from the one already built.

**Affect.** Every principle carries confidence but no valence. Nothing
distinguishes a preference held mildly from one felt strongly, or records what
frustrates and energizes. Judgment without weight is flatter than the thing it
models.

**A self-model.** Per-principle confidence exists; a model of the model does
not. The system cannot say where its coverage is thin, which domains it has
never seen its owner decide in, or how its picture of them has shifted over
time. This one gates the others — knowing what it does not know is the
precondition for letting it act.

These are not a roadmap and several are mutually exclusive in practice. The
design constraints worth holding regardless of direction: input stays
corrections rather than events, principles stay derived rather than stored, and
the model stays exportable — it should belong to the person it models.
