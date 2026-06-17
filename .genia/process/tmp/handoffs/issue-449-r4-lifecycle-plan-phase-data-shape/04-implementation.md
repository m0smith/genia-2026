# === GENIA IMPLEMENTATION HANDOFF ===

CHANGE NAME: issue #449 r4-lifecycle-plan-phase-data-shape
CHANGE SLUG: issue-449-r4-lifecycle-plan-phase-data-shape
ISSUE: #449
PHASE: IMPLEMENTATION
BRANCH: feature/issue-449-r4-lifecycle-plan-phase-data-shape
FAILING TEST COMMIT: 05ed414

## Branch

- Starting branch: `feature/issue-449-r4-lifecycle-plan-phase-data-shape`
- Working branch: `feature/issue-449-r4-lifecycle-plan-phase-data-shape`
- Branch status: already existed; no new branch was created

## Files Changed

- `src/genia/lifecycle_plan.py`
- `.genia/process/tmp/handoffs/issue-449-r4-lifecycle-plan-phase-data-shape/04-implementation.md`

## Implementation Summary

Added a focused `genia.lifecycle_plan` module for lifecycle phase-plan data-shape validation and normalization.

The implementation provides:

- `validate_lifecycle_plan(value) -> None`
- `normalize_lifecycle_plan(value) -> GeniaMap`
- validation that plans are ordinary `GeniaMap` values
- validation that plan `name` and phase `name` / `action` fields are quoted identifier values represented by `GeniaSymbol`
- validation that `phases` is a list of phase maps
- deterministic phase-order preservation
- `always: false` normalization when a phase omits `always`
- deterministic path-based diagnostics for malformed plan and phase shapes
- duplicate phase-name rejection within a plan
- callable action rejection as nonportable behavior

The implementation does not resolve actions, execute phases, inspect annotations, change parser behavior, change Core IR, or touch execution modes.

## Validation Commands Run

```bash
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run pytest -q tests/unit/test_lifecycle_plan.py
```

Observed result:

```text
13 passed in 0.09s
```

```bash
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run pytest -q tests/doc/test_lifecycle_architecture_doc.py tests/unit/test_quote_symbols.py
```

Observed result:

```text
18 passed in 0.16s
```

```bash
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run ruff check src/genia/lifecycle_plan.py tests/unit/test_lifecycle_plan.py
```

Observed result:

```text
error: Failed to spawn: `ruff`
Caused by: No such file or directory (os error 2)
```

Ruff was not available in this environment; pytest validation completed successfully.

## Limitations / Non-Goals Preserved

- No lifecycle runner behavior was added.
- No phase execution was added.
- No action resolution was added.
- No command/file/pipe/REPL execution-mode refactor was performed.
- No annotation discovery or execution behavior was added.
- No `@setup` or `@teardown` behavior was added.
- No parser, syntax, Core IR, prelude, host adapter, server, notebook, or module lifecycle changes were made.

## Docs Sync / Audit

Docs sync was not performed.

Audit was not performed.

## Next Required Phase

DOC SYNC
