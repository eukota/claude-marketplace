import json
import os
import re
import sqlite3
import unittest
from datetime import datetime
from unittest import mock

from tests.helpers import temp_data_dir, make_brain, StubCompleter
from tests.test_auto_pairing import _write as write_transcript, _user, _assistant
import auto
import history
import memory
import review
from memory import MemoryStore, Settings

NOW = datetime(2026, 11, 17, 12, 0, 0)
DOMAINS = ["writing", "code-review", "teaching"]
SECRET = "password = hunter2hunter2hunter2"


class LoopResponder(StubCompleter):
    """Plays the classifier and the distiller."""

    def complete(self, prompt, max_tokens=4096):
        self.prompts.append(prompt)
        if prompt.startswith("You are extracting durable preferences"):
            count = len(re.findall(r"^--- \d+ ---$", prompt, re.M))
            items = []
            for n in range(1, count + 1):
                if n % 2:
                    items.append({"n": n, "kind": "correction", "domain": DOMAINS[n % 3],
                                  "principle": f"principle {n}", "confidence": 0.9})
                else:
                    items.append({"n": n, "kind": "none", "domain": "general", "principle": None,
                                  "confidence": 0.9})
            return json.dumps(items)
        if prompt.startswith("Analyze this decision log"):
            return json.dumps({"principles": [{"principle": "distilled preference", "supporting_decisions": [],
                                               "conflicting_decisions": [], "confidence": 0.8}]})
        return json.dumps({"meta_principles": []})


class EndToEndTests(unittest.TestCase):
    def test_full_loop_from_prompt_to_accepted_principle(self):
        with temp_data_dir() as root:
            MemoryStore.save_settings(Settings(auto_mode="propose"))
            store = MemoryStore(root / "memory.db")
            brains = [make_brain(store, d) for d in DOMAINS]

            prompts = [f"prompt number {i}" for i in range(60)]
            prompts[7] = f"use this config\n{SECRET}\nthanks"
            rows, events = [], []
            for i, p in enumerate(prompts):
                events += [_user(p), _assistant(f"assistant reply {i}")]
                rows.append({"prompt": p, "session_id": "s1", "timestamp": f"2026-11-17T09:{i:02d}:00"})
            (root / "pending.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
            write_transcript(root / "transcripts", "s1", events)

            completer = LoopResponder()
            with mock.patch.dict(os.environ, {"MELDWERKES_TRANSCRIPTS": str(root / "transcripts")}):
                res = auto.run_once(root / "memory.db", completer, now=NOW)
            self.assertEqual(res["status"], "ok")
            run_id = res["run_id"]

            # decisions and exchanges exist; principles are proposals only
            self.assertGreater(sum(len(store.get_decisions(b.id)) for b in brains), 0)
            self.assertEqual(len(store.get_exchanges()), 60)
            proposals = store.get_proposals()
            self.assertGreater(len(proposals), 0)
            self.assertEqual(sum(len(store.get_principles(b.id)) for b in brains), 0)
            self.assertEqual(auto.load_cursor(), (root / "pending.jsonl").stat().st_size)

            # accept: principles appear and session context carries them
            for p in proposals:
                review.accept_proposal(store, p)
            self.assertGreater(sum(len(store.get_principles(b.id)) for b in brains), 0)
            self.assertIn("distilled preference", memory.SESSION_CONTEXT_FILE.read_text())

            # the planted secret reached no model prompt, no database row, no log
            self.assertTrue(all("hunter2" not in p for p in completer.prompts))
            with sqlite3.connect(root / "memory.db") as c:
                dump = "\n".join(c.iterdump())
            self.assertNotIn("hunter2", dump)
            self.assertNotIn("hunter2", (root / "logs" / "auto-latest.log").read_text())
            self.assertEqual(store.last_run()["scrubbed"], 1)

            # retract removes the run's decisions and exchanges
            counts = history.retract_run(store, run_id)
            self.assertGreater(counts["decisions"], 0)
            self.assertEqual(sum(len(store.get_decisions(b.id)) for b in brains), 0)
            self.assertEqual(store.get_exchanges(), [])
            self.assertEqual(store.last_run()["status"], "retracted")


if __name__ == "__main__":
    unittest.main()
