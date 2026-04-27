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


Add phase-specific sections below the Universal Header and Phase Rule for each phase.

## Preflight Phase

After completing sections 0 (BRANCH), 1 (SCOPE LOCK), 2 (SOURCE OF TRUTH), and 3 (FEATURE MATURITY),
complete section 3a (PORTABILITY ANALYSIS) before proceeding to section 4.

All seven portability fields are required. Do not leave any field blank or deferred.

Required fields:

- `Portability zone:` — one or more of: language contract, Core IR, prelude, Python reference host, host adapter, shared spec, docs/tests only
- `Core IR impact:` — `none` or `yes — <named Ir* node families>`
- `Capability categories affected:` — subset of parse, ir, eval, cli, flow, error — or `none`
- `Shared spec impact:` — `none` or `new/updated cases required in spec/<category>/`
- `Python reference host impact:` — `none` or `yes — <description>`
- `Host adapter impact:` — `none` or `yes — <description>`
- `Future host impact:` — forward-looking note grounded in current GENIA_STATE.md facts

Rules:
- Do not use "TBD" or defer any field.
- Do not claim Node.js, Java, Rust, Go, or C++ hosts are implemented.
- Do not claim a Python-host-only behavior is part of the language contract unless GENIA_STATE.md says so.
- Answer `Core IR impact:` with `none` or a named Ir* family — no vague answers.

Do not proceed to spec until section 3a is complete.