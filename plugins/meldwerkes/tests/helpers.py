"""Shared test helpers: isolated data dir, stub model, brain factory."""

import contextlib
import sys
import tempfile
from pathlib import Path
from unittest import mock

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import memory  # noqa: E402


@contextlib.contextmanager
def temp_data_dir():
    """Point every module-level storage path at a fresh temp directory."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        patches = [
            mock.patch.object(memory, "DATA_DIR", root),
            mock.patch.object(memory, "DEFAULT_DB", root / "memory.db"),
            mock.patch.object(memory, "SETTINGS_FILE", root / "settings.json"),
            mock.patch.object(memory, "CHECKPOINT_DIR", root / "checkpoints"),
            mock.patch.object(memory, "SESSION_CONTEXT_FILE", root / "session-context.json"),
        ]
        for p in patches:
            p.start()
        try:
            yield root
        finally:
            for p in reversed(patches):
                p.stop()


class StubCompleter:
    """Stands in for llm.Completer: pops canned responses, records prompts."""

    def __init__(self, responses=()):
        self.responses = list(responses)
        self.prompts = []

    def complete(self, prompt, max_tokens=4096):
        self.prompts.append(prompt)
        if not self.responses:
            raise RuntimeError("StubCompleter out of responses")
        item = self.responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def make_brain(store, domain):
    return store.create_brain(domain.replace("-", " ").title(), domain)
