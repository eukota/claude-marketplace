import json
import os
import unittest
import uuid
from datetime import datetime

from tests.helpers import temp_data_dir, make_brain, StubCompleter
import auto
import memory
import review
from memory import MemoryStore, Decision, Principle, Correction, Proposal

NOW = datetime(2026, 11, 17, 12, 0, 0)


def add_decisions(store, brain, timestamps, text="decision"):
    ids = []
    for i, ts in enumerate(timestamps):
        d = Decision(id=str(uuid.uuid4()), brain_id=brain.id, timestamp=ts,
                     context=f"ctx {i}", decision=f"{text} {i}", grounding="none")
        store.save_decision(d)
        ids.append(d.id)
    return ids


def add_principle(store, brain, ts, text="old principle"):
    store.save_principle(Principle(id=str(uuid.uuid4()), brain_id=brain.id, timestamp=ts,
                                   principle=text, confidence=0.8))


def principles_reply(*texts):
    return json.dumps({"principles": [
        {"principle": t, "supporting_decisions": [], "conflicting_decisions": [], "confidence": 0.8}
        for t in texts]})


class DueTests(unittest.TestCase):
    def test_due_when_5_new_items_since_last_distillation(self):
        with temp_data_dir() as root:
            store = MemoryStore(root / "memory.db"); b = make_brain(store, "writing")
            add_principle(store, b, "2026-11-16T00:00:00")
            add_decisions(store, b, ["2026-11-17T01:00:00"] * 4)
            self.assertFalse(auto.due_for_distill(store, b.id, NOW))
            add_decisions(store, b, ["2026-11-17T02:00:00"])
            self.assertTrue(auto.due_for_distill(store, b.id, NOW))

    def test_due_after_14_days_with_any_new_item(self):
        with temp_data_dir() as root:
            store = MemoryStore(root / "memory.db"); b = make_brain(store, "writing")
            add_principle(store, b, "2026-11-01T00:00:00")
            add_decisions(store, b, ["2026-11-10T00:00:00"])
            self.assertTrue(auto.due_for_distill(store, b.id, NOW))

    def test_not_due_with_nothing_new(self):
        with temp_data_dir() as root:
            store = MemoryStore(root / "memory.db"); b = make_brain(store, "writing")
            add_decisions(store, b, ["2026-10-01T00:00:00"] * 8)
            add_principle(store, b, "2026-11-01T00:00:00")
            self.assertFalse(auto.due_for_distill(store, b.id, NOW))

    def test_never_distilled_needs_5_items(self):
        with temp_data_dir() as root:
            store = MemoryStore(root / "memory.db"); b = make_brain(store, "writing")
            add_decisions(store, b, ["2026-11-01T00:00:00"])
            self.assertFalse(auto.due_for_distill(store, b.id, NOW))


class DistillTests(unittest.TestCase):
    def test_propose_mode_creates_proposals_and_no_principles(self):
        with temp_data_dir() as root:
            store = MemoryStore(root / "memory.db"); b = make_brain(store, "writing")
            add_decisions(store, b, ["2026-11-17T01:00:00"] * 5)
            c = StubCompleter([principles_reply("be brief", "cite sources")])
            props = auto.distill(store, c, b.id, "r1", "propose", now=NOW)
            self.assertEqual(len(props), 2)
            self.assertEqual(store.get_principles(b.id), [])
            self.assertEqual({p.payload["principle"] for p in store.get_proposals()}, {"be brief", "cite sources"})
            self.assertEqual(sorted(k for k, _ in store.get_run_items("r1")), ["proposal", "proposal"])

    def test_apply_mode_saves_principles_directly_after_checkpoint(self):
        with temp_data_dir() as root:
            store = MemoryStore(root / "memory.db"); b = make_brain(store, "writing")
            add_decisions(store, b, ["2026-11-17T01:00:00"] * 5)
            c = StubCompleter([principles_reply("be brief")])
            auto.distill(store, c, b.id, "r1", "apply", now=NOW)
            self.assertEqual([p.principle for p in store.get_principles(b.id)], ["be brief"])
            self.assertTrue(list((root / "checkpoints").glob("*pre-apply*")))
            self.assertEqual(store.get_proposals(), [])

    def test_exclude_ids_keep_held_out_decisions_out_of_the_prompt(self):
        with temp_data_dir() as root:
            store = MemoryStore(root / "memory.db"); b = make_brain(store, "writing")
            ids = add_decisions(store, b, ["2026-11-17T01:00:00"] * 3, text="secretly-held-out")
            keep = add_decisions(store, b, ["2026-11-17T02:00:00"], text="visible")
            c = StubCompleter([principles_reply("p")])
            auto.distill(store, c, b.id, "r1", "propose", exclude_ids=frozenset(ids), now=NOW)
            self.assertNotIn("secretly-held-out", c.prompts[0])
            self.assertIn("visible", c.prompts[0])

    def test_distill_also_proposes_meta_principles_when_conflicts_exist(self):
        with temp_data_dir() as root:
            store = MemoryStore(root / "memory.db"); b = make_brain(store, "writing")
            ids = add_decisions(store, b, ["2026-11-17T01:00:00"] * 5)
            add_principle(store, b, "2026-11-01T00:00:00", "p1")
            add_principle(store, b, "2026-11-01T00:00:00", "p2")
            store.save_correction(Correction(id="c1", decision_id=ids[0], brain_id=b.id,
                                             timestamp="2026-11-17T01:00:00", user_feedback="f",
                                             principle_affected="p1", new_weighting="p1 over p2"))
            meta = json.dumps({"meta_principles": [{"principle_a": "p1", "principle_b": "p2",
                                                    "weighting": "p1 > p2 when rushed", "context": "writing"}]})
            c = StubCompleter([principles_reply("new one"), meta])
            auto.distill(store, c, b.id, "r1", "propose", now=NOW)
            self.assertEqual(sorted(p.kind for p in store.get_proposals()), ["meta", "principle"])


class ReviewProposalTests(unittest.TestCase):
    def _proposal(self, store, brain, text="be brief", kind="principle", pid=None):
        payload = ({"principle": text, "confidence": 0.8, "supporting_decisions": [], "conflicting_decisions": []}
                   if kind == "principle" else
                   {"principle_a": "a", "principle_b": "b", "weighting": "a > b", "context": "writing"})
        p = Proposal(id=pid or str(uuid.uuid4()), brain_id=brain.id, kind=kind, payload=payload,
                     status="proposed", run_id="r1", created_at="2026-11-17T00:00:00")
        store.save_proposal(p)
        return p

    def test_accept_moves_proposal_to_principles_and_rewrites_session_context(self):
        with temp_data_dir() as root:
            store = MemoryStore(root / "memory.db"); b = make_brain(store, "writing")
            p = self._proposal(store, b)
            review.accept_proposal(store, p)
            self.assertEqual([x.principle for x in store.get_principles(b.id)], ["be brief"])
            self.assertEqual(store.get_proposals(), [])
            self.assertIn("be brief", memory.SESSION_CONTEXT_FILE.read_text())

    def test_reject_marks_rejected_and_writes_no_principle(self):
        with temp_data_dir() as root:
            store = MemoryStore(root / "memory.db"); b = make_brain(store, "writing")
            p = self._proposal(store, b)
            review.reject_proposal(store, p)
            self.assertEqual(store.get_principles(b.id), [])
            self.assertEqual([x.id for x in store.get_proposals(status="rejected")], [p.id])

    def test_accept_by_prefix_ambiguous_id_exits_with_message(self):
        with temp_data_dir() as root:
            store = MemoryStore(root / "memory.db"); b = make_brain(store, "writing")
            self._proposal(store, b, pid="abc11111")
            self._proposal(store, b, pid="abc22222")
            with self.assertRaises(SystemExit) as cm:
                review.find_proposal(store, "abc")
            self.assertIn("Ambiguous", str(cm.exception))
            self.assertEqual(review.find_proposal(store, "abc111").id, "abc11111")

    def test_meta_proposal_accept_saves_meta_principle(self):
        with temp_data_dir() as root:
            store = MemoryStore(root / "memory.db"); b = make_brain(store, "writing")
            p = self._proposal(store, b, kind="meta")
            review.accept_proposal(store, p)
            metas = store.get_meta_principles(b.id)
            self.assertEqual([(m.principle_a, m.weighting) for m in metas], [("a", "a > b")])


if __name__ == "__main__":
    unittest.main()
