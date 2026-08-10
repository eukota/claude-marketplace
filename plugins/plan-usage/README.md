# plan-usage

Tracks your Claude **account-level** rate-limit usage — the 5-hour and 7-day
subscription windows, not per-session context or tokens — and reports whether
your plan is the thing constraining your work.

## Why

Claude Code shows account rate limits in the status line, but only as a
snapshot. A snapshot cannot answer the question that actually matters: *am I
hitting the ceiling often enough to pay for a higher tier?* This plugin keeps
the history that turns the snapshot into an answer.

## Install

```
/plugin install plan-usage@eukota-claude-marketplace
/usage-install
```

`/usage-install` wires the status line into `~/.claude/settings.json`. Claude
Code's `statusLine` is a settings field that plugins cannot declare, so this
step is explicit — and the command will not overwrite an existing status line
without asking.

## Use

```
/usage-report            # last 30 days
/usage-report --days 7   # last week
```

Or run the script directly:

```bash
python3 scripts/usage-report.py --days 14
```

## What the status line shows

```
~/Development/my-project  used ▓▓░░░░░░░░ 18%  left ▓▓▓▓▓▓▓▓░░ 82%  $0.9705
acct  5h ▓▓▓░░░░░░░ 27% used, 73% left (resets 2h12m)  |  7d ▓▓▓▓▓▓░░░░ 61% used, 39% left (resets 3d3h)
```

Line 1 is the session: context window and running cost. Line 2 is the account:
both subscription windows with countdowns to reset, colored green under 50%,
yellow to 75%, red above.

## How the verdict works

Rows are grouped by the window's `resets_at` epoch and reduced to a **peak per
window** — a window's percentage only climbs, so the peak is the figure that
says whether it ran out. In-flight windows are excluded.

| Signal | Upgrade | Watch |
|---|---|---|
| Saturated 5h windows/week (peak ≥95%) | ≥2 | ≥0.5 |
| Worst completed 7d peak | ≥90% | ≥70% |

Either signal alone triggers an upgrade verdict. The 5-hour signal counts on
its own because a saturated session window interrupts work in progress, which
costs more than the throughput lost to a weekly cap.

Verdicts are marked provisional under 14 days of history.

## Files

| Path | Purpose |
|---|---|
| `scripts/statusline.sh` | Renders both lines; appends usage history |
| `scripts/usage-report.py` | Groups windows, computes peaks, renders the verdict |
| `commands/usage-report.md` | `/usage-report` |
| `commands/usage-install.md` | `/usage-install` |
| `.claude-plugin/plugin.json` | Manifest (canonical location for discovery) |
| `skills/reading-usage-trends/SKILL.md` | How to interpret the numbers before advising |

History is written to `~/.claude/usage-log.jsonl` (override with
`CLAUDE_USAGE_LOG`). One row per observed change, deduplicated against a
sibling `.last` file so the frequent status-line redraws do not spam it.

## Limits

- `rate_limits` is populated only for Claude.ai subscribers, and only after the
  first model response in a session. Nothing is logged before that.
- There is no backfill. The log starts empty and the verdict needs roughly two
  weeks before it is worth acting on.
- The log records *how much* was consumed, never *what* consumed it. It cannot
  tell a productive heavy week from a runaway agent loop.
- The cost figure on line 1 uses a hardcoded per-model price table in
  `statusline.sh`; update it if you switch models or prices change.
