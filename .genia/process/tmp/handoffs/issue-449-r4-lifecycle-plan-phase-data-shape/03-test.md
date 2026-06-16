# === GENIA TEST HANDOFF ===

CHANGE NAME: issue #449 r4-lifecycle-plan-phase-data-shape
CHANGE SLUG: issue-449-r4-lifecycle-plan-phase-data-shape
ISSUE: #449
PHASE: TEST
BRANCH: feature/issue-449-r4-lifecycle-plan-phase-data-shape

## Branch

- Starting branch: `feature/issue-449-r4-lifecycle-plan-phase-data-shape`
- Working branch: `feature/issue-449-r4-lifecycle-plan-phase-data-shape`
- Branch status: already existed; no new branch was created

## Files Changed

- `tests/unit/test_lifecycle_plan.py`
- `.genia/process/tmp/handoffs/issue-449-r4-lifecycle-plan-phase-data-shape/03-test.md`

## Tests Added

Focused failing tests were added in `tests/unit/test_lifecycle_plan.py` for the issue #449 lifecycle plan phase data-shape contract.

The tests cover:

- valid lifecycle plan shape with quoted identifier values
- valid phase shape with `name`, `action`, optional `scope`, and optional `always`
- `always` normalization to `false` when absent
- deterministic phase order preservation
- minimal plan and phase validation without action execution
- missing required plan fields
- invalid `phases` collection shape
- invalid phase entry shape
- missing phase `name` and `action`
- non-boolean `always`
- duplicate phase names
- callable phase actions rejected as nonportable behavior

The tests intentionally do not require:

- lifecycle execution
- annotation discovery or execution
- parser changes
- new syntax
- Core IR changes
- lifecycle runner behavior

## Validation Commands Run

```bash
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run pytest -q tests/unit/test_lifecycle_plan.py
```

## Observed Failing Output Summary

The focused test command failed as expected:

```text
13 failed in 0.27s
ModuleNotFoundError: No module named 'genia.lifecycle_plan'
```

All failures occur when the new focused tests attempt to import the intended lifecycle plan validation/normalization boundary:

```python
importlib.import_module("genia.lifecycle_plan")
```

## Why This Failure Is Expected

The approved design names `src/genia/lifecycle_plan.py` as the preferred later implementation file for issue #449. That module does not exist yet, and this TEST phase must not implement it.

The failure therefore proves the intended missing support:

- no lifecycle plan validator exists yet
- no lifecycle plan normalizer exists yet
- no production lifecycle plan data-shape support has been added yet

This is the expected TEST-phase failing state before implementation.

## Production Implementation

No production implementation was changed.

No files under `src/`, `hosts/`, `spec/`, parser, Core IR, evaluator, interpreter, or prelude were edited.

## Docs Sync / Audit

Docs sync was not performed.

Audit was not performed.

The only documentation-like artifact added in this phase is this TEST handoff file under `.genia/process/tmp/handoffs/`.

## Next Required Phase

IMPLEMENTATION
