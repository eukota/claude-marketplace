import json
import unittest
from pathlib import Path

from tests.helpers import temp_data_dir
import auto


def _user(text, prompt=True):
    d = {"type": "user", "message": {"content": text}}
    if prompt:
        d["promptSource"] = "typed"
    return d


def _assistant(text):
    return {"type": "assistant", "message": {"content": [{"type": "text", "text": text}]}}


def _write(root: Path, session, events, project="proj"):
    d = root / project
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{session}.jsonl").write_text("\n".join(json.dumps(e) for e in events) + "\n")


def _row(prompt, session="s1", ts="2026-11-17T10:00:00"):
    return {"prompt": prompt, "session_id": session, "timestamp": ts}


class PairingTests(unittest.TestCase):
    def test_pairs_prompt_with_preceding_assistant_text(self):
        with temp_data_dir() as root:
            _write(root, "s1", [_user("hello"), _assistant("I added a retry"), _user("no, use backoff")])
            out = auto.pair_with_transcripts([_row("no, use backoff")], root)
            self.assertEqual(len(out), 1)
            self.assertTrue(out[0].paired)
            self.assertEqual(out[0].assistant, "I added a retry")
            self.assertEqual(out[0].user, "no, use backoff")

    def test_first_prompt_of_session_has_empty_assistant_but_is_paired(self):
        with temp_data_dir() as root:
            _write(root, "s1", [_user("start here"), _assistant("ok")])
            out = auto.pair_with_transcripts([_row("start here")], root)
            self.assertTrue(out[0].paired)
            self.assertEqual(out[0].assistant, "")

    def test_missing_transcript_gives_unpaired_exchange(self):
        with temp_data_dir() as root:
            out = auto.pair_with_transcripts([_row("orphan", session="nope")], root)
            self.assertEqual(len(out), 1)
            self.assertFalse(out[0].paired)
            self.assertEqual(out[0].assistant, "")

    def test_prompt_longer_than_recorded_limit_still_matches(self):
        with temp_data_dir() as root:
            long = "x" * 4000 + " and then a tail that the hook never recorded"
            _write(root, "s1", [_user("a"), _assistant("A1"), _user(long)])
            out = auto.pair_with_transcripts([_row(long[:4000])], root)
            self.assertTrue(out[0].paired)
            self.assertEqual(out[0].assistant, "A1")

    def test_two_identical_prompts_pair_in_order(self):
        with temp_data_dir() as root:
            _write(root, "s1", [_user("again"), _assistant("first reply"),
                                _user("again"), _assistant("second reply"), _user("end")])
            out = auto.pair_with_transcripts([_row("again"), _row("again")], root)
            self.assertEqual([o.assistant for o in out], ["", "first reply"])

    def test_tool_result_turns_are_not_user_prompts(self):
        with temp_data_dir() as root:
            _write(root, "s1", [_user("go"), _assistant("running tool"),
                                _user("tool output here", prompt=False), _assistant("done"),
                                _user("thanks")])
            out = auto.pair_with_transcripts([_row("thanks")], root)
            self.assertEqual(out[0].assistant, "done")


if __name__ == "__main__":
    unittest.main()
