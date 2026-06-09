# Genia Test Handoff - Issue #463

CHANGE NAME: issue #463 r3-native-tests-jsonl-helper  
CHANGE SLUG: issue-463-r3-native-tests-jsonl-helper  
TYPE: feature  
ISSUE: 463  
BRANCH: feature/issue-463-r3-native-tests-jsonl-helper  
HANDOFF DIR: `.genia/process/tmp/handoffs/issue-463-r3-native-tests-jsonl-helper/`

## Branch

Starting branch: `feature/issue-463-r3-native-tests-jsonl-helper`  
Working branch: `feature/issue-463-r3-native-tests-jsonl-helper`  
Branch status: already checked out

## Files Changed

- `tests/native/jsonl_helper_behavior.genia`
- `tests/unit/test_jsonl_helper_native_tests.py`
- `.genia/process/tmp/handoffs/issue-463-r3-native-tests-jsonl-helper/03-test.md`

## Tests Added

Added Genia-native `@test` coverage for current `parse_jsonl_record(line)` behavior:

- `valid_json_object_returns_record_with_context`
- `blank_line_returns_absence_with_context`
- `malformed_json_returns_recoverable_failure_with_context`
- `non_object_json_returns_recoverable_failure_with_context`
- `all_jsonl_outcomes_preserve_exact_original_line_context`

Added a narrow pytest wrapper:

- `tests/unit/test_jsonl_helper_native_tests.py::test_jsonl_helper_native_tests_pass`

## Behavior Covered

The native fixture proves:

- valid JSON object lines return `some(parsed_record, context)`
- blank or whitespace-only lines return `none("blank_line", context)`
- malformed JSON lines return `err(quote(invalid_jsonl_record), context)`
- valid non-object JSON returns `err(quote(jsonl_record_not_object), context)`
- each recoverable Outcome preserves the exact original input string in `context.line`

The tests use current Genia-native pattern matching and the existing `assert_eq` helper only.

## Commands Run

```bash
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run pytest -q tests/unit/test_jsonl_helper_native_tests.py -v
```

Observed:

```text
tests/unit/test_jsonl_helper_native_tests.py . [100%]
1 passed in 0.08s
```

```bash
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run pytest -q tests/unit/test_native_test_runner.py -v
```

Observed:

```text
tests/unit/test_native_test_runner.py .......................... [100%]
26 passed in 0.29s
```

```bash
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run pytest -q tests/unit/test_native_test_cli.py -v
```

Observed:

```text
tests/unit/test_native_test_cli.py ...... [100%]
6 passed in 0.09s
```

```bash
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run pytest -q tests/unit/test_native_test_kernel.py -v
```

Observed:

```text
tests/unit/test_native_test_kernel.py ...... [100%]
6 passed in 0.08s
```

```bash
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run pytest -q tests/unit/test_r1_validated_pipeline_native_tests.py -v
```

Observed:

```text
tests/unit/test_r1_validated_pipeline_native_tests.py . [100%]
1 passed in 0.13s
```

## Failure Evidence

No failing output was observed. The TEST prompt requested a failing-test commit, but the approved contract/design handoffs define this issue as native coverage for already-implemented current `parse_jsonl_record` behavior. The new native tests pass without production changes.

## Production Changes

No production implementation was changed.

## Commit

Failing-test commit SHA: pending
