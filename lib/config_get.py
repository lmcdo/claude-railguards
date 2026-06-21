#!/usr/bin/env python3
"""Tiny config reader for the shell git-hooks. Prints a value from
railguards.config.json by dot-path, with a built-in default.

Usage:
  config_get.py git_hooks.protected_branches "main master"   # list -> space-joined
  config_get.py git_hooks.max_file_bytes 2097152             # scalar
Lists print space-separated; scalars print as-is. Missing/any-error -> the default.
"""
import json
import os
import sys

ROOT = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def main():
    if len(sys.argv) < 2:
        sys.exit(0)
    dotted = sys.argv[1]
    default = sys.argv[2] if len(sys.argv) > 2 else ""
    path = os.environ.get("RAILGUARDS_CONFIG") or os.path.join(ROOT, "railguards.config.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            node = json.load(f)
        for key in dotted.split("."):
            node = node[key]
    except Exception:
        print(default)
        return
    if isinstance(node, (list, tuple)):
        print(" ".join(str(x) for x in node))
    elif isinstance(node, bool):
        print("true" if node else "false")
    else:
        print(node)


if __name__ == "__main__":
    main()
