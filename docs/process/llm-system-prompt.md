# Genia LLM System Prompt

You are working in the Genia repo.

Before doing anything, read and follow:

- AGENTS.md
- GENIA_STATE.md
- GENIA_RULES.md
- GENIA_REPL_README.md
- README.md

GENIA_STATE.md is final authority when files conflict.



Rules:

- Do not invent implemented behavior.
- Do not expand scope.
- Do not redesign the feature
- Do not introduce new syntax unless the approved contract explicitly requires it.
- Keep documentation truthful and current.
- If behavior changes, update relevant tests and docs in the appropriate phase.
- Do not work on `main`.
- Do not continue into another phase.
- Prefer minimal, precise, local changes.

## Handoff Files

Each phase must produce a handoff file under:

.genia/process/tmp/handoffs/<change-slug>/

Rules:

- These are temporary LLM coordination artifacts.
- They are NOT canonical documentation.
- They must NOT be committed.
- Each phase must read prior handoffs before starting.
- If required handoff files are missing → STOP and report.
- Distillation must extract durable documentation into canonical docs, then remove or mark handoffs for deletion.

Testing note:
This repository is managed by `uv`. Always invoke pytest through the project
environment with `uv run pytest`; never use bare `pytest`, because it may resolve
to a system installation without the locked development dependencies.

The development dependency group includes `pytest-xdist` and PyYAML. Do not
infer that either is unavailable until the equivalent `uv run` command fails.

This repo supports parallel pytest execution.

For full regression testing, prefer:

  uv run pytest -n auto -q

Use narrower targeted tests during development, but before audit/merge run the full parallel regression command when practical.

If `uv run pytest -n auto -q` specifically reports that xdist or `-n` is
unavailable, report that clearly and fall back to:

  uv run pytest -q
