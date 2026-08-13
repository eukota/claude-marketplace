#!/usr/bin/env python3
"""Smoke-test a plugin's hooks against ordinary input.

Hooks are the one plugin primitive that can break a session outright. A hook
that errors, hangs, or returns a blocking exit code stops the user's work — and
the failure looks like Claude Code is broken rather than like a plugin bug.

The check that matters is not "does the hook work on the case it was written
for" but "does it stay out of the way on the cases it was not." So every hook
is fed a set of *ordinary* payloads — a slash command, plain prose, a routine
tool call — and must exit 0 and emit nothing that blocks.

This exists because a UserPromptSubmit hook once shipped that classified each
message and answered NO_SIGNAL for anything unremarkable. As a type:"prompt"
hook, that answer carried preventContinuation semantics, so the plugin blocked
every ordinary message including its own setup command. One run against a plain
prompt would have caught it.

Usage:
  python3 hookcheck.py <plugin-dir>
  python3 hookcheck.py <plugin-dir> --verbose
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

# Exit 2 is Claude Code's "block" signal for hooks. Anything non-zero is a
# problem; 2 specifically will stop the user's turn.
BLOCK_EXIT = 2

# Cost budgets. Hooks run on the user's critical path — a hook that is correct
# but slow is the failure mode immediately after one that blocks. Injected
# context is worse than a slow hook, because it is paid on every subsequent
# turn of the session rather than once.
SLOW_MS = 150
INTERPRETERS = ("python", "python3", "node", "ruby", "perl", "deno", "bun")
MAX_CONTEXT_CHARS = 4000

# Ordinary payloads per event. Deliberately unremarkable: the interesting case
# is usually handled, the boring one is what breaks.
PAYLOADS = {
    "UserPromptSubmit": [
        ("slash command", {"prompt": "/help"}),
        ("plain prose", {"prompt": "fix the failing test in auth.py"}),
        ("a question", {"prompt": "what does this function do?"}),
        ("a correction", {"prompt": "no, use tabs not spaces"}),
        ("empty", {"prompt": ""}),
    ],
    "SessionStart": [("startup", {"source": "startup"})],
    "Stop": [("turn end", {})],
    "SubagentStop": [("subagent end", {})],
    "PreToolUse": [
        ("read", {"tool_name": "Read", "tool_input": {"file_path": "/tmp/x.txt"}}),
        ("bash", {"tool_name": "Bash", "tool_input": {"command": "ls"}}),
    ],
    "PostToolUse": [
        ("read result", {"tool_name": "Read", "tool_input": {"file_path": "/tmp/x.txt"},
                         "tool_response": "ok"}),
    ],
    "PreCompact": [("compact", {"trigger": "auto"})],
    "Notification": [("notify", {"message": "waiting"})],
}
COMMON = {"session_id": "smoke-test", "cwd": os.getcwd(),
          "transcript_path": "/dev/null"}


def check_command_hook(event, hook, plugin_dir, verbose):
    """Run the hook against each ordinary payload; it must stay out of the way."""
    findings = []
    cmd = hook.get("command", "")
    env = dict(os.environ, CLAUDE_PLUGIN_ROOT=str(plugin_dir))
    timeout = hook.get("timeout", 10)

    # A referenced script that does not exist fails silently behind `|| true`
    for token in cmd.replace('"', " ").replace("'", " ").split():
        if "${CLAUDE_PLUGIN_ROOT}" in token:
            target = Path(token.replace("${CLAUDE_PLUGIN_ROOT}", str(plugin_dir)))
            if not target.exists():
                findings.append(("ERROR", f"referenced file missing: {target.name}"))

    # An interpreter costs 30-50ms of startup before the hook does anything.
    first_word = cmd.strip().split()[0] if cmd.strip() else ""
    if os.path.basename(first_word) in INTERPRETERS:
        findings.append(("INFO", f"spawns {os.path.basename(first_word)} "
                                 "(~30-50ms startup before any work)"))
    if "timeout" not in hook:
        findings.append(("WARN", "no timeout declared — a hang has no ceiling"))

    for label, extra in PAYLOADS.get(event, [("generic", {})]):
        payload = json.dumps({**COMMON, "hook_event_name": event, **extra})
        try:
            t0 = time.perf_counter()
            r = subprocess.run(cmd, shell=True, input=payload, capture_output=True,
                               text=True, timeout=timeout + 2, env=env)
            elapsed_ms = (time.perf_counter() - t0) * 1000
        except subprocess.TimeoutExpired:
            findings.append(("ERROR", f"[{label}] timed out (> {timeout}s) — blocks the turn"))
            continue

        if r.returncode == BLOCK_EXIT:
            findings.append(("ERROR", f"[{label}] exit 2 — BLOCKS the user's turn"))
        elif r.returncode != 0:
            findings.append(("WARN", f"[{label}] exit {r.returncode} (expected 0)"))

        if elapsed_ms > SLOW_MS:
            findings.append(("WARN", f"[{label}] took {elapsed_ms:.0f}ms "
                                     f"(budget {SLOW_MS}ms) — runs on the user's critical path"))

        out = (r.stdout or "").strip()
        if out:
            try:
                parsed = json.loads(out)
                ctx = parsed.get("hookSpecificOutput", {}).get("additionalContext")
                if ctx and len(ctx) > MAX_CONTEXT_CHARS:
                    findings.append(("WARN",
                        f"[{label}] injects {len(ctx)} chars of context — paid on "
                        "EVERY turn of the session, not once. Cap it by budget."))
                decision = parsed.get("decision") or parsed.get(
                    "hookSpecificOutput", {}).get("permissionDecision")
                if decision in ("block", "deny"):
                    findings.append(("ERROR", f"[{label}] returned decision '{decision}'"))
            except json.JSONDecodeError:
                if verbose:
                    findings.append(("INFO", f"[{label}] non-JSON stdout ({len(out)} chars)"))
    return findings


def check_prompt_hook(event, hook):
    """Prompt hooks are gates. Flag the shapes that stop work."""
    findings = []
    text = (hook.get("prompt") or "").lower()

    if event != "Stop":
        findings.append((
            "ERROR" if any(w in text for w in ("no_signal", "respond with", "classify", "does this"))
            else "WARN",
            f"type:'prompt' on {event} is a GATE — the evaluating model's "
            "ok:false carries preventContinuation and stops the turn. "
            "Use type:'command' for anything passive (logging, capture, "
            "context injection)."))

    if "no_signal" in text or "otherwise respond" in text:
        findings.append(("ERROR",
                         "prompt has a negative branch — that answer reads as "
                         "'do not continue' and will block ordinary messages"))
    return findings


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("plugin_dir")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    plugin_dir = Path(args.plugin_dir).expanduser().resolve()
    hooks_file = plugin_dir / "hooks" / "hooks.json"
    if not hooks_file.exists():
        print(f"No hooks/hooks.json in {plugin_dir.name} — nothing to check.")
        return 0

    try:
        config = json.loads(hooks_file.read_text())
    except json.JSONDecodeError as e:
        print(f"FAIL  hooks.json is not valid JSON: {e}")
        return 1

    print(f"Smoke-testing hooks in {plugin_dir.name}\n")
    errors = warns = checked = 0

    for event, groups in config.get("hooks", {}).items():
        for group in groups:
            for hook in group.get("hooks", []):
                checked += 1
                kind = hook.get("type", "?")
                label = f"{event} ({kind})"
                findings = (check_prompt_hook(event, hook) if kind == "prompt"
                            else check_command_hook(event, hook, plugin_dir, args.verbose))
                bad = [f for f in findings if f[0] == "ERROR"]
                mid = [f for f in findings if f[0] == "WARN"]
                errors += len(bad); warns += len(mid)
                status = "FAIL" if bad else ("WARN" if mid else "ok  ")
                print(f"  {status}  {label}")
                for level, msg in findings:
                    if level == "INFO" and not args.verbose:
                        continue
                    print(f"          {level}: {msg}")

    print(f"\n{checked} hook(s) checked — {errors} error(s), {warns} warning(s)")
    if errors:
        print("\nA hook that exits 2, times out, or returns a block decision stops")
        print("the user's turn. To them it looks like Claude Code is broken.")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
