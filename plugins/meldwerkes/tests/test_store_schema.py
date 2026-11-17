import json
import sqlite3
import unittest

from tests.helpers import temp_data_dir, make_brain
import memory
from memory import MemoryStore, Proposal, Settings


class SettingsTests(unittest.TestCase):
    def test_auto_mode_defaults_off_when_key_absent(self):
        with temp_data_dir() as root:
            (root / "settings.json").write_text(json.dumps({"principle_auto_answer": False}))
            self.assertEqual(MemoryStore.load_settings().auto_mode, "off")
            self.assertEqual(Settings().auto_mode, "off")

    def test_auto_mode_roundtrips(self):
        with temp_data_dir():
            MemoryStore.save_settings(Settings(auto_mode="propose"))
            self.assertEqual(MemoryStore.load_settings().auto_mode, "propose")


class SchemaTests(unittest.TestCase):
    def test_new_tables_created_and_old_tables_unchanged(self):
        with temp_data_dir() as root:
            MemoryStore(root / "memory.db")
            with sqlite3.connect(root / "memory.db") as c:
                tables = {r[0] for r in c.execute("select name from sqlite_master where type='table'")}
                self.assertTrue({"proposals", "run_items", "exchanges", "auto_runs"} <= tables)
                self.assertEqual(len(c.execute("pragma table_info(brains)").fetchall()), 5)
                self.assertEqual(len(c.execute("pragma table_info(decisions)").fetchall()), 7)

    def test_existing_db_gains_new_tables(self):
        with temp_data_dir() as root:
            db = root / "memory.db"
            with sqlite3.connect(db) as c:
                c.execute("create table brains (id TEXT PRIMARY KEY, name TEXT, domain TEXT, created_at TEXT, description TEXT)")
                c.execute("insert into brains values ('b1','Old','writing','2026-01-01','')")
            store = MemoryStore(db)
            self.assertEqual([b.id for b in store.get_brains()], ["b1"])
            with sqlite3.connect(db) as c:
                tables = {r[0] for r in c.execute("select name from sqlite_master where type='table'")}
            self.assertIn("proposals", tables)


class ProposalAndRunTests(unittest.TestCase):
    def test_proposal_lifecycle(self):
        with temp_data_dir() as root:
            store = MemoryStore(root / "memory.db")
            brain = make_brain(store, "writing")
            p = Proposal(id="p1", brain_id=brain.id, kind="principle",
                         payload={"principle": "be brief", "confidence": 0.7},
                         status="proposed", run_id="r1", created_at="2026-11-17T00:00:00")
            store.save_proposal(p)
            got = store.get_proposals()
            self.assertEqual([g.id for g in got], ["p1"])
            self.assertEqual(got[0].payload["principle"], "be brief")
            store.decide_proposal("p1", "accepted")
            self.assertEqual(store.get_proposals(), [])
            self.assertEqual([g.id for g in store.get_proposals(status="accepted")], ["p1"])

    def test_run_items_roundtrip(self):
        with temp_data_dir() as root:
            store = MemoryStore(root / "memory.db")
            store.record_run_item("r1", "decision", "d1")
            store.record_run_item("r1", "exchange", "e1")
            store.record_run_item("r2", "decision", "d2")
            self.assertEqual(sorted(store.get_run_items("r1")),
                             [("decision", "d1"), ("exchange", "e1")])

    def test_exchange_and_run_records(self):
        with temp_data_dir() as root:
            store = MemoryStore(root / "memory.db")
            store.save_exchange(id="e1", run_id="r1", timestamp="2026-11-17T01:00:00",
                                session_id="s", brain_id=None, domain="writing", kind="none",
                                confidence=0.3, assistant="a", user="u", decision_id=None, paired=1)
            self.assertEqual([e["id"] for e in store.get_exchanges(kind="none")], ["e1"])
            self.assertEqual(store.get_exchanges(kind="correction"), [])
            store.start_run("r1")
            store.finish_run("r1", rows_read=3, decisions=1, status="ok")
            last = store.last_run()
            self.assertEqual((last["run_id"], last["rows_read"], last["status"]), ("r1", 3, "ok"))


if __name__ == "__main__":
    unittest.main()
