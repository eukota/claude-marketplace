"""Meldwerkes memory store — stdlib only, no external dependencies."""

import sqlite3
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional


# Storage path predates the rename to meldwerkes and is deliberately
# unchanged: renaming it would orphan every existing brain. Same reason
# the export format key stays "small_brain_export".
DATA_DIR = Path.home() / ".small-brain"
DEFAULT_DB = DATA_DIR / "memory.db"
SETTINGS_FILE = DATA_DIR / "settings.json"


def effective_confidence(confidence: float, timestamp: str,
                         half_life_days: float, now: Optional[str] = None) -> float:
    """Confidence discounted for age.

    A principle learned two years ago should not carry the same weight as one
    reinforced last week: people change their minds, and a mind that only
    accumulates never reflects that. Exponential decay with a configurable
    half-life — after `half_life_days`, a principle retains half its original
    confidence. A half-life of 0 disables decay entirely.
    """
    if not half_life_days:
        return confidence
    try:
        then = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return confidence
    current = (datetime.fromisoformat(now.replace("Z", "+00:00")) if now
               else datetime.now(then.tzinfo))
    age_days = max((current - then).total_seconds() / 86400.0, 0.0)
    return confidence * (0.5 ** (age_days / half_life_days))


@dataclass
class Brain:
    id: str
    name: str
    domain: str
    created_at: str
    description: str = ""


@dataclass
class Decision:
    id: str
    brain_id: str
    timestamp: str
    context: str
    decision: str
    grounding: str
    confirmed: Optional[bool] = None  # True=confirmed, False=corrected, None=pending


@dataclass
class Correction:
    id: str
    decision_id: str
    brain_id: str
    timestamp: str
    user_feedback: str
    principle_affected: str
    new_weighting: Optional[str] = None


@dataclass
class Principle:
    id: str
    brain_id: str
    timestamp: str
    principle: str
    confidence: float
    supporting_decisions: list = field(default_factory=list)
    conflicting_decisions: list = field(default_factory=list)


@dataclass
class MetaPrinciple:
    id: str
    brain_id: str
    timestamp: str
    principle_a: str
    principle_b: str
    weighting: str
    context: str
    times_applied: int = 0


@dataclass
class Settings:
    principle_auto_answer: bool = True   # Auto-apply principles without asking user
    conflict_resolution: str = "auto"    # "auto" or "manual"
    confidence_half_life_days: float = 180.0  # principle confidence halves after this many days; 0 disables
    capture_enabled: bool = True         # master switch: when off, nothing is written to the store


class MemoryStore:
    def __init__(self, db_path: Path = DEFAULT_DB):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS brains (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    domain TEXT,
                    created_at TEXT,
                    description TEXT
                );
                CREATE TABLE IF NOT EXISTS decisions (
                    id TEXT PRIMARY KEY,
                    brain_id TEXT,
                    timestamp TEXT,
                    context TEXT,
                    decision TEXT,
                    grounding TEXT,
                    confirmed INTEGER,
                    FOREIGN KEY (brain_id) REFERENCES brains(id)
                );
                CREATE TABLE IF NOT EXISTS corrections (
                    id TEXT PRIMARY KEY,
                    decision_id TEXT,
                    brain_id TEXT,
                    timestamp TEXT,
                    user_feedback TEXT,
                    principle_affected TEXT,
                    new_weighting TEXT,
                    FOREIGN KEY (decision_id) REFERENCES decisions(id),
                    FOREIGN KEY (brain_id) REFERENCES brains(id)
                );
                CREATE TABLE IF NOT EXISTS principles (
                    id TEXT PRIMARY KEY,
                    brain_id TEXT,
                    timestamp TEXT,
                    principle TEXT,
                    confidence REAL,
                    supporting_decisions TEXT,
                    conflicting_decisions TEXT,
                    FOREIGN KEY (brain_id) REFERENCES brains(id)
                );
                CREATE TABLE IF NOT EXISTS meta_principles (
                    id TEXT PRIMARY KEY,
                    brain_id TEXT,
                    timestamp TEXT,
                    principle_a TEXT,
                    principle_b TEXT,
                    weighting TEXT,
                    context TEXT,
                    times_applied INTEGER,
                    FOREIGN KEY (brain_id) REFERENCES brains(id)
                );
            """)

    # --- Brains ---

    def create_brain(self, name: str, domain: str, description: str = "") -> Brain:
        brain = Brain(
            id=str(uuid.uuid4()),
            name=name,
            domain=domain,
            created_at=datetime.now().isoformat(),
            description=description
        )
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO brains VALUES (?, ?, ?, ?, ?)",
                (brain.id, brain.name, brain.domain, brain.created_at, brain.description)
            )
        return brain

    def get_brains(self) -> list[Brain]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute("SELECT * FROM brains").fetchall()
        return [Brain(*r) for r in rows]

    def get_brain(self, brain_id: str) -> Optional[Brain]:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute("SELECT * FROM brains WHERE id = ?", (brain_id,)).fetchone()
        return Brain(*row) if row else None

    # --- Decisions ---

    def save_decision(self, decision: Decision):
        confirmed_int = None if decision.confirmed is None else int(decision.confirmed)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO decisions VALUES (?, ?, ?, ?, ?, ?, ?)",
                (decision.id, decision.brain_id, decision.timestamp,
                 decision.context, decision.decision, decision.grounding, confirmed_int)
            )

    def confirm_decision(self, decision_id: str, confirmed: bool):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE decisions SET confirmed = ? WHERE id = ?",
                (int(confirmed), decision_id)
            )

    def get_decisions(self, brain_id: str) -> list[Decision]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT * FROM decisions WHERE brain_id = ? ORDER BY timestamp",
                (brain_id,)
            ).fetchall()
        return [Decision(r[0], r[1], r[2], r[3], r[4], r[5],
                         None if r[6] is None else bool(r[6])) for r in rows]

    # --- Corrections ---

    def save_correction(self, correction: Correction):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO corrections VALUES (?, ?, ?, ?, ?, ?, ?)",
                (correction.id, correction.decision_id, correction.brain_id,
                 correction.timestamp, correction.user_feedback,
                 correction.principle_affected, correction.new_weighting)
            )
        self.confirm_decision(correction.decision_id, False)

    def get_corrections(self, brain_id: str) -> list[Correction]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT * FROM corrections WHERE brain_id = ? ORDER BY timestamp",
                (brain_id,)
            ).fetchall()
        return [Correction(*r) for r in rows]

    # --- Principles ---

    def save_principle(self, principle: Principle):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO principles VALUES (?, ?, ?, ?, ?, ?, ?)",
                (principle.id, principle.brain_id, principle.timestamp,
                 principle.principle, principle.confidence,
                 json.dumps(principle.supporting_decisions),
                 json.dumps(principle.conflicting_decisions))
            )

    def reinforce_principle(self, principle_id: str, boost: float = 0.05) -> bool:
        """Reaffirm a principle: reset its clock and nudge confidence up.

        Decay measures time since a principle was last affirmed, so reinforcing
        resets the timestamp. Without this, review can only ever watch
        confidence fall — the user needs a way to say "still true".
        """
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT confidence FROM principles WHERE id = ?", (principle_id,)
            ).fetchone()
            if not row:
                return False
            new_conf = min(1.0, row[0] + boost)
            conn.execute(
                "UPDATE principles SET timestamp = ?, confidence = ? WHERE id = ?",
                (datetime.now().isoformat(), new_conf, principle_id)
            )
        return True

    def weaken_principle(self, principle_id: str, penalty: float = 0.25) -> bool:
        """Mark a principle as less true than recorded, without deleting it.

        A principle the user partly disagrees with is different from one that
        was never true — keeping it with lowered confidence preserves the
        provenance of the change.
        """
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT confidence FROM principles WHERE id = ?", (principle_id,)
            ).fetchone()
            if not row:
                return False
            conn.execute(
                "UPDATE principles SET timestamp = ?, confidence = ? WHERE id = ?",
                (datetime.now().isoformat(), max(0.0, row[0] - penalty), principle_id)
            )
        return True

    def retire_principle(self, principle_id: str) -> bool:
        """Remove a principle that is simply wrong."""
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute("DELETE FROM principles WHERE id = ?", (principle_id,))
        return cur.rowcount > 0

    def revise_principle(self, principle_id: str, text: str) -> bool:
        """Replace a principle's wording, keeping its id and supporting history."""
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                "UPDATE principles SET principle = ?, timestamp = ? WHERE id = ?",
                (text, datetime.now().isoformat(), principle_id)
            )
        return cur.rowcount > 0

    def get_principles(self, brain_id: str) -> list[Principle]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT * FROM principles WHERE brain_id = ? ORDER BY confidence DESC",
                (brain_id,)
            ).fetchall()
        return [Principle(r[0], r[1], r[2], r[3], r[4],
                          json.loads(r[5]), json.loads(r[6])) for r in rows]

    def get_all_principles(self) -> list[Principle]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT * FROM principles ORDER BY confidence DESC"
            ).fetchall()
        return [Principle(r[0], r[1], r[2], r[3], r[4],
                          json.loads(r[5]), json.loads(r[6])) for r in rows]

    # --- Meta-principles ---

    def save_meta_principle(self, meta: MetaPrinciple):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO meta_principles VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (meta.id, meta.brain_id, meta.timestamp, meta.principle_a,
                 meta.principle_b, meta.weighting, meta.context, meta.times_applied)
            )

    def get_meta_principles(self, brain_id: str) -> list[MetaPrinciple]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT * FROM meta_principles WHERE brain_id = ?", (brain_id,)
            ).fetchall()
        return [MetaPrinciple(*r) for r in rows]

    # --- Settings ---

    @staticmethod
    def load_settings() -> Settings:
        if not SETTINGS_FILE.exists():
            return Settings()
        with open(SETTINGS_FILE) as f:
            data = json.load(f)
        return Settings(
            principle_auto_answer=data.get("principle_auto_answer", True),
            conflict_resolution=data.get("conflict_resolution", "auto"),
            confidence_half_life_days=data.get("confidence_half_life_days", 180.0),
            capture_enabled=data.get("capture_enabled", True)
        )

    @staticmethod
    def save_settings(settings: Settings):
        SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(SETTINGS_FILE, "w") as f:
            json.dump({
                "principle_auto_answer": settings.principle_auto_answer,
                "conflict_resolution": settings.conflict_resolution,
                "confidence_half_life_days": settings.confidence_half_life_days,
                "capture_enabled": settings.capture_enabled
            }, f, indent=2)


CHECKPOINT_DIR = DATA_DIR / "checkpoints"


def checkpoint(db_path: Path, label: str) -> Optional[Path]:
    """Copy the store aside before a mutation.

    Principles are derived from decisions, so undoing a bulk change by deleting
    rows leaves principles whose support no longer exists. Snapshotting the
    whole file avoids reconstructing that after the fact — and SQLite stores
    this small make it nearly free.
    """
    import shutil
    if not Path(db_path).exists():
        return None
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    safe = "".join(c if c.isalnum() or c in "-_" else "-" for c in label)[:40]
    dest = CHECKPOINT_DIR / f"{stamp}__{safe}.db"
    shutil.copy2(db_path, dest)
    return dest


def list_checkpoints() -> list:
    if not CHECKPOINT_DIR.exists():
        return []
    return sorted(CHECKPOINT_DIR.glob("*.db"), reverse=True)


def restore_checkpoint(snapshot: Path, db_path: Path) -> Path:
    """Restore a snapshot, checkpointing the current state first.

    Restoring is itself a mutation, so it gets its own checkpoint — otherwise
    undo becomes a one-way door.
    """
    import shutil
    checkpoint(db_path, "pre-restore")
    shutil.copy2(snapshot, db_path)
    return db_path


SESSION_CONTEXT_FILE = DATA_DIR / "session-context.json"

# Injected context is paid on every turn of a session, not once — so it is
# capped by budget rather than by count-per-brain, which grows without limit as
# minds accumulate.
CONTEXT_MAX_PRINCIPLES = 12
CONTEXT_MAX_METAS = 5
CONTEXT_MAX_CHARS = 2000


def write_session_context(db_path: Path = None) -> Optional[Path]:
    """Precompute what SessionStart injects.

    The SessionStart hook used to open the database and render this on every
    session start. The text only changes when principles change, so it is
    rendered on mutation instead and the hook becomes a file read — no
    interpreter, no query, constant cost.
    """
    db_path = db_path or DEFAULT_DB
    try:
        store = MemoryStore(db_path)
        settings = MemoryStore.load_settings()
        brains = store.get_brains()
    except Exception:
        return None

    ranked = []
    for b in brains:
        for pr in store.get_principles(b.id):
            ranked.append((effective_confidence(pr.confidence, pr.timestamp,
                                                settings.confidence_half_life_days),
                           b.name, pr))
    ranked.sort(key=lambda t: -t[0])

    if not ranked:
        try:
            SESSION_CONTEXT_FILE.unlink(missing_ok=True)
        except Exception:
            pass
        return None

    lines = [f"## Meldwerkes — {len(brains)} mind(s), "
             f"auto-answer {'on' if settings.principle_auto_answer else 'off'}", ""]
    for eff, brain_name, pr in ranked[:CONTEXT_MAX_PRINCIPLES]:
        lines.append(f"- [{brain_name}] {pr.principle} ({eff:.0%})")

    metas = [m for b in brains for m in store.get_meta_principles(b.id)][:CONTEXT_MAX_METAS]
    for m in metas:
        lines.append(f"- [meta] {m.principle_a} > {m.principle_b} in {m.context}")

    if len(ranked) > CONTEXT_MAX_PRINCIPLES:
        lines.append(f"- (+{len(ranked) - CONTEXT_MAX_PRINCIPLES} more; "
                     "/meldwerkes-report for all)")

    context = "\n".join(lines)[:CONTEXT_MAX_CHARS]
    payload = json.dumps({"hookSpecificOutput": {
        "hookEventName": "SessionStart", "additionalContext": context}})
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        SESSION_CONTEXT_FILE.write_text(payload)
    except Exception:
        return None
    return SESSION_CONTEXT_FILE
