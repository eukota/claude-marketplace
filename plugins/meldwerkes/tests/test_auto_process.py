import json
import unittest

from tests.helpers import temp_data_dir, make_brain, StubCompleter
import auto
from memory import MemoryStore


def ex(user, assistant="the assistant did X", paired=True, n=0, session="s1"):
    return auto.Exchange(f"2026-11-17T10:{n % 60:02d}:00", session, user, assistant, paired)


def item(n, kind="none", domain="code-review", principle=None, confidence=0.9):
    return {"n": n, "kind": kind, "domain": domain, "principle": principle, "confidence": confidence}


def reply(*items):
    return json.dumps(list(items))


def nones(count):
    return reply(*[item(i + 1) for i in range(count)])


def setup(root, domain="code-review"):
    store = MemoryStore(root / "memory.db")
    return store, make_brain(store, domain)


class ProcessTests(unittest.TestCase):
    def test_correction_writes_decision_and_correction_for_matching_mind(self):
        with temp_data_dir() as root:
            store, brain = setup(root)
            c = StubCompleter([reply(item(1, "correction", principle="prefer backoff over fixed retries"))])
            counts, handled = auto.process_exchanges(store, c, [ex("no, use backoff")], "run1")
            self.assertEqual(handled, 1)
            d = store.get_decisions(brain.id)
            self.assertEqual(len(d), 1)
            self.assertIs(d[0].confirmed, False)
            self.assertTrue(d[0].context.startswith("[auto run1]"))
            cors = store.get_corrections(brain.id)
            self.assertEqual(cors[0].principle_affected, "prefer backoff over fixed retries")
            self.assertEqual((counts.decisions, counts.corrections), (1, 1))

    def test_directive_writes_unconfirmed_decision(self):
        with temp_data_dir() as root:
            store, brain = setup(root)
            c = StubCompleter([reply(item(1, "directive", principle="keep functions small"))])
            auto.process_exchanges(store, c, [ex("keep functions small")], "r")
            d = store.get_decisions(brain.id)
            self.assertEqual(len(d), 1)
            self.assertIsNone(d[0].confirmed)
            self.assertEqual(store.get_corrections(brain.id), [])

    def test_none_writes_only_an_exchange_row(self):
        with temp_data_dir() as root:
            store, brain = setup(root)
            counts, _ = auto.process_exchanges(store, StubCompleter([nones(1)]), [ex("run the tests")], "r")
            self.assertEqual(store.get_decisions(brain.id), [])
            rows = store.get_exchanges()
            self.assertEqual([r["kind"] for r in rows], ["none"])
            self.assertEqual(counts.classified, {"none": 1})

    def test_domain_without_a_mind_is_stored_unrouted_and_creates_no_brain(self):
        with temp_data_dir() as root:
            store, _ = setup(root)
            c = StubCompleter([reply(item(1, "directive", domain="cooking", principle="salt early"))])
            counts, _ = auto.process_exchanges(store, c, [ex("salt early")], "r")
            self.assertEqual(counts.unrouted, 1)
            self.assertEqual(len(store.get_brains()), 1)
            row = store.get_exchanges()[0]
            self.assertIsNone(row["brain_id"])

    def test_below_min_confidence_is_not_a_decision_but_is_an_exchange(self):
        with temp_data_dir() as root:
            store, brain = setup(root)
            c = StubCompleter([reply(item(1, "correction", principle="p", confidence=0.4))])
            auto.process_exchanges(store, c, [ex("meh")], "r")
            self.assertEqual(store.get_decisions(brain.id), [])
            self.assertEqual(len(store.get_exchanges()), 1)

    def test_unpaired_exchange_confidence_capped_at_0_5(self):
        with temp_data_dir() as root:
            store, brain = setup(root)
            c = StubCompleter([reply(item(1, "correction", principle="p", confidence=0.9))])
            auto.process_exchanges(store, c, [ex("no", assistant="", paired=False)], "r")
            self.assertEqual(store.get_decisions(brain.id), [])
            row = store.get_exchanges()[0]
            self.assertLessEqual(row["confidence"], 0.5)
            self.assertEqual(row["paired"], 0)

    def test_secret_line_never_reaches_model_prompt_or_database(self):
        with temp_data_dir() as root:
            store, brain = setup(root)
            c = StubCompleter([nones(1)])
            text = "use this\npassword = hunter2hunter2hunter2\nthanks"
            counts, _ = auto.process_exchanges(store, c, [ex(text)], "r")
            self.assertEqual(counts.scrubbed, 1)
            self.assertTrue(all("hunter2" not in p for p in c.prompts))
            for row in store.get_exchanges():
                self.assertNotIn("hunter2", row["user"])
                self.assertNotIn("hunter2", row["assistant"])

    def test_internal_prompt_rows_are_dropped_and_counted(self):
        with temp_data_dir() as root:
            store, _ = setup(root)
            c = StubCompleter([nones(1)])
            rows = [ex("You are extracting durable preferences from a developer's chat history."),
                    ex("real prompt", n=1)]
            counts, handled = auto.process_exchanges(store, c, rows, "r")
            self.assertEqual((counts.internal, handled), (1, 2))
            self.assertEqual(len(store.get_exchanges()), 1)

    def test_unparseable_batch_counts_failed_and_stops_without_losing_earlier_batches(self):
        with temp_data_dir() as root:
            store, _ = setup(root)
            c = StubCompleter([nones(20), "this is not json", nones(20)])
            rows = [ex(f"prompt {i}", n=i) for i in range(60)]
            counts, handled = auto.process_exchanges(store, c, rows, "r")
            self.assertEqual(handled, 20)
            self.assertEqual(counts.failed_batches, 1)
            self.assertEqual(len(store.get_exchanges()), 20)

    def test_model_exception_is_a_failed_batch_not_a_crash(self):
        with temp_data_dir() as root:
            store, _ = setup(root)
            c = StubCompleter([RuntimeError("claude CLI failed")])
            counts, handled = auto.process_exchanges(store, c, [ex("x")], "r")
            self.assertEqual((handled, counts.failed_batches), (0, 1))

    def test_batch_cap_stops_at_10_batches(self):
        with temp_data_dir() as root:
            store, _ = setup(root)
            c = StubCompleter([nones(20)] * 10)
            rows = [ex(f"prompt {i}", n=i, session=f"s{i}") for i in range(250)]
            counts, handled = auto.process_exchanges(store, c, rows, "r", max_batches=10)
            self.assertEqual(handled, 200)
            self.assertEqual(len(c.prompts), 10)

    def test_every_written_id_is_recorded_as_a_run_item(self):
        with temp_data_dir() as root:
            store, brain = setup(root)
            c = StubCompleter([reply(item(1, "correction", principle="p"), item(2))])
            auto.process_exchanges(store, c, [ex("fix it"), ex("ok", n=1)], "runX")
            kinds = [k for k, _ in store.get_run_items("runX")]
            self.assertEqual(sorted(kinds), ["correction", "decision", "exchange", "exchange"])

    def test_reprocessing_the_same_exchange_does_not_duplicate(self):
        with temp_data_dir() as root:
            store, brain = setup(root)
            rows = [ex("no, use backoff")]
            c1 = StubCompleter([reply(item(1, "correction", principle="p"))])
            auto.process_exchanges(store, c1, rows, "r1")
            c2 = StubCompleter([])  # a second run must not even call the model for it
            counts, handled = auto.process_exchanges(store, c2, rows, "r2")
            self.assertEqual(handled, 1)
            self.assertEqual(len(store.get_decisions(brain.id)), 1)
            self.assertEqual(len(store.get_exchanges()), 1)
            self.assertEqual(c2.prompts, [])


if __name__ == "__main__":
    unittest.main()
