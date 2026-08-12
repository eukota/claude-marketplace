#!/usr/bin/env python3
"""Check candidate project names for collisions across the registries that matter.

Uniqueness is a filtering outcome, not a generation outcome — so generate wide
and let this decide. Anything with a package-registry hit is effectively taken
for a dev tool; GitHub repo-name counts are a softer signal of crowding.
"""

import concurrent.futures as cf
import json
import socket
import sys
import urllib.error
import urllib.request

TIMEOUT = 8


def _get(url, headers=None):
    req = urllib.request.Request(url, headers=headers or {"User-Agent": "namecheck"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, b""
    except Exception:
        return None, b""


def npm(name):
    code, _ = _get(f"https://registry.npmjs.org/{name}")
    return "TAKEN" if code == 200 else ("free" if code == 404 else "?")


def pypi(name):
    code, _ = _get(f"https://pypi.org/pypi/{name}/json")
    return "TAKEN" if code == 200 else ("free" if code == 404 else "?")


def crates(name):
    code, _ = _get(f"https://crates.io/api/v1/crates/{name}")
    return "TAKEN" if code == 200 else ("free" if code == 404 else "?")


def github(name):
    """Repos whose *name* matches exactly — a crowding signal, not a blocker."""
    import os

    h = {"User-Agent": "namecheck", "Accept": "application/vnd.github+json"}
    tok = os.environ.get("GITHUB_TOKEN")
    if tok:
        h["Authorization"] = f"Bearer {tok}"
    code, body = _get(
        f"https://api.github.com/search/repositories?q={name}+in:name&per_page=1",
        headers=h,
    )
    if code != 200:
        return "?"
    try:
        return str(json.loads(body).get("total_count", "?"))
    except Exception:
        return "?"


def dns(name, tld):
    try:
        socket.getaddrinfo(f"{name}.{tld}", None)
        return "TAKEN"
    except socket.gaierror:
        return "free"
    except Exception:
        return "?"


def check(name):
    return {
        "name": name,
        "npm": npm(name),
        "pypi": pypi(name),
        "crates": crates(name),
        "gh": github(name),
        ".com": dns(name, "com"),
        ".ai": dns(name, "ai"),
    }


def main():
    names = [n.strip().lower() for n in sys.argv[1:] if n.strip()]
    with cf.ThreadPoolExecutor(max_workers=8) as ex:
        rows = list(ex.map(check, names))

    hdr = f"{'name':<16}{'npm':<8}{'pypi':<8}{'crates':<8}{'gh':<8}{'.com':<8}{'.ai':<8}verdict"
    print(hdr)
    print("-" * len(hdr))
    for r in sorted(rows, key=lambda r: (r["npm"] != "free", r["pypi"] != "free")):
        pkg_taken = any(r[k] == "TAKEN" for k in ("npm", "pypi", "crates"))
        try:
            crowded = int(r["gh"]) > 50
        except ValueError:
            crowded = False
        verdict = "TAKEN" if pkg_taken else ("crowded" if crowded else "CLEAR")
        print(
            f"{r['name']:<16}{r['npm']:<8}{r['pypi']:<8}{r['crates']:<8}"
            f"{r['gh']:<8}{r['.com']:<8}{r['.ai']:<8}{verdict}"
        )


if __name__ == "__main__":
    main()
