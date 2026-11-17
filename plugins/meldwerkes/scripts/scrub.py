"""Keep secrets out of model calls and storage, and recognise our own prompts.

Line-based: a line that looks like a credential is dropped whole, so the secret
never reaches a model prompt, the database or a log. Findings are counted, never
quoted.
"""

import re

INTERNAL_ENV = "MELDWERKES_INTERNAL"

_PATTERNS = [
    # keyword as a substring (DB_PASSWORD, "password": ...), then : or =, then a
    # 10+ char value that is not a placeholder (${VAR}, <...>, {{...}})
    re.compile(
        r"""(?i)(?:api[_-]?key|secret|token|passw(?:or)?d)[A-Za-z0-9_]*["']?\s*[:=]\s*["']?(?![$<{])\S{10,}"""
    ),
    re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]{20,}"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b"),
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"),
]

# First line of each prompt the automatic loop itself sends to a model.
_INTERNAL_HEADERS = (
    "You are extracting durable preferences",
    "Analyze this decision log",
    "Analyze principle conflicts",
)


def scrub(text: str):
    """Return (text without secret-looking lines, number of lines removed)."""
    kept, dropped = [], 0
    for line in text.split("\n"):
        if any(p.search(line) for p in _PATTERNS):
            dropped += 1
        else:
            kept.append(line)
    return "\n".join(kept), dropped


def is_internal_prompt(text: str) -> bool:
    return text.lstrip().startswith(_INTERNAL_HEADERS)
