import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from datetime import datetime
from pathlib import Path
from unittest import mock

from tests.helpers import temp_data_dir, make_brain
import auto
import memory
from memory import MemoryStore, Settings, Proposal

PLUGIN = Path(__file__).resolve().parent.parent
AUTO = PLUGIN / "scripts" / "auto.py"
NOW = datetime(2026, 11, 17, 12, 0, 0)


def pending(root, n):
    (root / "pending.jsonl").write_text(
        "".join(json.dumps({"prompt": f"p{i}", "session_id": "s", "timestamp": "2026-11-17T09:00:00"}) + "\n"
                for i in range(n)))


class MaybeRunCliTests(unittest.TestCase):
    def _run(self, home, *args):
        env = {**os.environ, "HOME": home}
        started = time.monotonic()
        proc = subprocess.run([sys.executable, str(AUTO), "maybe-run", *args], capture_output=True,
                              text=True, env=env, timeout=20)
        return proc, time.monotonic() - started

    def test_maybe_run_returns_fast_and_exits_zero_when_not_due(self):
        with tempfile.TemporaryDirectory() as home:
            data = Path(home) / ".small-brain"
            data.mkdir()
            (data / "settings.json").write_text(json.dumps({"auto_mode": "propose"}))
            MemoryStore(data / "memory.db")
            proc, took = self._run(home)
            self.assertEqual(proc.returncode, 0)
            self.assertLess(took, 1.0)
            self.assertFalse((data / "logs" / "auto-latest.log").exists())

    def test_maybe_run_exits_zero_with_missing_db_and_unreadable_settings(self):
        with tempfile.TemporaryDirectory() as home:
            self.assertEqual(self._run(home)[0].returncode, 0)
            data = Path(home) / ".small-brain"
            data.mkdir()
            (data / "settings.json").write_text("{not json")
            self.assertEqual(self._run(home)[0].returncode, 0)
            self.assertEqual(self._run(home, "--fallback")[0].returncode, 0)


class MaybeRunLogicTests(unittest.TestCase):
    def test_maybe_run_does_nothing_when_auto_mode_off(self):
        with temp_data_dir() as root:
            MemoryStore.save_settings(Settings(auto_mode="off"))
            MemoryStore(root / "memory.db")
            pending(root, 40)
            with mock.patch("auto.subprocess.Popen") as popen:
                self.assertEqual(auto.maybe_run(now=NOW), "off")
            popen.assert_not_called()

    def test_maybe_run_spawns_detached_run_when_due(self):
        with temp_data_dir() as root:
            MemoryStore.save_settings(Settings(auto_mode="propose"))
            MemoryStore(root / "memory.db")
            pending(root, 25)
            with mock.patch("auto.subprocess.Popen") as popen, \
                    mock.patch("auto.llm.subscription_available", return_value=True):
                self.assertEqual(auto.maybe_run(now=NOW), "spawned")
            popen.assert_called_once()
            argv = popen.call_args.args[0]
            self.assertIn("run", argv)
            self.assertIn("--auth", argv)
            self.assertIn("subscription", argv)
            self.assertTrue(popen.call_args.kwargs.get("start_new_session"))

    def test_maybe_run_does_not_spawn_when_a_run_holds_the_lock(self):
        with temp_data_dir() as root:
            MemoryStore.save_settings(Settings(auto_mode="propose"))
            MemoryStore(root / "memory.db")
            pending(root, 25)
            held = auto.RunLock()
            held.acquire()
            try:
                with mock.patch("auto.subprocess.Popen") as popen, \
                        mock.patch("auto.llm.subscription_available", return_value=True):
                    self.assertEqual(auto.maybe_run(now=NOW), "locked")
                popen.assert_not_called()
            finally:
                held.release()

    def test_maybe_run_not_due_below_threshold_and_fallback_after_a_day(self):
        with temp_data_dir() as root:
            MemoryStore.save_settings(Settings(auto_mode="propose"))
            MemoryStore(root / "memory.db")
            pending(root, 3)
            with mock.patch("auto.subprocess.Popen") as popen, \
                    mock.patch("auto.llm.subscription_available", return_value=True):
                self.assertEqual(auto.maybe_run(now=NOW), "not-due")
                popen.assert_not_called()
                self.assertEqual(auto.maybe_run(now=NOW, fallback=True), "spawned")


class WiringTests(unittest.TestCase):
    def test_hooks_json_is_valid_and_uses_plugin_root_variable_only(self):
        data = json.loads((PLUGIN / "hooks" / "hooks.json").read_text())
        cmds = [h["command"] for ev in data["hooks"].values() for entry in ev for h in entry["hooks"]]
        self.assertTrue(all("/Users/" not in c and "/home/" not in c for c in cmds))
        auto_cmds = [c for c in cmds if "auto.py" in c]
        self.assertTrue(all("${CLAUDE_PLUGIN_ROOT}" in c for c in auto_cmds))
        end = [h["command"] for e in data["hooks"]["SessionEnd"] for h in e["hooks"]]
        self.assertTrue(any("maybe-run" in c and "--fallback" not in c for c in end))
        start = [h["command"] for e in data["hooks"]["SessionStart"] for h in e["hooks"]]
        self.assertTrue(any("maybe-run --fallback" in c for c in start))
        self.assertTrue(all("|| true" in c for c in auto_cmds))

    def test_session_context_mentions_pending_proposals(self):
        with temp_data_dir() as root:
            store = MemoryStore(root / "memory.db")
            b = make_brain(store, "writing")
            store.save_proposal(Proposal(id="p1", brain_id=b.id, kind="principle",
                                         payload={"principle": "x", "confidence": 0.5},
                                         status="proposed", run_id="r", created_at="2026-11-17T00:00:00"))
            memory.write_session_context(root / "memory.db")
            text = memory.SESSION_CONTEXT_FILE.read_text()
            self.assertIn("1 proposal(s) awaiting review", text)

    def test_skill_has_frontmatter_name_and_description(self):
        text = (PLUGIN / "skills" / "meldwerkes-auto" / "SKILL.md").read_text()
        self.assertTrue(text.startswith("---\n"))
        head = text.split("---")[1]
        self.assertIn("name: meldwerkes-auto", head)
        self.assertIn("description:", head)


if __name__ == "__main__":
    unittest.main()
