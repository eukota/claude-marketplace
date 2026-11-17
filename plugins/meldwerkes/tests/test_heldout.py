import io
import json
import os
import unittest
import uuid
from contextlib import redirect_stdout
from datetime import datetime, timedelta
from unittest import mock

from tests.helpers import temp_data_dir, make_brain, StubCompleter
from tests.test_auto_run import make_env, nones, item
import auto
import heldout
import memory
import report
from memory import MemoryStore, Settings, Decision

NOW = datetime(2026, 11, 17, 12, 0, 0)


def add_ex(store, i, kind="none", confidence=0.9, paired=1, brain_id="b1", decision_id=None, ts=None):
    ts = ts or (datetime(2026, 11, 1) + timedelta(hours=i)).isoformat()
    store.save_exchange(id=f"e{i:03d}", run_id="r", timestamp=ts, session_id="s", brain_id=brain_id,
                        domain="writing", kind=kind, confidence=confidence, assistant="a", user="u",
                        decision_id=decision_id, paired=paired)


class CreateTests(unittest.TestCase):
    def test_create_returns_none_below_min_items(self):
        with temp_data_dir() as root:
            store = MemoryStore(root / "memory.db")
            for i in range(10):
                add_ex(store, i)
            self.assertIsNone(heldout.create(store, min_items=100))
            self.assertFalse((root / "heldout.json").exists())

    def test_create_picks_latest_20_percent_by_time(self):
        with temp_data_dir() as root:
            store = MemoryStore(root / "memory.db")
            for i in range(100):
                add_ex(store, i, kind="correction" if i % 5 == 0 else "none")
            made = heldout.create(store, min_items=100)
            self.assertEqual(made["exchange_ids"], [f"e{i:03d}" for i in range(80, 100)])
            self.assertEqual(heldout.load(), set(made["exchange_ids"]))

    def test_create_never_overwrites_existing_file(self):
        with temp_data_dir() as root:
            store = MemoryStore(root / "memory.db")
            for i in range(100):
                add_ex(store, i)
            first = heldout.create(store, min_items=100)
            for i in range(100, 150):
                add_ex(store, i)
            again = heldout.create(store, min_items=100)
            self.assertEqual(again["exchange_ids"], first["exchange_ids"])
            self.assertEqual(json.loads((root / "heldout.json").read_text())["exchange_ids"],
                             first["exchange_ids"])

    def test_only_labelled_paired_exchanges_are_eligible(self):
        with temp_data_dir() as root:
            store = MemoryStore(root / "memory.db")
            for i in range(6):
                add_ex(store, i, kind="correction" if i % 2 else "none")
            add_ex(store, 6, paired=0)
            add_ex(store, 7, brain_id=None)
            add_ex(store, 8, kind="directive")
            add_ex(store, 9, kind="correction", confidence=0.4)
            made = heldout.create(store, frac=1.0, min_items=5)
            self.assertEqual(made["exchange_ids"], [f"e{i:03d}" for i in range(6)])

    def test_decision_ids_maps_held_out_exchanges_to_their_decisions(self):
        with temp_data_dir() as root:
            store = MemoryStore(root / "memory.db")
            add_ex(store, 0, kind="correction", decision_id="d0")
            add_ex(store, 1)
            add_ex(store, 2, kind="correction", decision_id="d2")
            heldout.create(store, frac=1.0, min_items=3)
            self.assertEqual(heldout.decision_ids(store), {"d0", "d2"})
            self.assertEqual(heldout.load(), {"e000", "e001", "e002"})

    def test_load_without_file_is_empty(self):
        with temp_data_dir():
            self.assertEqual(heldout.load(), set())


class RateTests(unittest.TestCase):
    def test_correction_rate_per_100_exchanges_by_week(self):
        with temp_data_dir() as root:
            store = MemoryStore(root / "memory.db")
            this_week = NOW - timedelta(days=2)
            last_week = NOW - timedelta(days=9)
            for i in range(10):  # this week: 2 corrections of 10, plus a low-confidence one that must not count
                add_ex(store, i, kind="correction" if i < 2 else "none", ts=(this_week + timedelta(minutes=i)).isoformat())
            add_ex(store, 10, kind="correction", confidence=0.3, ts=this_week.isoformat())
            for i in range(20, 24):  # last week: 1 of 4
                add_ex(store, i, kind="correction" if i == 20 else "none", ts=(last_week + timedelta(minutes=i)).isoformat())
            weeks = heldout.correction_rate_by_week(store, NOW, weeks=2)
            self.assertEqual(len(weeks), 2)
            self.assertEqual((weeks[0]["n"], round(weeks[0]["rate"], 1)), (4, 25.0))
            self.assertEqual((weeks[1]["n"], round(weeks[1]["rate"], 1)), (11, round(200 / 11, 1)))
            rate = heldout.correction_rate(store, (NOW - timedelta(days=7)).isoformat(), NOW.isoformat())
            self.assertEqual(round(rate, 1), round(200 / 11, 1))

    def test_correction_rate_none_when_no_exchanges(self):
        with temp_data_dir() as root:
            store = MemoryStore(root / "memory.db")
            self.assertIsNone(heldout.correction_rate(store, "2026-01-01", "2026-12-31"))
            self.assertIsNone(heldout.correction_rate_by_week(store, NOW, weeks=1)[0]["rate"])

    def test_report_and_status_show_weekly_correction_rate(self):
        with temp_data_dir() as root:
            store = MemoryStore(root / "memory.db")
            make_brain(store, "writing")
            for i in range(10):
                add_ex(store, i, kind="correction" if i < 2 else "none",
                       ts=(NOW - timedelta(days=1, minutes=i)).isoformat())
            text = auto.status_text(store, now=NOW)
            self.assertIn("correction rate (7d): 20.0 per 100 (n=10)", text)
            buf = io.StringIO()
            with mock.patch("sys.argv", ["report.py", "--db", str(root / "memory.db")]), redirect_stdout(buf):
                report.main()
            self.assertIn("Correction rate by week", buf.getvalue())
            buf = io.StringIO()
            with mock.patch("sys.argv", ["report.py", "--db", str(root / "memory.db"), "--format", "json"]), \
                    redirect_stdout(buf):
                report.main()
            self.assertIn("correction_rate_by_week", json.loads(buf.getvalue())["auto_loop"])


class DistillExclusionTests(unittest.TestCase):
    def test_distill_excludes_held_out_decisions(self):
        with temp_data_dir() as root:
            store, brain = make_env(root, ["one new prompt"])
            for i in range(5):
                d = Decision(id=f"held{i}", brain_id=brain.id, timestamp="2026-11-01T00:00:00",
                             context="c", decision=f"held-out-marker {i}", grounding="none")
                store.save_decision(d)
                add_ex(store, i, kind="correction", brain_id=brain.id, decision_id=d.id)
            for i in range(5):
                store.save_decision(Decision(id=f"keep{i}", brain_id=brain.id, timestamp="2026-11-02T00:00:00",
                                             context="c", decision=f"visible-marker {i}", grounding="none"))
            heldout.create(store, frac=1.0, min_items=5)
            principles = json.dumps({"principles": [{"principle": "p", "supporting_decisions": [],
                                                     "conflicting_decisions": [], "confidence": 0.7}]})
            c = StubCompleter([nones(1), principles])
            with mock.patch.dict(os.environ, {"MELDWERKES_TRANSCRIPTS": str(root / "transcripts")}):
                auto.run_once(root / "memory.db", c, now=NOW)
            distill_prompt = c.prompts[1]
            self.assertNotIn("held-out-marker", distill_prompt)
            self.assertIn("visible-marker", distill_prompt)



class ContaminationTests(unittest.TestCase):
    def test_exchanges_from_runs_before_the_last_distillation_are_not_eligible(self):
        import sqlite3
        with temp_data_dir() as root:
            store = MemoryStore(root / "memory.db")
            b = make_brain(store, "writing")
            store.save_principle(memory.Principle(id="p", brain_id=b.id, timestamp="2026-11-10T00:00:00",
                                                  principle="old", confidence=0.8))
            with sqlite3.connect(root / "memory.db") as c:
                c.execute("insert into auto_runs (run_id, started_at, status) values ('old', '2026-11-05T00:00:00', 'ok')")
                c.execute("insert into auto_runs (run_id, started_at, status) values ('new', '2026-11-12T00:00:00', 'ok')")
            for i in range(3):
                add_ex(store, i)
                add_ex(store, 10 + i)
            with sqlite3.connect(root / "memory.db") as c:
                c.execute("update exchanges set run_id = 'old' where id < 'e010'")
                c.execute("update exchanges set run_id = 'new' where id >= 'e010'")
            made = heldout.create(store, frac=1.0, min_items=3)
            self.assertEqual(made["exchange_ids"], ["e010", "e011", "e012"])


if __name__ == "__main__":
    unittest.main()
