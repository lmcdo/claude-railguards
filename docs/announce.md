# Rules files ask the AI to behave. This makes it prove it.

Every AI coding setup today ships a rules file — `CLAUDE.md`, `AGENTS.md`, `.cursor/rules`.
They're useful, and they're all the same shape: **prose the model is asked to follow.** The
model can ignore them, and it quietly does as the context fills up. The most common symptom is
the one everyone's now measured: the agent **rewrites code that already exists** — a second
geocoder, a third "fetch the weather" function — because it didn't know (or forgot) the first
one was there.

**claude-railguards** is the deterministic backstop for that non-determinism. It doesn't ask
the agent to behave. It runs as code at the agent's edit boundary and **blocks the edit until
the agent has done the work.**

## What it enforces

- **Prior-art guard (PreToolUse).** When the agent tries to write a new file or add a data
  source, the hook searches your repo for an existing implementation of the same concern and
  **blocks the write**, pointing at the file to reuse. The only way past is a written
  `prior-art-checked: <why reuse isn't viable>` ack — which gets logged. This caught a duplicate
  data-source fetcher in the codebase it came from, *before* it was written.
- **Pre-implementation gate.** A skill that forces a real investigation (schema, join keys,
  timeout risk, loop invariants) before any DB-touching or migration code — and a marker the
  agent must produce.
- **QA-report-as-a-gate.** Before a risky change, the agent fills a `.qa_report.json` — what it
  assumed, how it could break, which functions it touched. A validator **blocks the push** if the
  report is missing or thin. This is the piece almost nothing else does: a machine-checked
  contract the agent has to satisfy.
- **Git-side guards.** Branch guard, secrets scan (keys + DB-URLs-with-passwords), large-file
  gate, and a commit-hash stamp — installed per repo.

## Honest positioning

I'm not going to oversell it. The git-side guards overlap with Gitleaks / lefthook / pre-commit —
use those if you prefer; the value here isn't the secrets scanner. The prior-art guard is
fast and grep-based: it blocks *before the write*, which the PR-time semantic dedup tools
(Octopus, Pharaoh, CodeAnt) don't — but they detect *better* (embeddings vs word-match). Different
trade-off, not a better mousetrap.

The genuinely under-served idea is the **composition**: nothing off-the-shelf makes an AI agent
*prove it investigated, prove it didn't duplicate, prove it filled a QA contract — and hard-blocks
the edit until it does.* That enforced-precondition layer, wired into the agent lifecycle, is the
point.

## Install

```text
/plugin marketplace add lmcdo/claude-railguards
/plugin install railguards@claude-railguards
install-git-hooks          # adds the git-side guards to the current repo
```

Everything project-specific (which data sources already exist, which branches are protected)
lives in one `railguards.config.json`. Nothing is hardcoded.

MIT. Feedback and issues welcome — especially on where the prior-art guard should go semantic.

https://github.com/lmcdo/claude-railguards
