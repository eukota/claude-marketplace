#!/usr/bin/env python3
"""Automatic learning loop: drain captured prompts into decisions and proposals.

Capture (hooks/capture_prompt.py) appends every prompt to pending.jsonl. This
script classifies them, writes decisions, and queues distilled principles for
review. It is started detached and throttled by a SessionEnd hook, so it never
sits in the path of a turn.
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import memory

MIN_NEW_ROWS = 20
MIN_HOURS_BETWEEN_RUNS = 6
FALLBACK_HOURS = 24


def pending_path() -> Path:
    return memory.DATA_DIR / "pending.jsonl"


# ------------------------------------------------------------------- intake

def read_new(pending: Path, offset: int):
    """Parse complete lines after `offset`. Returns (rows, new_offset).

    A trailing line without a newline is still being written, so it is left
    for the next run rather than skipped or half-parsed. A malformed complete
    line is skipped and the offset moves past it.
    """
    try:
        data = Path(pending).read_bytes()
    except FileNotFoundError:
        return [], 0
    if offset > len(data):
        offset = 0  # file was truncated or replaced; start over
    rows, pos = [], offset
    while True:
        nl = data.find(b"\n", pos)
        if nl == -1:
            break
        raw = data[pos:nl]
        pos = nl + 1
        try:
            row = json.loads(raw)
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        if isinstance(row, dict) and row.get("prompt"):
            rows.append(row)
    return rows, pos


def _cursor_file() -> Path:
    return memory.DATA_DIR / "auto-cursor.json"


def load_cursor() -> int:
    try:
        return int(json.loads(_cursor_file().read_text()).get("offset", 0))
    except Exception:
        return 0


def save_cursor(offset: int) -> None:
    memory.DATA_DIR.mkdir(parents=True, exist_ok=True)
    _cursor_file().write_text(json.dumps({"offset": offset}))


def should_run(new_rows: int, last_run_at: Optional[str], now: datetime,
               *, fallback: bool = False) -> bool:
    """Throttle: enough new prompts and enough time since the last run.

    The fallback check (SessionStart) covers sessions that died without a
    SessionEnd: any backlog at all counts once the last run is over a day old.
    """
    last = None
    if last_run_at:
        try:
            last = datetime.fromisoformat(last_run_at)
        except ValueError:
            last = None
    age = None if last is None else now - last
    if fallback:
        return new_rows > 0 and (age is None or age >= timedelta(hours=FALLBACK_HOURS))
    return new_rows >= MIN_NEW_ROWS and (age is None or age >= timedelta(hours=MIN_HOURS_BETWEEN_RUNS))


# --------------------------------------------------------------------- lock

class RunLock:
    """PID lock file: one processor at a time; a dead holder's lock is replaced."""

    def __init__(self):
        self.path = memory.DATA_DIR / "auto.lock"
        self.held = False

    def acquire(self) -> bool:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        for _ in range(2):
            try:
                fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            except FileExistsError:
                if self._holder_alive():
                    return False
                try:
                    self.path.unlink()
                except FileNotFoundError:
                    pass
                continue
            with os.fdopen(fd, "w") as f:
                f.write(str(os.getpid()))
            self.held = True
            return True
        return False

    def _holder_alive(self) -> bool:
        try:
            pid = int(self.path.read_text().strip())
            os.kill(pid, 0)
            return True
        except (ValueError, FileNotFoundError):
            return False
        except ProcessLookupError:
            return False
        except PermissionError:
            return True  # exists, owned by someone else

    def release(self) -> None:
        if self.held:
            try:
                self.path.unlink()
            except FileNotFoundError:
                pass
            self.held = False

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, *exc):
        self.release()
