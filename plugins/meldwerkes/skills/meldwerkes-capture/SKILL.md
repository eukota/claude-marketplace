---
name: meldwerkes-capture
description: Turn Meldwerkes learning on or off, and report whether it is currently recording. Use when the user wants to pause capture — NDA work, someone else at the keyboard, a throwaway experiment — or asks whether the plugin is currently learning.
---

# Capture Control

Meldwerkes records continuously once installed. This is the off switch.

## Check current state

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/history.py status
```

Report it plainly. Capture state should never be ambiguous — if the user has to
guess whether they are being recorded, the toggle is not doing its job.

## Turn capture off / on

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/history.py capture --off
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/history.py capture --on
```

The guard is enforced in `write.py`, not by instruction — with capture off, a
write is refused at the storage layer even if something later tries to record.

## When to suggest turning it off

Offer proactively; do not wait to be asked:

- Work under NDA, or a client's proprietary code
- Someone else is at the keyboard — their preferences are not the owner's
- A throwaway experiment whose choices should not shape the model
- Debugging Meldwerkes itself, where the loop would record its own noise

## When to suggest turning it back on

If capture has been off for a whole session, mention it once at a natural
point. A toggle someone forgets to restore ends up permanently off after the
first time they were cautious — which is the failure mode that quietly kills
the whole system.

Once is enough. Do not nag.

## The limitation to state honestly

**Pausing stops Meldwerkes from recording. It does not stop Claude Code from
writing its transcripts.** Everything still lands in `~/.claude/projects/`, so
a later `/meldwerkes-bootstrap` could import a period the user had deliberately
paused.

If they need that guaranteed, tell them to bound the bootstrap with `--since`
so the paused window is excluded. Do not let someone believe pausing erases the
conversation — it does not.
