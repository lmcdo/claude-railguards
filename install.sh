#!/usr/bin/env bash
# claude-railguards installer — copies the portable railguards into a target project
# and wires the PreToolUse hook into its .claude/settings.json.
#
# Usage:  ./install.sh /path/to/target-project
#
# Idempotent: re-running re-copies the files and re-merges the hook (no duplicates).
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="${1:-}"
if [ -z "$TARGET" ] || [ ! -d "$TARGET" ]; then
  echo "usage: ./install.sh /path/to/target-project   (must be an existing directory)" >&2
  exit 1
fi

mkdir -p "$TARGET/.claude/railguards/hooks" "$TARGET/.claude/railguards/scripts" \
         "$TARGET/.claude/skills/pre-impl"

cp "$HERE/hooks/prior-art-guard.py"  "$TARGET/.claude/railguards/hooks/"
cp "$HERE/scripts/qa_gate.py"        "$TARGET/.claude/railguards/scripts/"
cp "$HERE/skills/pre-impl/SKILL.md"  "$TARGET/.claude/skills/pre-impl/"

# Seed a project config if none exists (the user fills in the coupling points).
if [ ! -f "$TARGET/railguards.config.json" ]; then
  cp "$HERE/railguards.config.json" "$TARGET/railguards.config.json"
  echo "seeded railguards.config.json — edit prior_art.known_sources / watch_dirs for this project"
fi

# Merge the PreToolUse hook into .claude/settings.json (create if absent).
SETTINGS="$TARGET/.claude/settings.json"
python - "$SETTINGS" "$HERE/settings.fragment.json" <<'PY'
import json, sys, os
settings_path, fragment_path = sys.argv[1], sys.argv[2]
frag = json.load(open(fragment_path)).get("hooks", {})
cur = {}
if os.path.exists(settings_path):
    try:
        cur = json.load(open(settings_path))
    except Exception:
        cur = {}
hooks = cur.setdefault("hooks", {})
pre = hooks.setdefault("PreToolUse", [])
cmd = "$CLAUDE_PROJECT_DIR/.claude/railguards/hooks/prior-art-guard.py"
already = any(
    cmd in (h.get("command", ""))
    for entry in pre for h in entry.get("hooks", [])
)
if not already:
    pre.extend(frag.get("PreToolUse", []))
    json.dump(cur, open(settings_path, "w"), indent=2)
    print(f"wired prior-art-guard into {settings_path}")
else:
    print("prior-art-guard already wired; settings unchanged")
PY

echo "done. Run 'git config core.hooksPath .githooks' separately if you also ship git hooks."
