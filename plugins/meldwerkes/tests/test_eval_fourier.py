import io
import json
import os
import re
import unittest
import uuid
from contextlib import redirect_stdout
from unittest import mock

from tests.helpers import temp_data_dir, make_brain, StubCompleter
from tests.test_heldout import add_ex
import calibrate
import eval_fourier
import heldout
import memory
import report
from memory import MemoryStore, Decision, Principle

PRINCIPLES_JSON = json.dumps({"principles": [
    {"principle": "pooled principle one", "supporting_decisions": [], "conflicting_decisions": [], "confidence": 0.8}]})


class Responder(StubCompleter):
    """Answers distillation prompts with principles and predictions by assistant marker."""

    def __init__(self, predict=None):
        super().__init__()
        self.predict = predict or (lambda prompt: "7" if "ACT-C" in prompt else "1")

    def complete(self, prompt, max_tokens=4096):
        self.prompts.append(prompt)
        if prompt.startswith("Analyze this decision log"):
            return PRINCIPLES_JSON
        return self.predict(prompt)


def result_with(pooled_rs, multi_rs, n=50, corrections=10):
    return {"n": n, "corrections": corrections,
            "arms": {"pooled": {"rs": pooled_rs}, "multi": {"rs": multi_rs}}}


class ScoreAndVerdictTests(unittest.TestCase):
    def test_score_items_matches_calibrate_pearson_on_known_data(self):
        pred = [1, 2, 3, 4, 7, 2]
        act = [1, 2, 4, 4, 6, 1]
        items = [{"predicted": p, "actual": a, "confidence": 0.5} for p, a in zip(pred, act)]
        got = eval_fourier.score_items(items)
        self.assertAlmostEqual(got["r"], calibrate.pearson([float(x) for x in pred], [float(x) for x in act]))
        self.assertEqual(got["n"], 6)
        self.assertAlmostEqual(got["mae"], sum(abs(p - a) for p, a in zip(pred, act)) / 6)

    def test_verdict_insufficient_data_below_30_items_or_5_corrections(self):
        self.assertEqual(eval_fourier.verdict(result_with([.3], [.9], n=29)), "insufficient data")
        self.assertEqual(eval_fourier.verdict(result_with([.3], [.9], corrections=4)), "insufficient data")

    def test_verdict_multi_mind_only_when_margin_exceeds_noise(self):
        self.assertEqual(eval_fourier.verdict(result_with([.30, .32, .35], [.55, .52, .50])), "multi-mind")
        self.assertTrue(eval_fourier.verdict(result_with([.30, .32, .35], [.34, .36, .38])).startswith("tie"))
        self.assertTrue(eval_fourier.verdict(result_with([.5, .5, .5], [.2, .2, .2])).startswith("tie"))

    def test_undefined_r_counts_as_zero_not_a_crash(self):
        self.assertEqual(eval_fourier.verdict(result_with([None, None], [0.4, 0.4])), "multi-mind")


class PredictTests(unittest.TestCase):
    EX = {"assistant": "did the thing", "id": "e1", "kind": "none"}

    def test_predict_parses_a_1_to_7_integer_and_rejects_out_of_range(self):
        for raw, want in (("5", 5), ("The answer is 6.", 6), (" 1\n", 1)):
            self.assertEqual(eval_fourier.predict(StubCompleter([raw]), "- p", self.EX), want)
        for raw in ("9", "0", "12", "no idea"):
            with self.assertRaises(ValueError):
                eval_fourier.predict(StubCompleter([raw]), "- p", self.EX)


class ArmTests(unittest.TestCase):
    def test_render_arms_differ_in_structure(self):
        flat = eval_fourier.render_arm("pooled", ["a", "b"])
        grouped = eval_fourier.render_arm("multi", {
            "minds": [{"name": "Writing", "domain": "writing", "principles": ["a"]},
                      {"name": "Code", "domain": "code-review", "principles": ["b"]}],
            "metas": ["a > b when rushed"]})
        self.assertNotIn("Writing", flat)
        self.assertIn("Writing", grouped)
        self.assertIn("a > b when rushed", grouped)

    def test_pooled_arm_never_sees_held_out_decisions(self):
        with temp_data_dir() as root:
            store = MemoryStore(root / "memory.db")
            a, b = make_brain(store, "writing"), make_brain(store, "code-review")
            held = []
            for i in range(3):
                d = Decision(id=f"h{i}", brain_id=a.id, timestamp=f"2026-11-0{i+1}T00:00:00",
                             context="c", decision=f"held-marker {i}", grounding="none")
                store.save_decision(d)
                held.append(d.id)
            for i in range(3):
                store.save_decision(Decision(id=f"k{i}", brain_id=b.id, timestamp=f"2026-11-1{i}T00:00:00",
                                             context="c", decision=f"kept-marker {i}", grounding="none"))
            c = Responder()
            out = eval_fourier.build_pooled_principles(store, c, frozenset(held))
            self.assertEqual(out, ["pooled principle one"])
            self.assertNotIn("held-marker", c.prompts[0])
            self.assertIn("kept-marker", c.prompts[0])


def _seed_heldout(root, n_corr=8, n_none=22):
    store = MemoryStore(root / "memory.db")
    brain = make_brain(store, "writing")
    store.save_principle(Principle(id="p1", brain_id=brain.id, timestamp="2026-11-01T00:00:00",
                                   principle="live mind principle", confidence=0.8))
    for i in range(4):
        store.save_decision(Decision(id=f"d{i}", brain_id=brain.id, timestamp="2026-10-01T00:00:00",
                                     context="c", decision=f"training decision {i}", grounding="none"))
    for i in range(n_corr + n_none):
        kind = "correction" if i < n_corr else "none"
        add_ex(store, i, kind=kind, brain_id=brain.id)
    with __import__("sqlite3").connect(root / "memory.db") as c:
        for i in range(n_corr + n_none):
            marker = "ACT-C" if i < n_corr else "ACT-N"
            c.execute("update exchanges set assistant = ? where id = ?", (f"{marker}-{i}", f"e{i:03d}"))
    heldout.create(store, frac=1.0, min_items=n_corr + n_none)
    return store, brain


class ExperimentTests(unittest.TestCase):
    def test_arms_use_identical_template_and_differ_only_in_rendered_principles(self):
        with temp_data_dir() as root:
            store, _ = _seed_heldout(root)
            c = Responder()
            eval_fourier.run_experiment(store, c, repeats=1)
            preds = [p for p in c.prompts if not p.startswith("Analyze this decision log")]
            self.assertEqual(len(preds), 2 * 30)
            block = re.compile(r"BELIEFS:\n.*?\nEND BELIEFS", re.S)
            stripped = [block.sub("BELIEFS:X", p) for p in preds]
            half = len(preds) // 2
            self.assertEqual(stripped[:half], stripped[half:])
            self.assertNotEqual(preds[:half], preds[half:])

    def test_run_experiment_with_stub_writes_logs_and_results_file(self):
        with temp_data_dir() as root:
            store, _ = _seed_heldout(root)
            result = eval_fourier.run_experiment(store, Responder(), repeats=2)
            self.assertEqual(result["n"], 30)
            self.assertEqual(len(result["arms"]["pooled"]["rs"]), 2)
            self.assertAlmostEqual(result["arms"]["multi"]["mean_r"], 1.0)
            self.assertTrue(result["verdict"].startswith("tie"))  # identical perfect predictors
            saved = json.loads((root / "eval-results.json").read_text())
            self.assertEqual(saved["verdict"], result["verdict"])
            log = (root / "logs" / "eval-latest.log").read_text()
            self.assertIn("verdict", log)
            self.assertIn("proxy", log)

    def test_unparseable_prediction_skips_the_item_not_the_run(self):
        with temp_data_dir() as root:
            store, _ = _seed_heldout(root)
            seen = {"n": 0}

            def flaky(prompt):
                seen["n"] += 1
                if seen["n"] == 3:
                    return "no idea"
                return "7" if "ACT-C" in prompt else "1"

            result = eval_fourier.run_experiment(store, Responder(flaky), repeats=1)
            self.assertEqual(result["arms"]["pooled"]["skipped"] + result["arms"]["multi"]["skipped"], 1)

    def test_insufficient_held_out_data_is_reported_not_scored(self):
        with temp_data_dir() as root:
            store, _ = _seed_heldout(root, n_corr=2, n_none=10)
            c = Responder()
            result = eval_fourier.run_experiment(store, c, repeats=1)
            self.assertEqual(result["verdict"], "insufficient data")
            self.assertEqual(c.prompts, [])

    def test_report_prints_warning_when_multi_does_not_beat_pooled(self):
        with temp_data_dir() as root:
            MemoryStore(root / "memory.db")
            (root / "eval-results.json").write_text(json.dumps(
                {"date": "2026-11-17T00:00:00", "verdict": "tie: keep the simpler structure"}))
            buf = io.StringIO()
            with mock.patch("sys.argv", ["report.py", "--db", str(root / "memory.db")]), redirect_stdout(buf):
                report.main()
            self.assertIn("did not beat pooled", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
