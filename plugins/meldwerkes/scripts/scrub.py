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
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}"),                                   # API keys (sk-..., sk-ant-...)
    re.compile(r"://[^/\s:@]+:[^@\s]+@"),                                      # password in a URL
    re.compile(r"(?i)\bbasic\s+(?=[A-Za-z0-9+/]*[0-9+/=])[A-Za-z0-9+/]{16,}={0,2}"),  # HTTP Basic credentials
    re.compile(r"\beyJ[A-Za-z0-9_-]{5,}\.[A-Za-z0-9_-]{5,}\.[A-Za-z0-9_-]{5,}"),  # JWT
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b"),
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"),
]

_PEM_BEGIN = re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")
_PEM_END = re.compile(r"-----END [A-Z ]*PRIVATE KEY-----")
_PEM_BODY = re.compile(r"^[A-Za-z0-9+/=]{8,}$")

# First line of each prompt the automatic loop itself sends to a model.
_INTERNAL_HEADERS = (
    "You are extracting durable preferences",
    "Analyze this decision log",
    "Analyze principle conflicts",
)


def scrub(text: str):
    """Return (text without secret-looking lines, number of lines removed)."""
    kept, dropped, in_key = [], 0, False
    for line in text.split("\n"):
        if in_key:  # inside a PEM block: the base64 body is the secret, so drop it through END
            if _PEM_END.search(line):
                dropped, in_key = dropped + 1, False
                continue
            if _PEM_BODY.match(line.strip()):
                dropped += 1
                continue
            in_key = False  # prose after a bare header (or a truncated key): keep it
        if _PEM_BEGIN.search(line):
            dropped += 1
            in_key = not _PEM_END.search(line)
            continue
        if any(p.search(line) for p in _PATTERNS):
            dropped += 1
        else:
            kept.append(line)
    return "\n".join(kept), dropped


def is_internal_prompt(text: str) -> bool:
    return text.lstrip().startswith(_INTERNAL_HEADERS)
