# === GENIA IMPLEMENTATION (issue #492 r4-result-policy-include-flags) ===

Follow docs/process/llm-system-prompt.md.

CHANGE NAME: issue #492 r4-result-policy-include-flags
CHANGE SLUG: issue-492-r4-result-policy-include-flags

PHASE: implementation only.

GENIA_STATE.md is final authority.

## Branch Confirmation

- Starting branch: `feature/issue-492-r4-result-policy-include-flags`
- Working branch: `feature/issue-492-r4-result-policy-include-flags`
- Branch already existed: yes
- Confirmed not on `main`: yes

## Failing-Test Commit

- Failing-test commit SHA: `2fd81177bbf516e3b9b591a7b4aa576ecfc0b510`

## Files Changed

- `src/genia/lifecycle_plan.py`
- `.genia/process/tmp/handoffs/issue-492-r4-result-policy-include-flags/04-implementation.md`

No docs, tests, parser, IR, evaluator, builtins, CLI, prelude, lifecycle runner, cleanup behavior, annotation behavior, native-test behavior, or shared specs were edited in this phase.

## Implementation Summary

`_normalize_result_policy` now preserves accepted explicit boolean values for:

- `include_phase`
- `include_scope`
- `include_role`
- `include_source_location`

The implementation keeps the existing default normalized map with all include fields set to `true`, then reuses the existing `_require_boolean` validation for each present include field and writes the accepted value back into the normalized map.

Behavior preserved:

- omitted include fields default to `true`
- explicit `true` stays `true`
- explicit `false` now stays `false`
- non-boolean include values still raise deterministic path-specific `ValueError`
- unknown `result_policy` fields still reject
- `failure_order` remains unchanged; only `observed_order` is accepted
- no lifecycle behavior executes; this remains inert data normalization only

## Exact Command Run

```bash
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run pytest -q tests/unit/test_lifecycle_plan.py -v
```

## Test Results

```text
collected 35 items
tests/unit/test_lifecycle_plan.py ...................................    [100%]
35 passed in 0.22s
```

The previous red phase is now green.

## Doc-Sync Follow-Up

No docs were edited in this implementation phase.

Later doc-sync should review `GENIA_STATE.md` section 9.3 and `docs/architecture/lifecycle.md` for result-policy wording. `GENIA_STATE.md` section 9.3 likely needs its lifecycle-plan unit-test count updated from 32 to 35, and wording may need to clarify that result-policy `include_*` fields preserve explicit accepted boolean values while omitted fields default to `true`.

## Stop Point

Hard stop after the implementation commit. Do not proceed to doc sync, audit, or distillation in this phase.
