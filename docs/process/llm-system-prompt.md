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