# Genia TEST - Issue #458

CHANGE NAME: issue #458 r3-contract-annotation-native-tests  
CHANGE SLUG: issue-458-r3-contract-annotation-native-tests  
TYPE: feature  
ISSUE: 458  
BRANCH: feature/issue-458-r3-contract-annotation-native-tests  
HANDOFF DIR: `.genia/process/tmp/handoffs/issue-458-r3-contract-annotation-native-tests/`

---

## Branch

Starting branch:

```text
feature/issue-458-r3-contract-annotation-native-tests
```

Working branch:

```text
feature/issue-458-r3-contract-annotation-native-tests
```

Branch status:

```text
already existed and was already checked out
```

---

## Phase Scope

TEST phase only.

Production files were not changed. Documentation was not updated beyond this test handoff.

---

## Files Changed

- `tests/unit/test_interpreter_test_mode.py`
- `.genia/process/tmp/handoffs/issue-458-r3-contract-annotation-native-tests/03-test.md`

---

## Failing Tests Added

Added focused failing tests for R3 annotation-native test discovery through the existing native test mode report surface:

- annotated zero-argument function discovery and PASS result
- annotated assertion failure reported as FAIL, not ERROR
- annotated unexpected runtime error reported as ERROR
- mixed legacy `test(name, body)` and annotated tests in deterministic order
- annotated parameterized function reported as discovery ERROR
- lifecycle non-goal guardrail proving an ordinary unannotated `setup()` function is not treated as a lifecycle hook

The tests use existing prefix annotation syntax:

```genia
@test "description"
passes() = assert_true(true)
```

This avoids adding parser syntax in the TEST phase.

---

## Test Command

```bash
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run pytest -q tests/unit/test_interpreter_test_mode.py -v
```

Result:

```text
6 failed, 9 passed
```

Expected failure cause:

```text
Error: Unsupported annotation: @test. Supported annotations: @doc, @meta, @since, @deprecated, @category
```

Representative failing tests:

```text
FAILED tests/unit/test_interpreter_test_mode.py::test_test_mode_discovers_annotated_zero_arg_function
FAILED tests/unit/test_interpreter_test_mode.py::test_test_mode_reports_annotated_assertion_failure_as_failure
FAILED tests/unit/test_interpreter_test_mode.py::test_test_mode_reports_annotated_runtime_error_as_error
FAILED tests/unit/test_interpreter_test_mode.py::test_test_mode_runs_legacy_and_annotated_tests_in_deterministic_order
FAILED tests/unit/test_interpreter_test_mode.py::test_test_mode_reports_annotated_parameterized_function_as_discovery_error
FAILED tests/unit/test_interpreter_test_mode.py::test_test_mode_does_not_treat_unannotated_setup_as_lifecycle_hook
```

---

## Next Phase

Implementation phase should make `@test` annotation metadata discoverable by native test mode, validate annotated functions before execution, feed valid annotated tests into the existing native test kernel, and preserve current `test(name, body)` behavior.
