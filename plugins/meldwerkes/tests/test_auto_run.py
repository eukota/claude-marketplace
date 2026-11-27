import json
import math
import os
import sqlite3
import unittest
from datetime import datetime
from unittest import mock

from tests.helpers import temp_data_dir, make_brain, StubCompleter
from tests.test_auto_pairing import _write as write_transcript, _user, _assistant
import auto
import history
import memory
from memory import MemoryStore, Settings

NOW = datetime(2026, 11, 17, 12, 0, 0)


def item(n, kind="none", domain="writing", principle=None, confidence=0.9):
    return {"n": n, "kind": kind, "domain": domain, "principle": principle, "confidence": confidence}


def nones(count):
    return json.dumps([item(i + 1) for i in range(count)])


def make_env(root, prompts, mode="propose", domain="writing", session="s1"):
    """Store with one mind, a pending file and a matching transcript."""
    MemoryStore.save_settings(Settings(auto_mode=mode))
    store = MemoryStore(root / "memory.db")
    brain = make_brain(store, domain)
    rows, events = [], []
    for i, p in enumerate(prompts):
        events += [_user(p), _assistant(f"assistant reply {i}")]
        rows.append({"prompt": p, "session_id": session, "timestamp": f"2026-11-17T09:{i % 60:02d}:00"})
    (root / "pending.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    write_transcript(root / "transcripts", session, events)
    return store, brain


def run(root, completer, **kw):
    with mock.patch.dict(os.environ, {"MELDWERKES_TRANSCRIPTS": str(root / "transcripts")}):
        return auto.run_once(root / "memory.db", completer, now=NOW, **kw)


class RunOnceTests(unittest.TestCase):
    def test_run_once_end_to_end(self):
        with temp_data_dir() as root:
            store, brain = make_env(root, ["no, use backoff", "keep it short", "run the tests"])
            reply = json.dumps([item(1, "correction", principle="prefer backoff"),
                                item(2, "directive", principle="keep it short"), item(3)])
            res = run(root, StubCompleter([reply]))
            self.assertEqual(res["status"], "ok")
            self.assertEqual(len(store.get_decisions(brain.id)), 2)
            self.assertEqual(auto.load_cursor(), (root / "pending.jsonl").stat().st_size)
            log = (root / "logs" / "auto-latest.log").read_text()
            self.assertIn(res["run_id"], log)
            last = store.last_run()
            self.assertEqual((last["run_id"], last["status"]), (res["run_id"], "ok"))
            self.assertIsNotNone(last["finished_at"])

    def test_checkpoint_exists_after_run_and_restores_prior_state(self):
        with temp_data_dir() as root:
            store, brain = make_env(root, ["no, use backoff"])
            res = run(root, StubCompleter([json.dumps([item(1, "correction", principle="p")])]))
            snaps = list((root / "checkpoints").glob("*pre-auto*"))
            self.assertEqual(len(snaps), 1)
            self.assertEqual(len(store.get_decisions(brain.id)), 1)
            memory.restore_checkpoint(snaps[0], root / "memory.db")
            self.assertEqual(len(MemoryStore(root / "memory.db").get_decisions(brain.id)), 0)

    def test_dry_run_writes_nothing_and_reports_batches_and_histogram(self):
        with temp_data_dir() as root:
            store, brain = make_env(root, [f"prompt {i}" for i in range(45)])
            c = StubCompleter([nones(20)])
            res = run(root, c, dry_run=True)
            self.assertTrue(res["dry_run"])
            self.assertEqual(res["batches"], math.ceil(45 / 20))
            self.assertEqual(res["histogram"], {"none": 20})
            self.assertEqual(len(c.prompts), 1)
            self.assertEqual(store.get_exchanges(), [])
            self.assertIsNone(store.last_run())
            self.assertFalse((root / "auto-cursor.json").exists())
            self.assertFalse((root / "checkpoints").exists())

    def test_run_does_nothing_when_auto_mode_off(self):
        with temp_data_dir() as root:
            store, brain = make_env(root, ["x"], mode="off")
            c = StubCompleter([nones(1)])
            res = run(root, c)
            self.assertEqual(res["status"], "disabled")
            self.assertEqual(c.prompts, [])
            self.assertEqual(store.get_exchanges(), [])

    def test_dry_run_works_while_auto_mode_is_off(self):
        # the skill tells people to preview BEFORE enabling, so the preview must work while off
        with temp_data_dir() as root:
            store, brain = make_env(root, ["a", "b", "c"], mode="off")
            c = StubCompleter([nones(3)])
            res = run(root, c, dry_run=True)
            self.assertTrue(res["dry_run"])
            self.assertEqual(res["histogram"], {"none": 3})
            self.assertEqual(len(c.prompts), 1)
            self.assertEqual(store.get_exchanges(), [])
            self.assertFalse((root / "auto-cursor.json").exists())

    def test_run_does_nothing_when_capture_disabled_mid_run(self):
        with temp_data_dir() as root:
            store, brain = make_env(root, ["no, use backoff"])

            class FlipsCapture(StubCompleter):
                def complete(self, prompt, max_tokens=4096):
                    MemoryStore.save_settings(Settings(auto_mode="propose", capture_enabled=False))
                    return super().complete(prompt, max_tokens)

            res = run(root, FlipsCapture([json.dumps([item(1, "correction", principle="p")])]))
            self.assertEqual(res["status"], "capture-off")
            self.assertEqual(store.get_exchanges(), [])
            self.assertEqual(store.get_decisions(brain.id), [])
            self.assertEqual(auto.load_cursor(), 0)

    def test_failed_batch_leaves_cursor_before_it_and_next_run_retries(self):
        with temp_data_dir() as root:
            store, brain = make_env(root, [f"prompt {i}" for i in range(40)])
            rows, _ = auto.read_new(root / "pending.jsonl", 0)
            res1 = run(root, StubCompleter([nones(20), "garbage"]))
            self.assertEqual(res1["status"], "partial")
            self.assertEqual(auto.load_cursor(), rows[19]["_end"])
            self.assertEqual(len(store.get_exchanges()), 20)
            res2 = run(root, StubCompleter([nones(20)]))
            self.assertEqual(res2["status"], "ok")
            self.assertEqual(len(store.get_exchanges()), 40)
            self.assertEqual(auto.load_cursor(), (root / "pending.jsonl").stat().st_size)

    def test_second_concurrent_run_exits_without_writing(self):
        with temp_data_dir() as root:
            store, brain = make_env(root, ["x"])
            held = auto.RunLock()
            self.assertTrue(held.acquire())
            try:
                c = StubCompleter([nones(1)])
                res = run(root, c)
            finally:
                held.release()
            self.assertEqual(res["status"], "locked")
            self.assertEqual(c.prompts, [])
            self.assertEqual(store.get_exchanges(), [])

    def test_run_sets_internal_env_for_model_calls_and_restores_it(self):
        with temp_data_dir() as root:
            store, brain = make_env(root, ["x"])
            seen = []

            class Spy(StubCompleter):
                def complete(self, prompt, max_tokens=4096):
                    seen.append(os.environ.get("MELDWERKES_INTERNAL"))
                    return super().complete(prompt, max_tokens)

            before = os.environ.get("MELDWERKES_INTERNAL")
            run(root, Spy([nones(1)]))
            self.assertEqual(seen, ["1"])
            self.assertEqual(os.environ.get("MELDWERKES_INTERNAL"), before)

    def test_log_and_status_contain_no_prompt_text(self):
        with temp_data_dir() as root:
            store, brain = make_env(root, ["zebra-unique-token-123 please"])
            run(root, StubCompleter([nones(1)]))
            log = (root / "logs" / "auto-latest.log").read_text()
            with mock.patch.dict(os.environ, {"MELDWERKES_TRANSCRIPTS": str(root / "transcripts")}):
                text = auto.status_text(store, now=NOW)
            self.assertNotIn("zebra-unique", log)
            self.assertNotIn("zebra-unique", text)

    def test_status_reports_backlog_last_run_pending_proposals(self):
        with temp_data_dir() as root:
            store, brain = make_env(root, [f"p{i}" for i in range(45)])
            text = auto.status_text(store, now=NOW)
            self.assertIn("backlog: 45", text)
            self.assertIn("auto_mode: propose", text)
            self.assertIn("last run: none", text)
            run(root, StubCompleter([nones(20)] * 3))
            text = auto.status_text(store, now=NOW)
            self.assertIn("backlog: 0", text)
            self.assertIn("proposals awaiting review: 0", text)
            self.assertNotIn("last run: none", text)


def write_pending(root, rows):
    (root / "pending.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    return rows


def dead_row(i, session="gone", ts="2026-10-01T09:00:00"):
    return {"prompt": f"old prompt {i}", "session_id": session, "timestamp": ts}


class ExpiredRowTests(unittest.TestCase):
    """Rows whose session transcript is gone can never pair, so they can never
    produce a decision (an unpaired exchange is capped below min_confidence).
    They must be skipped without model calls instead of eating the run."""

    def test_rows_without_transcript_are_skipped_without_model_calls(self):
        with temp_data_dir() as root:
            store, brain = make_env(root, ["x"])
            write_pending(root, [dead_row(i) for i in range(3)])
            c = StubCompleter([nones(3)])
            res = run(root, c)
            self.assertEqual(res["status"], "idle")
            self.assertEqual(res["expired"], 3)
            self.assertEqual(c.prompts, [])
            self.assertEqual(store.get_exchanges(), [])
            self.assertEqual(auto.load_cursor(), (root / "pending.jsonl").stat().st_size)
            self.assertIn("expired=3", (root / "logs" / "auto-latest.log").read_text())

    def test_expired_rows_do_not_block_live_rows_behind_them(self):
        with temp_data_dir() as root:
            store, brain = make_env(root, ["keep it short", "run the tests"])
            live = [json.loads(l) for l in (root / "pending.jsonl").read_text().splitlines()]
            write_pending(root, [dead_row(i) for i in range(30)] + live)
            c = StubCompleter([nones(2)])
            res = run(root, c)
            self.assertEqual(res["status"], "ok")
            self.assertEqual(len(c.prompts), 1)              # one batch: only the live rows
            self.assertEqual(len(store.get_exchanges()), 2)
            self.assertEqual(res["counts"].expired, 30)
            self.assertEqual(auto.load_cursor(), (root / "pending.jsonl").stat().st_size)

    def test_recent_row_without_transcript_is_kept_for_now(self):
        # inside the grace period a missing transcript may just be a session that is
        # still starting; it is processed (as unpaired), not dropped
        with temp_data_dir() as root:
            store, brain = make_env(root, ["x"])
            write_pending(root, [dead_row(0, ts="2026-11-17T09:00:00")])
            c = StubCompleter([nones(1)])
            res = run(root, c)
            self.assertEqual(res["counts"].expired, 0)
            self.assertEqual(len(c.prompts), 1)
            self.assertEqual(res["counts"].unpaired, 1)

    def test_log_reports_unpaired_count(self):
        with temp_data_dir() as root:
            store, brain = make_env(root, ["x"])
            write_pending(root, [dead_row(0, ts="2026-11-17T09:00:00")])
            run(root, StubCompleter([nones(1)]))
            self.assertIn("unpaired=1", (root / "logs" / "auto-latest.log").read_text())

    def test_dry_run_reports_expired_and_writes_nothing(self):
        with temp_data_dir() as root:
            store, brain = make_env(root, ["keep it short"])
            live = [json.loads(l) for l in (root / "pending.jsonl").read_text().splitlines()]
            write_pending(root, [dead_row(i) for i in range(5)] + live)
            c = StubCompleter([nones(1)])
            res = run(root, c, dry_run=True)
            self.assertTrue(res["dry_run"])
            self.assertEqual(res["rows"], 1)
            self.assertEqual(res["expired"], 5)
            self.assertEqual(res["histogram"], {"none": 1})
            self.assertFalse((root / "auto-cursor.json").exists())

    def test_partial_run_cursor_stays_before_unprocessed_live_rows(self):
        with temp_data_dir() as root:
            store, brain = make_env(root, [f"prompt {i}" for i in range(40)])
            live = [json.loads(l) for l in (root / "pending.jsonl").read_text().splitlines()]
            write_pending(root, [dead_row(i) for i in range(10)] + live)
            rows, _ = auto.read_new(root / "pending.jsonl", 0)
            res = run(root, StubCompleter([nones(20), "garbage"]))
            self.assertEqual(res["status"], "partial")
            self.assertEqual(auto.load_cursor(), rows[10 + 19]["_end"])   # after the 20th live row
            res2 = run(root, StubCompleter([nones(20)]))
            self.assertEqual(res2["status"], "ok")
            self.assertEqual(len(store.get_exchanges()), 40)


class NothingWrittenWarningTests(unittest.TestCase):
    """A run that finds durable preferences but writes no decisions is not a quiet
    success: it must say so in the result, the log and the status."""

    def _unpaired_correction_run(self, root):
        make_env(root, ["x"])
        write_pending(root, [dead_row(0, ts="2026-11-17T09:00:00")])   # recent, no transcript
        reply = json.dumps([item(1, "correction", principle="p", confidence=0.95)])
        return run(root, StubCompleter([reply]))

    def test_warns_when_durable_items_found_but_no_decision_written(self):
        with temp_data_dir() as root:
            res = self._unpaired_correction_run(root)
            self.assertEqual(res["counts"].decisions, 0)
            self.assertEqual(res["warn"], "nothing-written")
            self.assertIn("warn=nothing-written", (root / "logs" / "auto-latest.log").read_text())

    def test_no_warning_when_a_decision_is_written(self):
        with temp_data_dir() as root:
            make_env(root, ["no, use backoff"])
            res = run(root, StubCompleter([json.dumps([item(1, "correction", principle="p")])]))
            self.assertEqual(res["counts"].decisions, 1)
            self.assertNotIn("warn", res)
            self.assertNotIn("warn=", (root / "logs" / "auto-latest.log").read_text())

    def test_no_warning_when_everything_is_none(self):
        with temp_data_dir() as root:
            make_env(root, ["run the tests"])
            res = run(root, StubCompleter([nones(1)]))
            self.assertNotIn("warn", res)

    def test_status_shows_the_warning_for_the_last_run(self):
        with temp_data_dir() as root:
            self._unpaired_correction_run(root)
            store = MemoryStore(root / "memory.db")
            text = auto.status_text(store, now=NOW)
            self.assertIn("warning:", text)
            self.assertIn("0 decisions", text)

    def test_status_has_no_warning_after_a_clean_run(self):
        with temp_data_dir() as root:
            store, _ = make_env(root, ["no, use backoff"])
            run(root, StubCompleter([json.dumps([item(1, "correction", principle="p")])]))
            self.assertNotIn("warning:", auto.status_text(store, now=NOW))


class RetractRunTests(unittest.TestCase):
    def test_retract_run_removes_only_that_runs_rows(self):
        with temp_data_dir() as root:
            store, brain = make_env(root, ["no, a", "no, b"])
            one = json.dumps([item(1, "correction", principle="pa")])
            # run A sees only the first prompt; run B the second
            (root / "pending.jsonl").write_text(json.dumps(
                {"prompt": "no, a", "session_id": "s1", "timestamp": "2026-11-17T09:00:00"}) + "\n")
            res_a = run(root, StubCompleter([one]))
            with open(root / "pending.jsonl", "a") as f:
                f.write(json.dumps({"prompt": "no, b", "session_id": "s1", "timestamp": "2026-11-17T09:01:00"}) + "\n")
            res_b = run(root, StubCompleter([json.dumps([item(1, "correction", principle="pb")])]))
            self.assertEqual(len(store.get_decisions(brain.id)), 2)
            counts = history.retract_run(store, res_a["run_id"])
            self.assertEqual(counts["decisions"], 1)
            left = store.get_decisions(brain.id)
            self.assertEqual(len(left), 1)
            self.assertIn(res_b["run_id"], left[0].context)
            self.assertEqual(len(store.get_corrections(brain.id)), 1)
            self.assertEqual([e["run_id"] for e in store.get_exchanges()], [res_b["run_id"]])


if __name__ == "__main__":
    unittest.main()
