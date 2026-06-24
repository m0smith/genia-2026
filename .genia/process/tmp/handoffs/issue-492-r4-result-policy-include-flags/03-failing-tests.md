# === GENIA FAILING TESTS (issue #492 r4-result-policy-include-flags) ===

Follow docs/process/llm-system-prompt.md.

CHANGE NAME: issue #492 r4-result-policy-include-flags
CHANGE SLUG: issue-492-r4-result-policy-include-flags

PHASE: failing tests only.

GENIA_STATE.md is final authority.

Read before work:
- AGENTS.md
- GENIA_STATE.md
- GENIA_RULES.md
- GENIA_REPL_README.md
- README.md
- docs/process/llm-system-prompt.md
- docs/strategy/killer-workflow.md
- docs/strategy/release-roadmap.md
- .genia/process/tmp/handoffs/issue-492-r4-result-policy-include-flags/00-preflight.md
- .genia/process/tmp/handoffs/issue-492-r4-result-policy-include-flags/01-contract.md
- .genia/process/tmp/handoffs/issue-492-r4-result-policy-include-flags/02-design.md

## Branch Confirmation

- Starting branch: `feature/issue-492-r4-result-policy-include-flags`
- Working branch: `feature/issue-492-r4-result-policy-include-flags`
- Branch already existed: yes
- Confirmed not on `main`: yes

## Files Changed

- `tests/unit/test_lifecycle_plan.py`
- `.genia/process/tmp/handoffs/issue-492-r4-result-policy-include-flags/03-failing-tests.md`

No implementation code or canonical docs were edited in this phase.

## Tests Added

- `test_result_policy_preserves_explicit_all_false_include_flags`
- `test_result_policy_preserves_mixed_explicit_include_flags_independently`
- `test_result_policy_defaults_omitted_include_flags_after_single_explicit_false`

These tests prove:
- explicit all-false `result_policy` include flags should normalize to false
- mixed explicit boolean values should be preserved independently
- a single explicit false should be preserved while omitted include fields default to true

Existing result-policy coverage for absent defaults, explicit true values, non-boolean diagnostics, unsupported `failure_order`, and unknown field rejection was kept intact.

## Exact Command Run

```bash
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run pytest -q tests/unit/test_lifecycle_plan.py -v
```

## Failing Output Summary

Result:

```text
collected 35 items
tests/unit/test_lifecycle_plan.py ...........................FFF.....    [100%]
3 failed, 32 passed in 0.33s
```

Failing tests:

```text
FAILED tests/unit/test_lifecycle_plan.py::test_result_policy_preserves_explicit_all_false_include_flags
FAILED tests/unit/test_lifecycle_plan.py::test_result_policy_preserves_mixed_explicit_include_flags_independently
FAILED tests/unit/test_lifecycle_plan.py::test_result_policy_defaults_omitted_include_flags_after_single_explicit_false
```

Representative assertion:

```text
assert result_policy.get("include_phase") is False
E       AssertionError: assert True is False
```

## Expected Failure Explanation

The failures are expected and prove the approved implementation gap.

The current `_normalize_result_policy` implementation validates explicit boolean `include_*` values, including `false`, but returns a normalized map with hardcoded `true` defaults for all four include fields. The new tests demonstrate that accepted explicit `false` input is discarded during normalization.

This matches the contract/design handoff: accepted explicit booleans must be preserved, and defaults should apply only when fields are omitted.

## Doc-Sync Follow-Up

No docs were edited in this failing-test phase.

During the later implementation/docs phase, review `GENIA_STATE.md` section 9.3 and `docs/architecture/lifecycle.md` for result-policy wording. `GENIA_STATE.md` section 9.3 may also need its lifecycle-plan unit-test count updated because this phase increases `tests/unit/test_lifecycle_plan.py` from 32 to 35 focused cases once the implementation passes.

## Stop Point

Hard stop after the failing-test commit. Do not implement the fix in this phase.
