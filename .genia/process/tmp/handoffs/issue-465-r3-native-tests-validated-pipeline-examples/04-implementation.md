# Genia IMPLEMENTATION - Issue #465

CHANGE NAME: issue #465 r3-native-tests-validated-pipeline-examples
CHANGE SLUG: issue-465-r3-native-tests-validated-pipeline-examples
TYPE: feature
ISSUE: 465
BRANCH: feature/issue-465-r3-native-tests-validated-pipeline-examples

## Phase

IMPLEMENTATION ONLY

## Failing-test commit SHA

```text
19c197a6a37394b14efbbc73299117841bdbaf55
```

## Branches

- Starting branch: `feature/issue-465-r3-native-tests-validated-pipeline-examples`
- Working branch: `feature/issue-465-r3-native-tests-validated-pipeline-examples`
- Branch status: already existed

## Files changed

- `examples/r3_validated_pipeline_native_tests.genia`
- `.genia/process/tmp/handoffs/issue-465-r3-native-tests-validated-pipeline-examples/04-implementation.md`

## Implementation summary

Added `examples/r3_validated_pipeline_native_tests.genia`, a runnable native-test example file using existing `test(name, body)` syntax, current assertion helpers, and current validation/Outcome helpers only.

The example contains three native tests matching the TEST-phase harness:

- `validated pipeline preserves upstream Outcome boundaries`
- `validate_each feeds collect_validated directly`
- `validated JSONL pipeline keeps clean records and diagnostics observable`

No parser, runtime, validation helper, assertion helper, native-test framework, CLI, docs, lifecycle, actor, browser, or playground behavior was changed.

## Commands run

```bash
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run pytest -q tests/unit/test_r3_validated_pipeline_native_test_examples.py -v
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run pytest -q tests/unit/test_r3_validation_helpers_native_tests.py -v
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run pytest -q tests/unit/test_native_test_runner.py -v
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run pytest -q tests/unit/test_native_test_cli.py -v
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run pytest -q tests/unit/test_native_test_kernel.py -v
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run pytest -q tests/unit/test_r1_validated_pipeline_native_tests.py -v
```

## Validation results

- `tests/unit/test_r3_validated_pipeline_native_test_examples.py`: 1 passed
- `tests/unit/test_r3_validation_helpers_native_tests.py`: 1 passed
- `tests/unit/test_native_test_runner.py`: 26 passed
- `tests/unit/test_native_test_cli.py`: 6 passed
- `tests/unit/test_native_test_kernel.py`: 6 passed
- `tests/unit/test_r1_validated_pipeline_native_tests.py`: 1 passed

## Implementation commit SHA

Final SHA is reported after the commit is created. The SHA cannot be embedded in this same committed file without changing the commit identity.

## Phase boundary

Docs sync and audit were not performed in this phase. Stop after the implementation commit.
