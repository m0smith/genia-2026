# Genia LLM Prompt Templates

## Universal Header

Before doing anything, read and follow:

- AGENTS.md
- GENIA_STATE.md
- GENIA_RULES.md
- GENIA_REPL_README.md
- README.md

GENIA_STATE.md is final authority.

Run:

```bash
./scripts/check-genia-branch.sh

# Genia LLM Prompt Templates

## Universal Header

Before doing anything, read and follow:

- AGENTS.md
- GENIA_STATE.md
- GENIA_RULES.md
- GENIA_REPL_README.md
- README.md

GENIA_STATE.md is final authority.

Run:

```bash
./scripts/check-genia-branch.sh
```

Do not work on main.
Do not continue into another phase.

# Phase Rule

This prompt is for phase: <PHASE>.

Allowed commit prefix: <PREFIX>.

You may only modify files needed for this phase.
Stop after committing this phase.


Then add phase-specific sections below it for `preflight`, `spec`, `design`, `test`, `implementation`, `doc-sync`