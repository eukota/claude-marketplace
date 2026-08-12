#!/usr/bin/env python3
"""Score a calibration run: how well does the mind predict its owner?

The agent proposes questions, predicts each answer from existing principles,
then the user answers. This scores the two against each other.

Three question kinds, and only one of them is scored for correlation:

  validation — principles make a confident prediction. Scored: this is the
               measurement. Note it is still a weak test, since the questions
               derive from the principles being tested.
  coverage   — no principle applies. Not scored; it maps where the mind is
               blind, which is the self-model gap.
  conflict   — two principles predict differently. Not scored; a disagreement
               here is a finding, not an error.

Statistics reported:
  r     Pearson correlation, predicted vs actual, on 1-7 scale answers.
        Correlation is only meaningful on continuous data — this is why
        answers are a scale rather than a choice.
  MAE   mean absolute error, in scale points. More interpretable than r.
  ECE   expected calibration error: does a 0.9-confidence principle actually
        predict within tolerance 90% of the time? Answers a question r cannot.

Input JSON (one object per question):
  [{"kind": "validation", "domain": "code-review", "question": "...",
    "predicted": 5, "actual": 6, "confidence": 0.8, "principle_id": "abc123"}]

Usage:
  python3 calibrate.py score --input run.json [--brain-id <id>]
"""

import argparse
import json
import math
import os
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from memory import MemoryStore, DEFAULT_DB

SCALE_MIN, SCALE_MAX = 1, 7
TOLERANCE = 1  # within this many scale points counts as a hit


def pearson(xs, ys):
    n = len(xs)
    if n < 3:
        return None
    mx, my = sum(xs) / n, sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    dy = math.sqrt(sum((y - my) ** 2 for y in ys))
    if dx == 0 or dy == 0:
        return None  # no variance: undefined, not zero
    return num / (dx * dy)


def scatter(xs, ys, width=46, height=13):
    """ASCII scatter of predicted vs actual, with the perfect-agreement line."""
    grid = [[" "] * width for _ in range(height)]
    span = SCALE_MAX - SCALE_MIN
    for i in range(min(width, height * 3)):
        t = i / max(width - 1, 1)
        r = height - 1 - int(t * (height - 1))
        c = int(t * (width - 1))
        grid[r][c] = "."
    for x, y in zip(xs, ys):
        c = int((x - SCALE_MIN) / span * (width - 1))
        r = height - 1 - int((y - SCALE_MIN) / span * (height - 1))
        c, r = max(0, min(width - 1, c)), max(0, min(height - 1, r))
        grid[r][c] = "#" if grid[r][c] in (" ", ".") else "@"
    out = [f"  actual {SCALE_MAX}  |" + "".join(grid[0])]
    for r in range(1, height - 1):
        out.append("          |" + "".join(grid[r]))
    out.append(f"         {SCALE_MIN}  |" + "".join(grid[height - 1]))
    out.append("          +" + "-" * width)
    out.append(f"           {SCALE_MIN}{' ' * (width - 2)}{SCALE_MAX}  predicted")
    return "\n".join(out)


def ece(items, bins=4):
    """Expected calibration error over confidence bins."""
    buckets = defaultdict(list)
    for it in items:
        b = min(int(it["confidence"] * bins), bins - 1)
        buckets[b].append(abs(it["predicted"] - it["actual"]) <= TOLERANCE)
    total = sum(len(v) for v in buckets.values())
    if not total:
        return None, []
    err, rows = 0.0, []
    for b in sorted(buckets):
        hits = buckets[b]
        acc = sum(hits) / len(hits)
        mid = (b + 0.5) / bins
        err += (len(hits) / total) * abs(acc - mid)
        rows.append((mid, acc, len(hits)))
    return err, rows


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sc = sub.add_parser("score")
    sc.add_argument("--input", required=True)
    sc.add_argument("--brain-id")
    sc.add_argument("--db", default=str(DEFAULT_DB))
    args = ap.parse_args()

    items = json.loads(Path(args.input).read_text())
    for it in items:
        it.setdefault("confidence", 0.5)
        it.setdefault("domain", "general")

    validation = [i for i in items if i.get("kind") == "validation"
                  and i.get("actual") is not None and i.get("predicted") is not None]
    coverage = [i for i in items if i.get("kind") == "coverage"]
    conflict = [i for i in items if i.get("kind") == "conflict"]

    print("=" * 70)
    print("CALIBRATION REPORT")
    print("=" * 70)
    print(f"Questions: {len(items)}  "
          f"(validation {len(validation)}, coverage {len(coverage)}, conflict {len(conflict)})")

    if len(validation) < 3:
        print("\nNot enough validation answers to score. Aim for 20+; below about")
        print("15 the correlation is too noisy to act on.")
        return

    xs = [float(i["predicted"]) for i in validation]
    ys = [float(i["actual"]) for i in validation]
    r = pearson(xs, ys)
    mae = sum(abs(x - y) for x, y in zip(xs, ys)) / len(xs)
    hit = sum(1 for x, y in zip(xs, ys) if abs(x - y) <= TOLERANCE) / len(xs)

    print("\n" + "-" * 70)
    print("AGREEMENT  (validation questions only)")
    print("-" * 70)
    print(f"  r     {r:+.3f}" if r is not None else "  r     undefined (no variance in answers)")
    print(f"  MAE   {mae:.2f} scale points")
    print(f"  within ±{TOLERANCE}: {hit:.0%} of answers")
    print(f"  n     {len(validation)}")
    if len(validation) < 15:
        print(f"  ! n={len(validation)} is small — treat r as directional only")

    print("\n" + scatter(xs, ys))

    per = defaultdict(list)
    for i in validation:
        per[i["domain"]].append(i)
    if len(per) > 1:
        print("\n" + "-" * 70)
        print("BY DOMAIN  (these are candidate weights for the mind × domain matrix)")
        print("-" * 70)
        for dom, group in sorted(per.items(), key=lambda kv: -len(kv[1])):
            gx = [float(i["predicted"]) for i in group]
            gy = [float(i["actual"]) for i in group]
            gr = pearson(gx, gy)
            gmae = sum(abs(a - b) for a, b in zip(gx, gy)) / len(gx)
            rt = f"r={gr:+.2f}" if gr is not None else "r=n/a"
            print(f"  {dom:<22} n={len(group):<4} {rt:<10} MAE={gmae:.2f}")

    err, rows = ece(validation)
    if rows:
        print("\n" + "-" * 70)
        print("CALIBRATION  (is stated confidence honest?)")
        print("-" * 70)
        for mid, acc, n in rows:
            flag = "" if abs(acc - mid) < 0.15 else "   <-- miscalibrated"
            print(f"  confidence ~{mid:.2f}  actual accuracy {acc:.2f}  (n={n}){flag}")
        print(f"\n  ECE {err:.3f}   (0 is perfect; >0.15 means confidence numbers mislead)")

    if coverage:
        print("\n" + "-" * 70)
        print(f"COVERAGE GAPS — {len(coverage)} question(s) no principle could answer")
        print("-" * 70)
        for i in coverage[:8]:
            print(f"  [{i['domain']}] {i['question'][:60]}")
        print("\n  These are the self-model gap: domains where the mind has never")
        print("  seen its owner decide. Worth capturing deliberately.")

    if conflict:
        print("\n" + "-" * 70)
        print(f"CONFLICTS — {len(conflict)} question(s) where principles disagreed")
        print("-" * 70)
        for i in conflict[:8]:
            print(f"  [{i['domain']}] {i['question'][:60]}")
        print("\n  A disagreement here is a finding, not an error — it may mean the")
        print("  domain should split into separate minds.")

    print("\n" + "-" * 70)
    print("Caveat: validation questions derive from the principles being tested,")
    print("so r is optimistic. It measures internal consistency more than")
    print("predictive power. Falling r over repeated runs is the real signal.")


if __name__ == "__main__":
    main()
