# claude-railguards (PoC)

Portable extraction of the PlotDetect/ComplianceEngine code-safety railguards, so the
same discipline can be dropped into any project. See the design doc:
`~/.claude/plans/meta-railguards-portability-2026-06.md`.

## What's in this PoC
The 3 highest-value, lowest-coupling pieces, made config-driven:

| Piece | What it does | Coupling externalized to |
|---|---|---|
| `hooks/prior-art-guard.py` | PreToolUse(Write\|Edit) — blocks re-implementing existing capability; forced `prior-art-checked:` ack | `prior_art.watch_dirs`, `known_sources`, `domain_url_fragments` |
| `scripts/qa_gate.py` | Validates a `.qa_report.json` against the universal schema | `qa_gate.tiers`, `min_break_it`, `require_functions` |
| `skills/pre-impl/SKILL.md` | Pre-implementation investigation protocol (generic, as-is) | none |

All project specifics live in **`railguards.config.json`** — nothing PlotDetect-specific
is reachable in the code.

## Install into a project
```bash
./install.sh /path/to/target-project
# then edit target-project/railguards.config.json (known_sources, watch_dirs)
```
This copies the files under `.claude/railguards/`, seeds `railguards.config.json`, and
merges the PreToolUse hook into `.claude/settings.json` (idempotent).

## Not yet ported (later phases — see plan)
Branch guard, secrets scan, bracket-lint, hash-stamp (near-generic, P2); liability scan,
test-baseline ratchet, db-safety, capability index (project-coupled, P3); pip-package the
validators + plugin marketplace manifest (P4).

## Config shape
```json
{
  "prior_art": {
    "watch_dirs": ["/services/", "/src/"],
    "known_sources": ["the", "data-source", "names", "already", "implemented"],
    "domain_url_fragments": ["yourapi.example.com"]
  },
  "qa_gate": {
    "tiers": ["critical", "standard", "minor"],
    "min_break_it":      { "critical": 5, "standard": 3, "minor": 0 },
    "require_functions": { "critical": 1, "standard": 1, "minor": 0 }
  }
}
```
