# Failing Tests — Issue #451

CHANGE NAME: issue #451 r4-lifecycle-cleanup-failure-semantics
CHANGE SLUG: issue-451-r4-lifecycle-cleanup-failure-semantics

## 1. Branch report

- Starting branch: `feature/issue-451-r4-lifecycle-cleanup-failure-semantics`
- Working branch: `feature/issue-451-r4-lifecycle-cleanup-failure-semantics`
- Branch was already correct: yes

## 2. Input files read

- `AGENTS.md`
- `GENIA_STATE.md`
- `GENIA_RULES.md`
- `GENIA_REPL_README.md`
- `README.md`
- `docs/ai/LLM_CONTRACT.md`
- `docs/process/04-test.md`
- `docs/strategy/killer-workflow.md`
- `docs/strategy/release-roadmap.md`
- `.genia/process/tmp/handoffs/issue-451-r4-lifecycle-cleanup-failure-semantics/00-preflight.md`
- `.genia/process/tmp/handoffs/issue-451-r4-lifecycle-cleanup-failure-semantics/01-contract.md`
- `.genia/process/tmp/handoffs/issue-451-r4-lifecycle-cleanup-failure-semantics/02-design.md`

Note: `00-preflight.md` exists but is empty in this checkout. The prompt says to stop if required handoff files are missing; it was not missing.

## 3. Test plan

Files changed:

- `tests/unit/test_lifecycle_plan.py`
- `.genia/process/tmp/handoffs/issue-451-r4-lifecycle-cleanup-failure-semantics/03-failing-tests.md`

Behavior groups covered:

- cleanup policy validation and normalization
- failure policy validation and normalization
- result policy validation and normalization
- existing lifecycle plan regressions through the unchanged nearby tests

Contract invariants covered:

- entered scopes remain cleanup-eligible
- unentered scopes must not be configured for cleanup
- nested cleanup order is limited to the approved portable policy
- same-scope cleanup order is limited to approved reverse-order policies
- primary failures must remain preserved
- cleanup failures must remain preserved
- cleanup failures must not overwrite primary failures
- failure result ordering remains deterministic
- result context fields must remain boolean portable data
- no execution behavior, runner, annotation execution, or setup/teardown fixture is introduced

## 4. Files changed

- `tests/unit/test_lifecycle_plan.py`
- `.genia/process/tmp/handoffs/issue-451-r4-lifecycle-cleanup-failure-semantics/03-failing-tests.md`

## 5. Tests added

- `test_cleanup_normalizes_contract_safe_defaults_and_explicit_safe_values`
  - Proves an empty `cleanup` map normalizes to contract-safe defaults and explicit safe cleanup values are preserved.
- `test_cleanup_rejects_unsafe_or_nonportable_policy_values`
  - Proves `unentered_scope_cleanup: true`, unsupported `nested_order`, unsupported `same_scope_order`, non-boolean cleanup fields, and disabling entered-scope cleanup are rejected.
- `test_failure_policy_normalizes_contract_safe_defaults_and_explicit_safe_values`
  - Proves an empty `failure_policy` map normalizes to safe defaults and explicit safe failure values are preserved.
- `test_failure_rejects_policies_that_drop_or_overwrite_failures`
  - Proves policies that drop primary failures, drop cleanup failures, use unsupported primary/continuation policies, swallow cleanup failures, or let cleanup overwrite primary failure are rejected.
- `test_result_policy_normalizes_deterministic_defaults_and_explicit_safe_values`
  - Proves an empty `result_policy` map normalizes deterministic defaults and explicit safe result-policy values are preserved.
- `test_result_rejects_unsupported_or_nonportable_policy_values`
  - Proves unsupported failure ordering and non-boolean result context fields are rejected.

Existing regression coverage preserved by unchanged tests:

- `test_normalize_accepts_valid_lifecycle_plan_shape_and_defaults_always`
- `test_normalize_preserves_phase_order_exactly_as_declared`
- `test_validate_accepts_minimal_plan_and_phase_without_execution`
- `test_rejects_invalid_plan_shape_with_path_diagnostics`
- `test_rejects_invalid_phase_shape_with_path_diagnostics`
- `test_rejects_duplicate_phase_names_with_deterministic_diagnostic`
- `test_rejects_callable_phase_action_as_nonportable_behavior`

## 6. Commands run

```bash
git branch --show-current
```

Observed result:

```text
feature/issue-451-r4-lifecycle-cleanup-failure-semantics
```

```bash
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run pytest -q tests/unit/test_lifecycle_plan.py -v
```

Initial observed result after first draft:

```text
22 failed, 13 passed
```

Action taken: grouped safe-default and explicit-safe assertions so the same required coverage reports fewer than 20 failing test items.

Final observed result:

```text
19 failed, 13 passed
```

```bash
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run ruff check tests/unit/test_lifecycle_plan.py
```

Observed result:

```text
error: Failed to spawn: `ruff`
  Caused by: No such file or directory (os error 2)
```

No docs validation was run because this TEST-only phase did not edit docs.

## 7. Failing evidence

Expected failing tests:

- `test_cleanup_normalizes_contract_safe_defaults_and_explicit_safe_values`
  - Fails with `AttributeError: 'GeniaOptionNone' object has no attribute 'get'` because `normalize_lifecycle_plan` does not yet preserve or default `plan.cleanup`.
- `test_cleanup_rejects_unsafe_or_nonportable_policy_values`
  - Fails with `Failed: DID NOT RAISE <class 'ValueError'>` because unsafe cleanup policy fields are currently ignored.
- `test_failure_policy_normalizes_contract_safe_defaults_and_explicit_safe_values`
  - Fails with `AttributeError: 'GeniaOptionNone' object has no attribute 'get'` because `normalize_lifecycle_plan` does not yet preserve or default `plan.failure_policy`.
- `test_failure_rejects_policies_that_drop_or_overwrite_failures`
  - Fails with `Failed: DID NOT RAISE <class 'ValueError'>` because unsafe failure policy fields are currently ignored.
- `test_result_policy_normalizes_deterministic_defaults_and_explicit_safe_values`
  - Fails with `AttributeError: 'GeniaOptionNone' object has no attribute 'get'` because `normalize_lifecycle_plan` does not yet preserve or default `plan.result_policy`.
- `test_result_rejects_unsupported_or_nonportable_policy_values`
  - Fails with `Failed: DID NOT RAISE <class 'ValueError'>` because unsafe result policy fields are currently ignored.

Implementation gaps pointed to by the failures:

- add root-level `cleanup` map validation and default normalization
- add root-level `failure_policy` map validation and default normalization
- add root-level `result_policy` map validation and default normalization
- reject explicitly unsafe policy values with deterministic path-specific `ValueError` diagnostics

## 8. Ambiguities/blockers

- `src/genia/lifecycle_plan.py` does not yet expose stable `scopes` model support from issue #450. Per the prompt, scope-name and parent validation tests were not added in this phase.
- `00-preflight.md` exists but is empty. This was treated as an ambiguity rather than a blocker because the required file was present.
- `uv run ruff check ...` cannot run in this environment because `ruff` is not installed in the current `uv run` environment.

## 9. Next recommended phase

Implementation phase should make only these failing lifecycle-plan policy tests pass.

Recommended boundaries:

- keep the change in `src/genia/lifecycle_plan.py`
- add no lifecycle runner
- add no setup/teardown annotation execution
- add no command/file/pipe/repl lifecycle behavior
- add no native-test lifecycle fixtures unless the implementation prompt explicitly expands scope
- preserve existing lifecycle plan behavior and diagnostics outside the new policy fields
