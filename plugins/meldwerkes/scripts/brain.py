#!/usr/bin/env python3
"""Manage brains — create, list, split."""

import argparse
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from memory import MemoryStore, DEFAULT_DB
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="cmd", required=True)

    cr = subparsers.add_parser("create")
    cr.add_argument("--name", required=True)
    cr.add_argument("--domain", required=True)
    cr.add_argument("--description", default="")

    subparsers.add_parser("list")

    parser.add_argument("--db", default=str(DEFAULT_DB))
    args = parser.parse_args()

    store = MemoryStore(Path(args.db))

    if args.cmd == "create":
        brain = store.create_brain(args.name, args.domain, args.description)
        print(f"brain:{brain.id} name:{brain.name} domain:{brain.domain}")

    elif args.cmd == "list":
        brains = store.get_brains()
        if not brains:
            print("No brains registered.")
            return
        for b in brains:
            print(f"[{b.id[:8]}] {b.name} (domain: {b.domain}) — {b.description or 'no description'}")


if __name__ == "__main__":
    main()
