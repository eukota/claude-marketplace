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
            conflict_resolution=data.get("conflict_resolution", "auto")
        )

    @staticmethod
    def save_settings(settings: Settings):
        SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(SETTINGS_FILE, "w") as f:
            json.dump({
                "principle_auto_answer": settings.principle_auto_answer,
                "conflict_resolution": settings.conflict_resolution
            }, f, indent=2)
