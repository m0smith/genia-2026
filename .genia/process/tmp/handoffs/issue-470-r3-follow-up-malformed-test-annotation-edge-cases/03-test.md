# === GENIA TEST ===

CHANGE NAME: issue #470 r3-follow-up-malformed-test-annotation-edge-cases
CHANGE SLUG: issue-470-r3-follow-up-malformed-test-annotation-edge-cases
ISSUE: #470
TYPE: feature
BRANCH: feature/issue-470-r3-follow-up-malformed-test-annotation-edge-cases

GENIA_STATE.md is final authority.

HARD STOP OBSERVED:
- TEST phase only.
- No implementation changes were made.
- No parser, lexer, Core IR, prelude, assertion helper, report formatter, host adapter, contract, design, or docs changes were made.
- The only documentation-style change is this TEST handoff.

---

## 0. BRANCH CHECK

Required branch:

```text
feature/issue-470-r3-follow-up-malformed-test-annotation-edge-cases
```

Result:
- Starting branch: `feature/issue-470-r3-follow-up-malformed-test-annotation-edge-cases`
- Working branch: `feature/issue-470-r3-follow-up-malformed-test-annotation-edge-cases`
- Branch already existed: YES
- Current branch matched required branch before edits: YES
- Stopped on main: NO
- Merge/rebase performed: NO

---

## 1. FILES CHANGED

- `tests/unit/test_native_test_cli.py`
- `.genia/process/tmp/handoffs/issue-470-r3-follow-up-malformed-test-annotation-edge-cases/03-test.md`

No implementation files were changed.

---

## 2. TESTS ADDED

Added direct `run_native_tests_from_file` coverage in `tests/unit/test_native_test_cli.py`:

- `test_native_test_cli_runs_valid_annotated_native_test`
- `test_native_test_cli_reports_empty_test_description_as_discovery_error`
- `test_native_test_cli_reports_test_on_non_function_as_discovery_error`
- `test_native_test_cli_reports_parameterized_annotated_function_as_discovery_error`
- `test_native_test_cli_reports_all_malformed_annotations_and_runs_valid_tests`
- `test_native_test_cli_preserves_malformed_annotation_reason_before_duplicate_name`
- `test_native_test_cli_reports_duplicate_valid_native_test_names`
- `test_native_test_cli_rejects_setup_annotation_instead_of_running_lifecycle_hook`

---

## 3. BEHAVIOR PROVED

- Valid annotated native tests still run and exit `0`.
- `@test ""` on a zero-argument function reports:
  - `ERROR bad_description phase=discovery reason=@test description must be a non-empty string`
  - exit code `1`
- `@test "not a function"` on a value binding reports:
  - `ERROR value phase=discovery reason=@test must annotate a function`
  - exit code `1`
- `@test "has a parameter"` on a parameterized function reports:
  - `ERROR needs_arg phase=discovery reason=@test functions must take zero arguments`
  - exit code `1`
- Multiple malformed annotated declarations are observable together when discovery is reached, and a valid annotated test in the same file still runs.
- A malformed annotated declaration with the same name as an explicit valid native test must preserve the malformed annotation reason and must not be replaced by:
  - `duplicate native test name: bad_duplicate`
- Duplicate valid native-test names still report:
  - `ERROR same_name phase=discovery reason=duplicate native test name: same_name`
  - exit code `1`
- `@setup` remains unsupported and does not become lifecycle setup behavior.

---

## 4. COMMANDS RUN

Focused changed tests:

```bash
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run pytest -q tests/unit/test_native_test_cli.py -v
```

Observed result:

```text
tests/unit/test_native_test_cli.py .....F........                        [100%]
1 failed, 13 passed
```

Nearby native-test regression coverage:

```bash
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run pytest -q tests/unit/test_native_test_runner.py -v
```

Observed result:

```text
26 passed
```

```bash
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run pytest -q tests/unit/test_native_test_kernel.py -v
```

Observed result:

```text
6 passed
```

`tests/unit/test_interpreter_test_mode.py` was not changed, so its phase-specific command was not required.

---

## 5. OBSERVED FAILING OUTPUT

The intended failing test is:

```text
tests/unit/test_native_test_cli.py::test_native_test_cli_preserves_malformed_annotation_reason_before_duplicate_name
```

Expected by Contract:

```text
ERROR bad_duplicate phase=discovery reason=@test description must be a non-empty string
```

Observed current implementation output:

```text
total=1 passed=0 failed=0 errored=1
ERROR bad_duplicate phase=discovery reason=duplicate native test name: bad_duplicate
total=1 passed=0 failed=0 errored=1
```

Pytest assertion excerpt:

```text
AssertionError: assert 'ERROR bad_duplicate phase=discovery reason=@test description must be a non-empty string\n' in 'total=1 passed=0 failed=0 errored=1\nERROR bad_duplicate phase=discovery reason=duplicate native test name: bad_duplicate\ntotal=1 passed=0 failed=0 errored=1\n'
```

This proves the implementation phase needs to preserve already-detected malformed annotated discovery errors before duplicate-name validation.

---

## 6. CASES INTENTIONALLY NOT TESTED

- Non-string `@test` metadata was not added as a discovery-error test in this phase because current annotation evaluation rejects non-string `@test` values before native-test discovery. The prompt says not to convert parse/evaluation failures into discovery errors.
- Bare missing-value `@test` syntax was not added because this phase must not require invalid Genia syntax to be accepted.
- Shared CLI spec fixtures were not added because the Contract and Design prefer focused unit tests first and no shared-spec promotion was required for this TEST phase.

---

## 7. FAILING-TEST COMMIT SHA

```text
cd2a407772a81d7241c6a6751bcf6aed4360bea0
```
