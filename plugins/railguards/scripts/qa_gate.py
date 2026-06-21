#!/usr/bin/env python3
"""QA-report gate — PORTABLE EDITION (core schema validation).

prior-art-checked: this is a NEW standalone railguards-toolkit file in a separate
repo (claude-railguards), not a duplicate of any other project code; it is the
portable extraction OF that project's scripts/qa_gate.py, built to run anywhere.

Validates a `.qa_report.json` against the universal schema a production QA
discipline relies on, with the thresholds read from `railguards.config.json`:

  qa_gate.tiers              — allowed tier names.
  qa_gate.min_break_it       — required break-it scenarios per tier.
  qa_gate.require_functions  — required documented functions per tier.

This is the project-agnostic core. The full upstream gate adds optional layers
(liability scan, test-baseline ratchet, Python/TS adversarial scanners, diff
coverage) — those are project-coupled and shipped separately/behind config.

Usage:  python qa_gate.py .qa_report.json [--config railguards.config.json]
Exit 0 = pass, 1 = validation errors (printed to stderr).
"""
import json
import os
import re
import sys

ROOT = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
DEFAULTS = {
    "tiers": ["critical", "standard", "minor"],
    "min_break_it": {"critical": 5, "standard": 3, "minor": 0},
    "require_functions": {"critical": 1, "standard": 1, "minor": 0},
}


def load_config(explicit=None):
    path = explicit or os.environ.get("RAILGUARDS_CONFIG") or os.path.join(ROOT, "railguards.config.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            cfg = (json.load(f) or {}).get("qa_gate", {}) or {}
    except Exception:
        cfg = {}
    out = dict(DEFAULTS)
    out.update({k: v for k, v in cfg.items() if v is not None})
    return out


def non_empty(val):
    return isinstance(val, str) and bool(val.strip())


def validate(report, cfg):
    errors = []
    tier = report.get("tier")
    if tier not in cfg["tiers"]:
        errors.append(f"tier must be one of {cfg['tiers']}, got {tier!r}")
        return errors  # can't tier-gate without a valid tier

    ch = report.get("commit_hash")
    if not non_empty(ch) or not re.fullmatch(r"[0-9a-fA-F]{7,40}", ch.strip()):
        errors.append("commit_hash must be a 7-40 char hex string")

    files = report.get("files")
    if not isinstance(files, list) or not files or not all(non_empty(f) for f in files):
        errors.append("files must be a non-empty list of paths")

    if not non_empty(report.get("justification")):
        errors.append("justification must be a non-empty string")

    need_bi = cfg["min_break_it"].get(tier, 0)
    bi = report.get("break_it") or []
    if len(bi) < need_bi:
        errors.append(f"need >= {need_bi} break_it scenarios for tier {tier}, got {len(bi)}")
    for i, s in enumerate(bi):
        for key in ("scenario", "what_happens", "how"):
            if not non_empty((s or {}).get(key, "")):
                errors.append(f"break_it[{i}].{key} must be non-empty")

    need_fn = cfg["require_functions"].get(tier, 0)
    fns = report.get("functions") or []
    if len(fns) < need_fn:
        errors.append(f"need >= {need_fn} documented functions for tier {tier}, got {len(fns)}")

    return errors


def main():
    args = list(sys.argv[1:])
    cfg_path = None
    if "--config" in args:
        i = args.index("--config")
        cfg_path = args[i + 1] if i + 1 < len(args) else None
        args = args[:i] + args[i + 2:]
    report_path = args[0] if args else ".qa_report.json"
    try:
        with open(report_path, "r", encoding="utf-8") as f:
            report = json.load(f)
    except Exception as e:
        print(f"QA-GATE: cannot read {report_path}: {e}", file=sys.stderr)
        sys.exit(1)

    cfg = load_config(cfg_path)
    errors = validate(report, cfg)
    if errors:
        print(f"QA-GATE: FAILED — {len(errors)} validation error(s):", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        sys.exit(1)
    print("QA-GATE: PASSED")
    sys.exit(0)


if __name__ == "__main__":
    main()
