# Implementation — Issue #451

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
- `docs/strategy/killer-workflow.md`
- `docs/strategy/release-roadmap.md`
- `.genia/process/tmp/handoffs/issue-451-r4-lifecycle-cleanup-failure-semantics/01-contract.md`
- `.genia/process/tmp/handoffs/issue-451-r4-lifecycle-cleanup-failure-semantics/02-design.md`
- `.genia/process/tmp/handoffs/issue-451-r4-lifecycle-cleanup-failure-semantics/03-failing-tests.md`

Also checked:

- `.genia/process/tmp/handoffs/issue-451-r4-lifecycle-cleanup-failure-semantics/00-preflight.md`

Notes:

- `00-preflight.md` exists but is empty in this checkout.
- `docs/process/05-implementation.md` does not exist in this checkout, so it could not be read.

## 3. Files changed

- `src/genia/lifecycle_plan.py`
- `.genia/process/tmp/handoffs/issue-451-r4-lifecycle-cleanup-failure-semantics/04-implementation.md`

## 4. Implementation summary

Added:

- root-level `cleanup` policy normalization and validation when `plan.cleanup` is present
- root-level `failure_policy` normalization and validation when `plan.failure_policy` is present
- root-level `result_policy` normalization and validation when `plan.result_policy` is present
- contract-safe defaults for present empty policy maps
- deterministic path-specific `ValueError` diagnostics for unsafe or unsupported policy values
- preservation of omitted policy fields for backward compatibility with existing minimal lifecycle plans

Deliberately not added:

- no lifecycle runner
- no setup/teardown annotation execution
- no annotation discovery
- no command/file/pipe/repl lifecycle behavior
- no native-test lifecycle execution fixtures
- no docs sync
- no public API beyond the existing `normalize_lifecycle_plan` and `validate_lifecycle_plan` boundary

## 5. Tests fixed

Formerly failing tests now passing:

- `test_cleanup_normalizes_contract_safe_defaults_and_explicit_safe_values`
- `test_cleanup_rejects_unsafe_or_nonportable_policy_values`
- `test_failure_policy_normalizes_contract_safe_defaults_and_explicit_safe_values`
- `test_failure_rejects_policies_that_drop_or_overwrite_failures`
- `test_result_policy_normalizes_deterministic_defaults_and_explicit_safe_values`
- `test_result_rejects_unsupported_or_nonportable_policy_values`

Existing regression tests also still pass:

- minimal valid lifecycle plan normalization
- phase order preservation
- phase `always` default
- callable phase action rejection
- deterministic path diagnostics for existing plan/phase validation

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

Observed result:

```text
32 passed in 0.14s
```

```bash
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run pytest -q tests/doc/test_lifecycle_architecture_doc.py tests/doc/test_semantic_doc_sync.py
```

Observed result:

```text
92 passed in 0.41s
```

```bash
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run ruff check src/genia/lifecycle_plan.py tests/unit/test_lifecycle_plan.py
```

Observed result:

```text
error: Failed to spawn: `ruff`
  Caused by: No such file or directory (os error 2)
```

## 7. Ruff result

Ruff was unavailable in the current `uv run` environment:

```text
error: Failed to spawn: `ruff`
  Caused by: No such file or directory (os error 2)
```

## 8. Scope guardrails observed

- no runner
- no annotations
- no docs
- no CLI/native-test execution changes
- no parser, IR, evaluator, builtins, interpreter, test CLI, or native test runner changes
- production edit stayed in `src/genia/lifecycle_plan.py`

## 9. Next recommended phase

Proceed to test verification and then docs sync according to the local process.

Docs sync should describe only the validation/data-shape behavior actually implemented here, avoid implying lifecycle execution, and keep annotation/setup/teardown behavior out of current-state claims.
