---
description: Validate the project's .qa_report.json against the railguards QA schema (tier, commit_hash, files, break-it count, functions).
---

Run the railguards QA-gate validator on this project's QA report and report the result.

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/qa_gate.py" "${CLAUDE_PROJECT_DIR}/.qa_report.json"
```

If it FAILS, list each validation error and what the report needs (the required
break-it count and documented-function count come from the tier in
`railguards.config.json`). Do not proceed with a risky change until it passes.
