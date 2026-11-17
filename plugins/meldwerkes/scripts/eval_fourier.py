#!/usr/bin/env python3
"""Experiment 1: do several domain minds plus an orchestrator beat one pooled mind?

The Meldwerkes thesis is that a person's decision function is better approximated
by a weighted sum of domain minds than by one undifferentiated mind. This tests it:
on a fixed held-out set, a model predicts whether the user would object to an
assistant's action, once given a pooled mind's principles and once given
per-mind principles. Both arms are distilled from the SAME pool of non-held-out
decisions (the 60 most recent, across all minds) with the SAME distillation call:
the pooled arm over the whole pool, the multi arm once per mind over that mind's
share of it. Same template, same model, same items; only the grouping differs.
Meta-principles are not used in either arm (they accumulate over time and would
confound the comparison). The verdict also needs an item-level paired bootstrap
interval for the r difference to exclude zero, because with a small held-out set
resampling the model alone understates the noise.

PROXY LIMITATION: ground truth is noisy. A held-out "correction" is scored 7 (the
user objected) and a held-out "none" is scored 1 (the user moved on). A "none" can
be a fresh task request rather than approval, so absolute r is understated; the
comparison between arms is what carries information.

Usage:
  python3 eval_fourier.py run [--repeats 3] [--auth subscription]
"""

import json
import os
import random
import re
import sys
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import calibrate
import compress
import heldout
import llm
import memory
import scrub

MIN_ITEMS = 30
MIN_CORRECTIONS = 5
POOLED_DECISIONS = 60

TEMPLATE = """You predict whether a user will push back on an AI assistant's action.

BELIEFS:
{principles}
END BELIEFS

The assistant just did or said:
{assistant}

Using only the beliefs above, rate from 1 to 7 how likely this user is to object to
or correct what the assistant did (1 = certainly accepts it, 7 = certainly objects).
Return ONLY the integer."""

HEADER = ("Experiment 1: multi-mind vs pooled. Ground truth is a proxy: held-out correction = 7, "
          "none = 1; a 'none' may be a new request, not approval, so compare arms, not absolute r. "
          "Arms are distilled from the same decision pool; verdict needs margin > resampling noise AND a "
          "bootstrap interval excluding zero.")


def score_items(items: list) -> dict:
    """r, MAE and ECE over [{predicted, actual, confidence}], using calibrate's own functions."""
    if not items:
        return {"r": None, "mae": None, "ece": None, "n": 0}
    xs = [float(i["predicted"]) for i in items]
    ys = [float(i["actual"]) for i in items]
    rows = [{**i, "confidence": i.get("confidence", 0.5)} for i in items]
    err, _ = calibrate.ece(rows)
    return {"r": calibrate.pearson(xs, ys),
            "mae": sum(abs(x - y) for x, y in zip(xs, ys)) / len(xs), "ece": err, "n": len(items)}


def _pool(store, exclude_ids) -> list:
    """The shared evidence both arms learn from: newest non-held-out decisions, all minds."""
    pool = [d for b in store.get_brains() for d in store.get_decisions(b.id) if d.id not in exclude_ids]
    pool.sort(key=lambda d: d.timestamp)
    return pool[-POOLED_DECISIONS:]


def _distil(completer, decisions) -> list:
    """Principles distilled from `decisions` alone, in a scratch database."""
    if not decisions:
        return []
    with tempfile.TemporaryDirectory() as tmp:
        scratch = memory.MemoryStore(Path(tmp) / "scratch.db")
        brain = scratch.create_brain("Scratch", "scratch")
        for d in decisions:
            scratch.save_decision(memory.Decision(
                id=d.id, brain_id=brain.id, timestamp=d.timestamp, context=d.context,
                decision=d.decision, grounding=d.grounding, confirmed=d.confirmed))
        compress.COMPLETER = completer
        return [p.principle for p in compress.extract_principles(scratch, brain.id, POOLED_DECISIONS)]


def build_pooled_principles(store, completer, exclude_ids) -> list:
    """Distil ONE mind from every non-held-out decision of every mind."""
    return _distil(completer, _pool(store, exclude_ids))


def build_arms(store, completer, exclude_ids) -> dict:
    """Both arms from the same pool: pooled = one distillation, multi = one per mind."""
    pool = _pool(store, exclude_ids)
    pooled = _distil(completer, pool)
    minds = [{"name": b.name, "domain": b.domain,
              "principles": _distil(completer, [d for d in pool if d.brain_id == b.id])}
             for b in store.get_brains()]
    return {"pooled": pooled, "multi": {"minds": minds, "metas": []}}


def paired_bootstrap_low(pred_a, pred_b, actual, *, seed: int = 0, iters: int = 1000) -> float:
    """Lower 5th percentile of r(b) - r(a) over items resampled with replacement."""
    rng = random.Random(seed)
    n = len(actual)
    diffs = []
    for _ in range(iters):
        idx = [rng.randrange(n) for _ in range(n)]
        ys = [float(actual[i]) for i in idx]
        ra = _r(calibrate.pearson([float(pred_a[i]) for i in idx], ys))
        rb = _r(calibrate.pearson([float(pred_b[i]) for i in idx], ys))
        diffs.append(rb - ra)
    diffs.sort()
    return diffs[int(0.05 * len(diffs))]


def render_arm(arm: str, principles) -> str:
    if arm == "pooled":
        return "\n".join(f"- {p}" for p in principles) or "- (none yet)"
    lines = []
    for m in principles["minds"]:
        lines.append(f"[{m['name']}] ({m['domain']})")
        lines += [f"  - {p}" for p in m["principles"]] or ["  - (none yet)"]
    if principles["metas"]:
        lines.append("When minds disagree:")
        lines += [f"  - {m}" for m in principles["metas"]]
    return "\n".join(lines)


def predict(completer, arm_text: str, exchange: dict) -> int:
    raw = completer.complete(TEMPLATE.format(principles=arm_text, assistant=exchange["assistant"] or "(nothing)"),
                             max_tokens=20)
    m = re.search(r"(?<!\d)([1-7])(?!\d)", raw)
    if not m:
        raise ValueError(f"no 1-7 rating in model output: {raw[:40]!r}")
    return int(m.group(1))


def _mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def _r(x):
    return 0.0 if x is None else x


def verdict(result: dict) -> str:
    """Decision rule, fixed before any run: multi-mind must beat pooled by more than the noise."""
    if result["n"] < MIN_ITEMS or result["corrections"] < MIN_CORRECTIONS:
        return "insufficient data"
    pooled = [_r(x) for x in result["arms"]["pooled"]["rs"]]
    multi = [_r(x) for x in result["arms"]["multi"]["rs"]]
    margin = sum(multi) / len(multi) - sum(pooled) / len(pooled)
    noise = max(max(pooled) - min(pooled), max(multi) - min(multi))
    ci_low = result.get("diff_ci_low")
    wins = margin > noise and (ci_low is None or ci_low > 0)
    return "multi-mind" if wins else "tie: keep the simpler structure"


def run_experiment(store, completer, repeats: int = 3, *, max_items: int = 100,
                   now: Optional[datetime] = None) -> dict:
    now = now or datetime.now()
    held = heldout.load()
    exchanges = [e for e in store.get_exchanges() if e["id"] in held and e["kind"] in ("correction", "none")]
    exchanges = exchanges[:max_items]
    result = {"date": now.isoformat(), "n": len(exchanges), "repeats": repeats,
              "corrections": sum(1 for e in exchanges if e["kind"] == "correction"), "arms": {}}
    if result["n"] < MIN_ITEMS or result["corrections"] < MIN_CORRECTIONS:
        result["verdict"] = "insufficient data"
        _record(result)
        return result

    arms = build_arms(store, completer, frozenset(heldout.decision_ids(store)))
    texts = {"pooled": render_arm("pooled", arms["pooled"]), "multi": render_arm("multi", arms["multi"])}
    per_item = {}
    for arm, text in texts.items():
        rs, maes, skipped = [], [], 0
        per_item[arm] = {}
        for _ in range(repeats):
            items = []
            for e in exchanges:
                try:
                    pred = predict(completer, text, e)
                except (ValueError, RuntimeError):
                    skipped += 1
                    continue
                items.append({"predicted": pred, "actual": 7 if e["kind"] == "correction" else 1,
                              "confidence": 0.5})
                per_item[arm].setdefault(e["id"], []).append(pred)
            score = score_items(items)
            rs.append(score["r"])
            maes.append(score["mae"])
        result["arms"][arm] = {"rs": rs, "mean_r": _mean(rs), "mean_mae": _mean(maes), "skipped": skipped}

    shared = [e for e in exchanges if e["id"] in per_item["pooled"] and e["id"] in per_item["multi"]]
    if len(shared) >= 3:
        mean = lambda xs: sum(xs) / len(xs)
        result["diff_ci_low"] = paired_bootstrap_low(
            [mean(per_item["pooled"][e["id"]]) for e in shared],
            [mean(per_item["multi"][e["id"]]) for e in shared],
            [7 if e["kind"] == "correction" else 1 for e in shared])
    result["verdict"] = verdict(result)
    _record(result)
    return result


def _record(result: dict) -> None:
    log_dir = memory.DATA_DIR / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    arms = " ".join(f"{a}: mean_r={v['mean_r']} rs={v['rs']} skipped={v['skipped']}"
                    for a, v in result["arms"].items())
    with open(log_dir / "eval-latest.log", "a") as f:
        f.write(f"{result['date']} {HEADER}\n  n={result['n']} corrections={result['corrections']} "
                f"repeats={result['repeats']} diff_ci_low={result.get('diff_ci_low')} {arms}\n  verdict: {result['verdict']}\n")
    (memory.DATA_DIR / "eval-results.json").write_text(json.dumps(result, indent=2))


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--db", default=str(memory.DEFAULT_DB))
    sub = ap.add_subparsers(dest="cmd", required=True)
    rn = sub.add_parser("run")
    rn.add_argument("--repeats", type=int, default=3)
    llm.add_auth_arg(rn)
    args = ap.parse_args(argv)
    os.environ[scrub.INTERNAL_ENV] = "1"  # our own model calls must not be captured
    store = memory.MemoryStore(Path(args.db))
    completer = llm.Completer(llm.resolve_auth(args.auth))
    result = run_experiment(store, completer, repeats=args.repeats)
    print(json.dumps(result, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
