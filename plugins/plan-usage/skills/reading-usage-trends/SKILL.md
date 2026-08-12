---
name: reading-usage-trends
description: Interprets Claude account rate-limit history — 5-hour and 7-day window peaks — to judge whether the subscription plan is constraining the user's work, and what would change that.
---

# Reading Usage Trends

## What the data is

Claude Code's status line receives a `rate_limits` object with two windows,
each carrying `used_percentage` and `resets_at`:

- `five_hour` — the rolling session window
- `seven_day` — the weekly window

The status line appends a row to `~/.claude/usage-log.jsonl` whenever those
percentages change. Each row records the window's `resets_at` epoch, which is
what makes windows groupable: every row sharing a `resets_at` belongs to the
same window.

## The one analysis rule

**Take the peak per window, not the average of samples.**

A window's percentage only climbs until it resets, so sampling it more often
during heavy use would bias any average upward — the average measures how
often you looked, not how hard you worked. The peak is the only figure that
answers "did this window run out?"

Discard windows whose `resets_at` is still in the future. They haven't
finished accumulating, and counting a window that is 20% used with three hours
left as a "20% window" understates it.

## The two signals

| Signal | Upgrade | Watch |
|---|---|---|
| Saturated 5h windows per week (peak ≥95%) | ≥2 | ≥0.5 |
| Worst completed 7d peak | ≥90% | ≥70% |

Either signal alone is sufficient for an upgrade verdict.

**Why the 5-hour signal can trigger on its own:** the weekly cap costs
throughput — you do less in a week than you wanted. A saturated 5-hour window
costs *flow* — it stops work already in progress, mid-task, and the context
you had built up goes stale before you can resume. That interruption is the
more expensive failure, so it does not need the weekly signal to corroborate
it.

## Interpreting for the user

Name the signal that drove the verdict, not just the verdict. "Upgrade" is
not useful on its own; "you hit the 5-hour wall three times last week, always
mid-afternoon" tells them what changes if they upgrade.

Watch for these before advising:

- **Short history.** Under ~14 days, the verdict is provisional — say so. A
  single unusual week dominates a small sample.
- **A recent change in how they work.** A new project, a migration, or a
  switch to heavier agentic use will show as a step change rather than a
  trend. Peaks from before that step describe a workload that no longer
  exists.
- **One bad week versus a rising line.** Compare recent windows against older
  ones. A single saturated week amid quiet ones argues for scheduling, not
  spending; a monotonic climb argues for the upgrade.
- **Saturation clustered in time.** If every saturated window falls on the
  same day or the same hours, the constraint may be schedulable — moving
  batch-style work off the peak may buy more than a plan tier.

## What this does not tell you

The log carries no information about *what* consumed the budget. It cannot
distinguish a productive heavy week from a week lost to a runaway agent loop.
Before recommending a plan change on a single dramatic week, ask what the user
was doing — the answer sometimes points at a fix rather than a purchase.
