#!/usr/bin/env python3
"""Held-out split and correction-rate metric for evaluating the learning loop.

The split is created once and never regenerated: a test set that moves is not a
test set. It is drawn only from exchanges recorded by an automatic run that started
after the latest distillation, so no principle can have been distilled from them,
and their decisions are excluded from all later distillation.
"""

import json
import math
import os
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import memory

MIN_CONFIDENCE = 0.6  # a "correction" label below this is too weak to count


def _path(path=None) -> Path:
    return Path(path) if path else memory.DATA_DIR / "heldout.json"


def _naive(ts) -> Optional[datetime]:
    try:
        return datetime.fromisoformat(str(ts).replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return None


def _last_distillation(store) -> Optional[datetime]:
    with sqlite3.connect(store.db_path) as c:
        stamps = [r[0] for r in c.execute("SELECT timestamp FROM principles")]
        stamps += [r[0] for r in c.execute("SELECT created_at FROM proposals")]
    parsed = [t for t in (_naive(s) for s in stamps) if t]
    return max(parsed) if parsed else None


def eligible(store) -> list:
    """Labelled, paired, routed exchanges nothing has been distilled from, oldest first."""
    last = _last_distillation(store)
    with sqlite3.connect(store.db_path) as c:
        started = dict(c.execute("SELECT run_id, started_at FROM auto_runs"))
    out = []
    for e in store.get_exchanges():
        if not e["brain_id"] or not e["paired"]:
            continue
        if e["kind"] == "correction":
            if (e["confidence"] or 0) < MIN_CONFIDENCE:
                continue
        elif e["kind"] != "none":
            continue
        if last is not None:
            began = _naive(started.get(e["run_id"]))
            if began is not None and began <= last:
                continue  # its decisions existed when principles were distilled
        out.append(e)
    return out


def create(store, *, frac: float = 0.2, min_items: int = 100, path=None) -> Optional[dict]:
    """Write heldout.json once. Returns its contents, None if there is too little data.

    If the file already exists it is returned unchanged, never rewritten.
    """
    target = _path(path)
    if target.exists():
        return json.loads(target.read_text())
    rows = eligible(store)
    if len(rows) < min_items:
        return None
    k = max(1, math.ceil(round(frac * len(rows), 6)))
    data = {"created_at": datetime.now().isoformat(), "exchange_ids": [e["id"] for e in rows[-k:]]}
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2))
    os.replace(tmp, target)
    return data


def load(path=None) -> set:
    try:
        return set(json.loads(_path(path).read_text()).get("exchange_ids", []))
    except Exception:
        return set()


def decision_ids(store, path=None) -> set:
    """Decision ids behind held-out exchanges (only corrections have one)."""
    held = load(path)
    return {e["decision_id"] for e in store.get_exchanges() if e["id"] in held and e["decision_id"]}


def _window(store, since: str, until: str):
    rows = [e for e in store.get_exchanges(since=since) if e["timestamp"] < until]
    corrections = sum(1 for e in rows
                      if e["kind"] == "correction" and (e["confidence"] or 0) >= MIN_CONFIDENCE)
    return corrections, len(rows)


def correction_rate(store, since: str, until: str) -> Optional[float]:
    """Corrections per 100 classified exchanges in [since, until), None if there are none."""
    corrections, n = _window(store, since, until)
    return None if n == 0 else 100.0 * corrections / n


def correction_rate_by_week(store, now: datetime, weeks: int = 4) -> list:
    """Oldest to newest; each entry {week_start, rate, n}; the last week ends at `now`."""
    out = []
    for i in range(weeks - 1, -1, -1):
        until = now - timedelta(days=7 * i)
        since = until - timedelta(days=7)
        corrections, n = _window(store, since.isoformat(), until.isoformat())
        out.append({"week_start": since.date().isoformat(),
                    "rate": None if n == 0 else 100.0 * corrections / n, "n": n})
    return out
