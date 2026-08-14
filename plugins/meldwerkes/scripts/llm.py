#!/usr/bin/env python3
"""Shared model access for meldwerkes scripts.

Two ways to reach a model, and they bill differently:

  subscription — shells out to the `claude` CLI in headless mode (`claude -p`),
                 which runs on the user's existing Claude Code login. No API
                 key, no credit balance, draws on subscription usage limits.

  api          — the anthropic SDK against the raw API. Needs ANTHROPIC_API_KEY
                 and a funded API account, which is billed separately from any
                 Claude Code subscription.

Scripts ask which to use up front rather than discovering it halfway through a
long run, when the first call fails on a missing key or an empty balance.
"""

import os
import shutil
import subprocess
import sys

MODEL = "claude-sonnet-4-6"

# `claude -p` has no max_tokens equivalent; the cap only applies to the API path.
CLI_TIMEOUT = 300


def subscription_available() -> bool:
    return shutil.which("claude") is not None


def api_available() -> bool:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return False
    try:
        import anthropic  # noqa: F401
    except ImportError:
        return False
    return True


def add_auth_arg(parser):
    """Register --auth on a script's parser."""
    parser.add_argument(
        "--auth", choices=("ask", "subscription", "api"), default="ask",
        help="Which credentials to use for model calls. 'ask' prompts when "
             "interactive and auto-detects otherwise (default: ask).",
    )


def _prompt_for_auth() -> str:
    sub, api = subscription_available(), api_available()
    print("\nThis run makes model calls. Which credentials should it use?\n")
    print(f"  1) Your Claude Code subscription (claude -p)"
          f"{'' if sub else '   [unavailable: `claude` not on PATH]'}")
    print(f"     No API key needed; counts against subscription usage limits.")
    print(f"  2) Anthropic API key (ANTHROPIC_API_KEY)"
          f"{'' if api else '   [unavailable: no key set or SDK missing]'}")
    print(f"     Billed to your API account, separate from the subscription.\n")

    default = "1" if sub else ("2" if api else None)
    if default is None:
        sys.exit("Neither auth method is available. Install the `claude` CLI "
                 "or set ANTHROPIC_API_KEY with the anthropic SDK installed.")

    while True:
        try:
            choice = input(f"Choice [{default}]: ").strip() or default
        except (EOFError, KeyboardInterrupt):
            sys.exit("\nAborted.")
        if choice == "1" and sub:
            return "subscription"
        if choice == "2" and api:
            return "api"
        print("  Not a usable option — pick one that is not marked unavailable.")


def resolve_auth(choice: str) -> str:
    """Turn the --auth value into a concrete method, or exit explaining why not."""
    if choice == "subscription":
        if not subscription_available():
            sys.exit("--auth subscription needs the `claude` CLI on PATH.")
        return "subscription"

    if choice == "api":
        if not os.environ.get("ANTHROPIC_API_KEY"):
            sys.exit("--auth api needs ANTHROPIC_API_KEY set.")
        try:
            import anthropic  # noqa: F401
        except ImportError:
            sys.exit("--auth api needs the anthropic SDK: pip install anthropic")
        return "api"

    # ask: prompt a human, auto-detect a pipe.
    if sys.stdin.isatty():
        return _prompt_for_auth()
    if subscription_available():
        print("Non-interactive; using subscription auth (claude CLI).", file=sys.stderr)
        return "subscription"
    if api_available():
        print("Non-interactive; using API key auth.", file=sys.stderr)
        return "api"
    sys.exit("No usable auth. Install the `claude` CLI or set ANTHROPIC_API_KEY.")


class Completer:
    """One resolved auth method, reusable across many calls."""

    def __init__(self, auth: str):
        self.auth = auth
        self._client = None
        if auth == "api":
            from anthropic import Anthropic
            self._client = Anthropic()

    def complete(self, prompt: str, max_tokens: int = 4096) -> str:
        if self.auth == "subscription":
            proc = subprocess.run(
                ["claude", "-p", "--output-format", "text"],
                input=prompt, capture_output=True, text=True, timeout=CLI_TIMEOUT,
            )
            if proc.returncode != 0:
                raise RuntimeError(
                    f"claude CLI failed ({proc.returncode}): {proc.stderr.strip()[:300]}")
            return proc.stdout.strip()

        resp = self._client.messages.create(
            model=MODEL, max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(b.text for b in resp.content if b.type == "text").strip()


def strip_fence(raw: str) -> str:
    """Unwrap a ```json fence if the model added one."""
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.lstrip().startswith("json"):
            raw = raw.lstrip()[4:]
    return raw.strip()
