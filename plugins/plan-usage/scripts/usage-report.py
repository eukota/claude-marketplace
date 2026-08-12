#!/usr/bin/env python3
"""Analyze ~/.claude/usage-log.jsonl and advise on whether to upgrade the plan.

The statusline appends a row whenever the account-level rate-limit percentages
change. Each row carries the window's resets_at epoch, so rows group cleanly
into 5-hour and 7-day windows and we can take a peak per window.

Usage: python3 ~/.claude/usage-report.py [--days N]
"""

import json
import os
import sys
import time
from collections import defaultdict

LOG = os.path.expanduser(
    os.environ.get("CLAUDE_USAGE_LOG", "~/.claude/usage-log.jsonl")
)

# A window this close to the cap is treated as saturated: work was throttled
# or about to be.
BLOCKED = 95.0
# Weekly peaks above this mean the plan is the binding constraint.
WEEK_HOT = 90.0
WEEK_WARM = 70.0
# Saturated 5h windows per week that justify an upgrade on their own.
BLOCKED_PER_WEEK_HOT = 2.0
BLOCKED_PER_WEEK_WARM = 0.5


def load(days):
    if not os.path.exists(LOG):
        sys.exit(f"No usage log yet at {LOG} — it fills in as you use Claude Code.")
    cutoff = time.time() - days * 86400
    rows = []
    with open(LOG) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if r.get("ts", 0) >= cutoff:
                rows.append(r)
    return rows


def peaks(rows, pct_key, reset_key):
    """Max observed percentage per window, keyed by the window's reset epoch."""
    by_window = defaultdict(float)
    for r in rows:
        pct, reset = r.get(pct_key), r.get(reset_key)
        if pct is None or reset is None:
            continue
        by_window[reset] = max(by_window[reset], float(pct))
    return by_window


def bar(pct, width=24):
    filled = int(round(pct * width / 100))
    return "#" * filled + "." * (width - filled)


def main():
    days = 30
    if "--days" in sys.argv:
        days = int(sys.argv[sys.argv.index("--days") + 1])

    rows = load(days)
    if not rows:
        sys.exit(f"No usage rows in the last {days} days.")

    span_days = max((rows[-1]["ts"] - rows[0]["ts"]) / 86400, 1 / 24)
    five = peaks(rows, "five_pct", "five_reset")
    week = peaks(rows, "week_pct", "week_reset")

    # Drop the in-flight windows from peak stats: they haven't finished
    # accumulating, so counting them understates nothing but skews averages.
    now = time.time()
    five_done = {k: v for k, v in five.items() if k < now}
    week_done = {k: v for k, v in week.items() if k < now}

    print(f"Observed span: {span_days:.1f} days ({len(rows)} samples)\n")

    print("5-hour windows")
    if five_done:
        vals = sorted(five_done.values(), reverse=True)
        blocked = [v for v in vals if v >= BLOCKED]
        blocked_rate = len(blocked) / span_days * 7
        print(f"  completed windows : {len(vals)}")
        print(f"  median peak       : {vals[len(vals) // 2]:.0f}%")
        print(f"  worst peak        : {vals[0]:.0f}%  {bar(vals[0])}")
        print(f"  saturated (>={BLOCKED:.0f}%) : {len(blocked)}  ({blocked_rate:.1f}/week)")
    else:
        blocked_rate = 0.0
        print("  no completed windows yet")

    print("\n7-day windows")
    if week_done:
        wvals = sorted(week_done.values(), reverse=True)
        week_peak = wvals[0]
        print(f"  completed windows : {len(wvals)}")
        print(f"  worst peak        : {week_peak:.0f}%  {bar(week_peak)}")
    else:
        # Fall back to the live window so a first-week run still says something.
        week_peak = max(week.values()) if week else 0.0
        print(f"  in-flight so far  : {week_peak:.0f}%  {bar(week_peak)}  (no completed window yet)")

    print("\nVerdict")
    reasons = []
    if blocked_rate >= BLOCKED_PER_WEEK_HOT:
        reasons.append(f"{blocked_rate:.1f} saturated 5h windows/week")
    if week_peak >= WEEK_HOT:
        reasons.append(f"weekly peak {week_peak:.0f}%")

    if reasons:
        print("  UPGRADE — " + "; ".join(reasons) + ".")
        print("  The plan, not your workload, is setting the pace.")
    elif blocked_rate >= BLOCKED_PER_WEEK_WARM or week_peak >= WEEK_WARM:
        print(f"  WATCH — {blocked_rate:.1f} saturated 5h windows/week, weekly peak {week_peak:.0f}%.")
        print("  You have headroom but not much. Re-check after another week.")
    else:
        print(f"  STAY — weekly peak {week_peak:.0f}%, {blocked_rate:.1f} saturated 5h windows/week.")
        print("  Current plan comfortably covers this workload.")

    if span_days < 14:
        print(f"\n  (Only {span_days:.1f} days of data — treat the verdict as provisional.)")


if __name__ == "__main__":
    main()
