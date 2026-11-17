import json
import subprocess
import unittest
from datetime import datetime, timedelta
from pathlib import Path

from tests.helpers import temp_data_dir
import auto


def _line(prompt, **extra):
    return json.dumps({"prompt": prompt, "session_id": "s", **extra}) + "\n"


class ReadNewTests(unittest.TestCase):
    def test_read_new_returns_rows_after_offset(self):
        with temp_data_dir() as root:
            f = root / "pending.jsonl"
            f.write_text(_line("one") + _line("two") + _line("three"))
            rows, off = auto.read_new(f, 0)
            self.assertEqual([r["prompt"] for r in rows], ["one", "two", "three"])
            self.assertEqual(off, f.stat().st_size)
            first_len = len(_line("one").encode())
            rows, _ = auto.read_new(f, first_len)
            self.assertEqual([r["prompt"] for r in rows], ["two", "three"])

    def test_incomplete_last_line_is_left_for_next_time(self):
        with temp_data_dir() as root:
            f = root / "pending.jsonl"
            f.write_text(_line("one") + '{"prompt": "half wri')
            rows, off = auto.read_new(f, 0)
            self.assertEqual([r["prompt"] for r in rows], ["one"])
            self.assertEqual(off, len(_line("one").encode()))
            f.write_text(_line("one") + _line("half written"))
            rows, off2 = auto.read_new(f, off)
            self.assertEqual([r["prompt"] for r in rows], ["half written"])
            self.assertEqual(off2, f.stat().st_size)

    def test_invalid_json_line_is_skipped_and_offset_advances(self):
        with temp_data_dir() as root:
            f = root / "pending.jsonl"
            f.write_text(_line("a") + "not json\n" + _line("b"))
            rows, off = auto.read_new(f, 0)
            self.assertEqual([r["prompt"] for r in rows], ["a", "b"])
            self.assertEqual(off, f.stat().st_size)

    def test_empty_or_missing_file_returns_nothing(self):
        with temp_data_dir() as root:
            self.assertEqual(auto.read_new(root / "nope.jsonl", 0), ([], 0))
            f = root / "pending.jsonl"
            f.write_text("")
            self.assertEqual(auto.read_new(f, 0), ([], 0))

    def test_offset_beyond_file_size_restarts_from_zero(self):
        with temp_data_dir() as root:
            f = root / "pending.jsonl"
            f.write_text(_line("x"))
            rows, off = auto.read_new(f, 10_000)
            self.assertEqual([r["prompt"] for r in rows], ["x"])

    def test_cursor_roundtrip_and_corrupt_cursor_is_zero(self):
        with temp_data_dir() as root:
            self.assertEqual(auto.load_cursor(), 0)
            auto.save_cursor(123)
            self.assertEqual(auto.load_cursor(), 123)
            (root / "auto-cursor.json").write_text("garbage")
            self.assertEqual(auto.load_cursor(), 0)


class ShouldRunTests(unittest.TestCase):
    NOW = datetime(2026, 11, 17, 12, 0, 0)

    def ago(self, hours):
        return (self.NOW - timedelta(hours=hours)).isoformat()

    def test_should_run_requires_20_rows_and_6_hours(self):
        self.assertFalse(auto.should_run(19, self.ago(10), self.NOW))
        self.assertFalse(auto.should_run(20, self.ago(5), self.NOW))
        self.assertTrue(auto.should_run(20, self.ago(6), self.NOW))
        self.assertTrue(auto.should_run(20, None, self.NOW))

    def test_fallback_runs_after_24h_even_with_few_rows(self):
        self.assertTrue(auto.should_run(3, self.ago(25), self.NOW, fallback=True))
        self.assertFalse(auto.should_run(3, self.ago(23), self.NOW, fallback=True))
        self.assertFalse(auto.should_run(0, self.ago(48), self.NOW, fallback=True))


class RunLockTests(unittest.TestCase):
    def test_lock_is_exclusive_and_released(self):
        with temp_data_dir():
            a, b = auto.RunLock(), auto.RunLock()
            self.assertTrue(a.acquire())
            self.assertFalse(b.acquire())
            a.release()
            self.assertTrue(b.acquire())
            b.release()

    def test_stale_pid_is_replaced(self):
        with temp_data_dir() as root:
            dead = subprocess.Popen(["true"])
            dead.wait()
            (root / "auto.lock").write_text(str(dead.pid))
            lock = auto.RunLock()
            self.assertTrue(lock.acquire())
            lock.release()


if __name__ == "__main__":
    unittest.main()
