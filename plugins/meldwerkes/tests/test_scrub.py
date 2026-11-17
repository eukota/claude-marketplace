import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.helpers import SCRIPTS  # noqa: F401  (puts scripts/ on sys.path)
import scrub

HOOK = Path(__file__).resolve().parent.parent / "hooks" / "capture_prompt.py"

SECRETS = [
    "DB_PASSWORD=hunter2hunter2hunter2",
    '"password": "hunter2hunter2hunter2"',
    "client_secret = abcdefgh12345678",
    "GITHUB_TOKEN=abcdefgh12345678",
    "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9abc",
    "-----BEGIN OPENSSH PRIVATE KEY-----",
    "AKIAABCDEFGHIJKLMNOP",
    "xoxb-1234567890-abcdefghij",
]
SAFE = [
    "password: change-me",
    "token: <paste here>",
    "treated the token as optional (if req.token:)",
    "${CTX_PASSWORD}",
]


class ScrubTests(unittest.TestCase):
    def test_credential_shapes_are_dropped(self):
        for line in SECRETS:
            clean, n = scrub.scrub(f"before\n{line}\nafter")
            self.assertEqual((clean, n), ("before\nafter", 1), line)

    def test_placeholders_and_prose_survive(self):
        for line in SAFE:
            clean, n = scrub.scrub(line)
            self.assertEqual((clean, n), (line, 0), line)

    def test_scrub_keeps_other_lines_and_reports_count(self):
        text = "keep one\nDB_PASSWORD=hunter2hunter2hunter2\nkeep two\nAKIAABCDEFGHIJKLMNOP"
        clean, n = scrub.scrub(text)
        self.assertEqual(clean, "keep one\nkeep two")
        self.assertEqual(n, 2)

    def test_secret_value_absent_from_output(self):
        clean, _ = scrub.scrub("x\npassword = hunter2hunter2hunter2\ny")
        self.assertNotIn("hunter2", clean)

    def test_internal_prompt_headers_detected(self):
        for head in ("You are extracting durable preferences from a developer's chat history.",
                     "Analyze this decision log and extract key principles.",
                     "Analyze principle conflicts and extract meta-principles."):
            self.assertTrue(scrub.is_internal_prompt(head + "\nmore"))
        self.assertFalse(scrub.is_internal_prompt("please analyze this decision log"))
        self.assertEqual(scrub.INTERNAL_ENV, "MELDWERKES_INTERNAL")


def _run_hook(extra_env):
    with tempfile.TemporaryDirectory() as home:
        env = {**os.environ, "HOME": home, **extra_env}
        env.pop("MELDWERKES_INTERNAL", None) if "MELDWERKES_INTERNAL" not in extra_env else None
        payload = json.dumps({"prompt": "please use tabs", "session_id": "s1", "cwd": "/x"})
        proc = subprocess.run([sys.executable, str(HOOK)], input=payload, text=True,
                              capture_output=True, env=env, timeout=20)
        pending = Path(home) / ".small-brain" / "pending.jsonl"
        rows = pending.read_text().splitlines() if pending.exists() else []
        return proc.returncode, rows


class CaptureHookGuardTests(unittest.TestCase):
    def test_capture_hook_records_nothing_when_internal_env_set(self):
        code, rows = _run_hook({"MELDWERKES_INTERNAL": "1"})
        self.assertEqual(code, 0)
        self.assertEqual(rows, [])

    def test_capture_hook_still_records_normally(self):
        code, rows = _run_hook({})
        self.assertEqual(code, 0)
        self.assertEqual(len(rows), 1)
        self.assertEqual(json.loads(rows[0])["prompt"], "please use tabs")


if __name__ == "__main__":
    unittest.main()
