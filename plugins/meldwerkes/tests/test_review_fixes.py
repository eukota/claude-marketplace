"""Regression tests for the whole-branch review's Critical and Important findings."""
import json
import os
import sqlite3
import subprocess
import sys
import textwrap
import time
import unittest
from datetime import datetime
from unittest import mock

from tests.helpers import temp_data_dir, make_brain, StubCompleter
from tests.test_auto_run import make_env, nones, item, run, NOW
from tests.test_auto_hooks import pending
from tests.test_heldout import add_ex
import auto
import compress
import eval_fourier
import heldout
import memory
import scrub
from memory import MemoryStore, Settings, Decision, Principle


# ---- 1. maybe-run must not stall on a locked database
class LockedDbHookTests(unittest.TestCase):
    def test_maybe_run_returns_fast_when_the_database_is_write_locked(self):
        with temp_data_dir() as root:
            MemoryStore.save_settings(Settings(auto_mode="propose"))
            MemoryStore(root / "memory.db")
            pending(root, 25)
            blocker = sqlite3.connect(root / "memory.db", isolation_level=None)
            blocker.execute("BEGIN EXCLUSIVE")
            try:
                with mock.patch("auto.subprocess.Popen"), \
                        mock.patch("auto.llm.subscription_available", return_value=True):
                    started = time.monotonic()
                    status = auto.maybe_run(now=NOW)
                    took = time.monotonic() - started
            finally:
                blocker.execute("ROLLBACK")
                blocker.close()
            self.assertLess(took, 1.0)
            self.assertIn(status, ("spawned", "not-due"))


# ---- 2. scrub gaps
class ScrubGapTests(unittest.TestCase):
    def test_more_secret_shapes_are_removed(self):
        cases = [
            "sk-ant-api03-AbCdEf1234567890xyzABCDEF",
            "my key is sk-abcdefghijklmnopqrstuvwx1234",
            "postgres://admin:s3cretpass@db.example.com/app",
            "Authorization: Basic dXNlcjpwYXNzd29yZA==",
            "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dBjftJeZ4CVPmB92K27uhbUJU1p1r_wW1gFWFOEjXk",
        ]
        for line in cases:
            clean, n = scrub.scrub(f"before\n{line}\nafter")
            self.assertEqual((clean, n), ("before\nafter", 1), line)

    def test_whole_pem_block_is_removed_not_just_the_header(self):
        text = ("before\n-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA1234\nabcdEFGH5678\n"
                "-----END RSA PRIVATE KEY-----\nafter")
        clean, n = scrub.scrub(text)
        self.assertEqual(clean, "before\nafter")
        self.assertEqual(n, 4)
        self.assertNotIn("MIIEow", clean)

    def test_unterminated_pem_block_drops_to_the_end(self):
        clean, n = scrub.scrub("keep\n-----BEGIN PRIVATE KEY-----\nAAAAAAAAAAAAAAAA\nBBBBBBBBBBBBBBBB")
        self.assertEqual(clean, "keep")
        self.assertEqual(scrub.scrub("a\n-----BEGIN PRIVATE KEY-----\nsee above"), ("a\nsee above", 1))

    def test_lookalikes_survive(self):
        for line in ("the sk-learn library", "see https://example.com/path?x=1", "user:pass format",
                     "a.b.c is not a jwt"):
            self.assertEqual(scrub.scrub(line), (line, 0), line)


# ---- 3. lock is kernel-backed
class FlockTests(unittest.TestCase):
    def test_a_live_holder_in_another_process_blocks_and_death_releases(self):
        with temp_data_dir() as root:
            code = textwrap.dedent(f"""
                import fcntl, sys, time
                f = open({str(root / 'auto.lock')!r}, 'a+')
                fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
                print('held', flush=True)
                time.sleep(30)
            """)
            proc = subprocess.Popen([sys.executable, "-c", code], stdout=subprocess.PIPE, text=True)
            try:
                self.assertEqual(proc.stdout.readline().strip(), "held")
                self.assertFalse(auto.RunLock().acquire())
                self.assertTrue(auto.RunLock().is_held())
            finally:
                proc.kill()
                proc.wait()
            lock = auto.RunLock()
            self.assertTrue(lock.acquire())
            lock.release()

    def test_empty_lock_file_while_held_is_still_held(self):
        with temp_data_dir():
            a = auto.RunLock()
            self.assertTrue(a.acquire())
            a.path.write_text("")  # a racing writer could see it empty
            self.assertTrue(auto.RunLock().is_held())
            self.assertFalse(auto.RunLock().acquire())
            a.release()


# ---- 4. propose-mode held-out leak
class ProposeLeakTests(unittest.TestCase):
    def test_exchanges_from_the_distilling_run_are_not_heldout_eligible_in_propose_mode(self):
        with temp_data_dir() as root:
            store, brain = make_env(root, [f"no, fix {i}" for i in range(6)])
            reply = json.dumps([item(i + 1, "correction", principle=f"p{i}") for i in range(6)])
            principles = json.dumps({"principles": [{"principle": "distilled", "supporting_decisions": [],
                                                     "conflicting_decisions": [], "confidence": 0.7}]})
            res = run(root, StubCompleter([reply, principles]))
            self.assertEqual(res["status"], "ok")
            self.assertGreaterEqual(len(store.get_proposals()), 1)
            self.assertEqual(heldout.eligible(store), [])


# ---- 5. experiment arms are built from the same decisions
def _two_mind_store(root):
    store = MemoryStore(root / "memory.db")
    a, b = make_brain(store, "writing"), make_brain(store, "code-review")
    for brain, tag in ((a, "wr"), (b, "cr")):
        for i in range(4):
            store.save_decision(Decision(id=f"{tag}{i}", brain_id=brain.id,
                                         timestamp=f"2026-11-0{i + 1}T00:00:00", context="c",
                                         decision=f"dec-{tag}-{i}", grounding="none"))
        store.save_principle(Principle(id=f"live-{tag}", brain_id=brain.id, timestamp="2026-11-01T00:00:00",
                                       principle=f"accumulated live principle {tag}", confidence=0.9))
    return store, a, b


class DistillResponder(StubCompleter):
    def complete(self, prompt, max_tokens=4096):
        self.prompts.append(prompt)
        return json.dumps({"principles": [{"principle": "p", "supporting_decisions": [],
                                           "conflicting_decisions": [], "confidence": 0.7}]})


class ArmFairnessTests(unittest.TestCase):
    def test_multi_arm_distils_each_mind_from_the_same_pool_the_pooled_arm_uses(self):
        with temp_data_dir() as root:
            store, a, b = _two_mind_store(root)
            c = DistillResponder()
            arms = eval_fourier.build_arms(store, c, frozenset())
            self.assertEqual(len(c.prompts), 3)  # one pooled + one per mind
            pooled_prompt, *mind_prompts = c.prompts
            decisions = {f"dec-{t}-{i}" for t in ("wr", "cr") for i in range(4)}
            self.assertEqual({d for d in decisions if d in pooled_prompt}, decisions)
            seen = set()
            for mp in mind_prompts:
                got = {d for d in decisions if d in mp}
                self.assertTrue(got)
                self.assertFalse(got & seen)
                seen |= got
            self.assertEqual(seen, decisions)
            rendered = eval_fourier.render_arm("multi", arms["multi"])
            self.assertNotIn("accumulated live principle", rendered)
            self.assertEqual(arms["multi"]["metas"], [])

    def test_held_out_decisions_are_excluded_from_both_arms(self):
        with temp_data_dir() as root:
            store, a, b = _two_mind_store(root)
            c = DistillResponder()
            eval_fourier.build_arms(store, c, frozenset({"wr0", "cr0"}))
            self.assertTrue(all("dec-wr-0" not in p and "dec-cr-0" not in p for p in c.prompts))


class BootstrapVerdictTests(unittest.TestCase):
    def test_bootstrap_lower_bound_positive_only_for_a_real_gain(self):
        actual = [7, 1] * 20
        good = [7, 1] * 20
        noise = [4, 4, 1, 7] * 10
        self.assertGreater(eval_fourier.paired_bootstrap_low(noise, good, actual, seed=0, iters=300), 0)
        self.assertLessEqual(eval_fourier.paired_bootstrap_low(good, good, actual, seed=0, iters=300), 0)

    def test_verdict_requires_the_item_level_interval_to_exclude_zero(self):
        base = {"n": 50, "corrections": 10,
                "arms": {"pooled": {"rs": [.30, .32, .35]}, "multi": {"rs": [.55, .52, .50]}}}
        self.assertEqual(eval_fourier.verdict({**base, "diff_ci_low": 0.05}), "multi-mind")
        self.assertTrue(eval_fourier.verdict({**base, "diff_ci_low": -0.02}).startswith("tie"))
        self.assertEqual(eval_fourier.verdict(base), "multi-mind")  # no interval recorded: rule unchanged


# ---- 6. duplicates
class DuplicateTests(unittest.TestCase):
    def test_distill_prompt_lists_existing_and_drops_exact_duplicates(self):
        with temp_data_dir() as root:
            store = MemoryStore(root / "memory.db")
            b = make_brain(store, "writing")
            for i in range(5):
                store.save_decision(Decision(id=f"d{i}", brain_id=b.id, timestamp="2026-11-16T00:00:00",
                                             context="c", decision=f"dec {i}", grounding="none"))
            store.save_principle(Principle(id="p", brain_id=b.id, timestamp="2026-11-01T00:00:00",
                                           principle="Be brief", confidence=0.8))
            reply = json.dumps({"principles": [
                {"principle": "be brief.", "supporting_decisions": [], "conflicting_decisions": [], "confidence": 0.8},
                {"principle": "cite sources", "supporting_decisions": [], "conflicting_decisions": [], "confidence": 0.8}]})
            c = StubCompleter([reply])
            props = auto.distill(store, c, b.id, "r", "propose", now=datetime(2026, 11, 17))
            self.assertEqual([p.payload["principle"] for p in props], ["cite sources"])
            self.assertIn("Be brief", c.prompts[0])
            # a second distill must not re-propose the pending one either
            c2 = StubCompleter([reply])
            props2 = auto.distill(store, c2, b.id, "r2", "propose", now=datetime(2026, 11, 17))
            self.assertEqual(props2, [])


# ---- 7. poison batch
class PoisonBatchTests(unittest.TestCase):
    def test_a_batch_that_keeps_failing_is_skipped_after_three_attempts(self):
        with temp_data_dir() as root:
            store, brain = make_env(root, [f"prompt {i}" for i in range(40)])
            rows, _ = auto.read_new(root / "pending.jsonl", 0)
            for attempt in (1, 2):
                res = run(root, StubCompleter(["garbage"]))
                self.assertEqual(res["status"], "partial")
                self.assertEqual(auto.load_cursor(), 0, f"attempt {attempt}")
            res = run(root, StubCompleter(["garbage"]))
            self.assertEqual(auto.load_cursor(), rows[19]["_end"])
            self.assertIn("skipped", (root / "logs" / "auto-latest.log").read_text())
            res = run(root, StubCompleter([nones(20)]))
            self.assertEqual(res["status"], "ok")
            self.assertEqual(len(store.get_exchanges()), 20)  # the skipped batch was never written

    def test_progress_resets_the_failure_count(self):
        with temp_data_dir() as root:
            store, brain = make_env(root, [f"prompt {i}" for i in range(40)])
            run(root, StubCompleter(["garbage"]))
            run(root, StubCompleter([nones(20), "garbage"]))  # progress: first batch lands
            self.assertGreater(auto.load_cursor(), 0)
            run(root, StubCompleter(["garbage"]))
            run(root, StubCompleter(["garbage"]))
            self.assertEqual(len(store.get_exchanges()), 20)  # still not skipped: only 2 fails since progress


# ---- 11. backlog drained after a distillation still counts
class BacklogDueTests(unittest.TestCase):
    def test_decisions_from_a_later_run_count_even_with_old_prompt_timestamps(self):
        with temp_data_dir() as root:
            store = MemoryStore(root / "memory.db")
            b = make_brain(store, "writing")
            store.save_principle(Principle(id="p", brain_id=b.id, timestamp="2026-11-10T00:00:00",
                                           principle="old", confidence=0.8))
            with sqlite3.connect(root / "memory.db") as c:
                c.execute("insert into auto_runs (run_id, started_at, status) values ('late', '2026-11-12T00:00:00', 'ok')")
            for i in range(5):
                store.save_decision(Decision(id=f"d{i}", brain_id=b.id, timestamp="2026-11-01T00:00:00",
                                             context="c", decision=f"old prompt {i}", grounding="none"))
                store.record_run_item("late", "decision", f"d{i}")
            self.assertTrue(auto.due_for_distill(store, b.id, datetime(2026, 11, 17, 12)))


if __name__ == "__main__":
    unittest.main()
