# Genia Test Handoff — Issue #452

CHANGE NAME: issue #452 r4-lifecycle-annotation-binding-model
CHANGE SLUG: issue-452-r4-lifecycle-annotation-binding-model
TYPE: feature
ISSUE: 452
BRANCH: feature/issue-452-r4-lifecycle-annotation-binding-model
HANDOFF DIR: `.genia/process/tmp/handoffs/issue-452-r4-lifecycle-annotation-binding-model/`

## Branch

Starting branch: feature/issue-452-r4-lifecycle-annotation-binding-model
Working branch: feature/issue-452-r4-lifecycle-annotation-binding-model
Branch already existed or newly created: already existed

## Files Changed

- `tests/unit/test_lifecycle_binding.py`
- `tests/unit/test_native_test_cli.py`
- `.genia/process/tmp/handoffs/issue-452-r4-lifecycle-annotation-binding-model/03-test.md`

## Tests Added

Added `tests/unit/test_lifecycle_binding.py` with focused failing coverage for the approved lifecycle annotation binding helper contract:

- `test_optional_binding_with_zero_candidates_succeeds_without_diagnostics`
- `test_required_binding_with_zero_candidates_reports_deterministic_diagnostic`
- `test_annotation_name_matching_selects_only_matching_annotations`
- `test_exact_metadata_filters_include_matching_metadata`
- `test_exact_metadata_filters_exclude_non_matching_metadata`
- `test_callable_participant_kind_accepts_callable_values`
- `test_callable_participant_kind_rejects_non_callable_values_with_diagnostic`
- `test_source_order_ordering_is_deterministic`
- `test_reverse_source_order_ordering_is_deterministic`
- `test_stable_name_order_ordering_is_deterministic`
- `test_duplicate_participant_selection_reports_diagnostic_and_keeps_at_most_one_participant`
- `test_unsupported_ordering_reports_deterministic_error`

Added nearby native-test regression coverage in `tests/unit/test_native_test_cli.py`:

- `test_native_test_cli_ignores_non_test_metadata_annotations_for_discovery`
- `test_test_annotation_does_not_execute_outside_native_test_mode`

Existing nearby coverage already proves valid `@test` discovery still works.

## Expected Failing Command

```bash
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run pytest -q tests/unit/test_lifecycle_binding.py -v
```

## Failing Output Summary

The focused lifecycle binding suite collected 12 tests and all 12 failed:

```text
tests/unit/test_lifecycle_binding.py FFFFFFFFFFFF
ModuleNotFoundError: No module named 'genia.lifecycle_binding'
12 failed in 0.32s
```

## Reason The Tests Fail

The tests intentionally target the later implementation module from the approved design:

```text
src/genia/lifecycle_binding.py
```

That module does not exist yet. This is the expected TEST-phase failure boundary. No placeholder module was added because importing the missing target is enough to fail clearly before implementation.

## Validation Run

Focused red lifecycle binding command:

```bash
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run pytest -q tests/unit/test_lifecycle_binding.py -v
```

Result: expected failure, 12 failed with `ModuleNotFoundError: No module named 'genia.lifecycle_binding'`.

Native-test regression command:

```bash
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run pytest -q tests/unit/test_native_test_cli.py -v
```

Result: 19 passed.

Focused lint command:

```bash
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uvx ruff check tests/unit/test_lifecycle_binding.py tests/unit/test_native_test_cli.py
```

Result: All checks passed.

Initial local `uv run ruff ...` failed because `ruff` was not installed in the project environment. `uvx ruff ...` required network access and then passed.

## No Implementation Done

No implementation was done in this phase.

No parser, lexer, Core IR, evaluator, runtime lifecycle execution, CLI behavior, native test behavior, public builtins, prelude functions, lifecycle runner, setup/teardown behavior, module/server/actor/REPL lifecycle behavior, or docs outside this handoff were changed.

## Recommended Implementation Target Files

- `src/genia/lifecycle_binding.py`
- `src/genia/test_cli.py`, only if later implementation routes native-test discovery through the helper while preserving current observable behavior

## Risks Or Follow-ups

- The new unit tests define the expected internal Python helper API names from the approved design: `LifecycleAnnotationBinding`, `AnnotationCandidate`, `AnnotationInfo`, `discover_lifecycle_participants`, result participants, and diagnostics.
- Unsupported ordering is expected to raise `ValueError` with a deterministic path-style message.
- Callable participant validation is currently specified using Python callability for the internal helper tests; later implementation should reconcile this with existing Genia runtime/native-test function-group callability without changing current native-test behavior.
- The prompt asked to read `docs/process/03-test.md`, but that file is absent in this checkout. The available process files include `docs/process/04-test.md`.
