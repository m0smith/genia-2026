# Genia IMPLEMENTATION - Issue #458

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
already correct
```

---

## Files Changed

- `src/genia/evaluator.py`
- `src/genia/test_cli.py`
- `src/genia/test_kernel.py`
- `.genia/process/tmp/handoffs/issue-458-r3-contract-annotation-native-tests/04-implementation.md`

---

## Implementation Summary

- Added `@test` to the existing string annotation metadata path so annotated bindings keep `"test"` metadata instead of failing as unsupported annotations.
- Extended native test discovery to append `@test` annotated function groups after existing `test(name, body)` registrations.
- Valid annotated zero-argument functions are adapted into existing `TestUnit` values with the function name as the test name.
- Malformed annotated declarations are represented as existing native-test discovery errors.
- `run_native_tests_from_file` now uses the shared discovery helper after source evaluation, so `--test` sees both legacy and annotated tests.

---

## Scope Confirmation

Lifecycle behavior was not added.

No setup, teardown, before, after, fixture, module lifecycle, parameterized-test, parallel-runner, or R4 lifecycle behavior was introduced.

Legacy `test(name, body)` behavior remains supported and continues to run through the existing native test kernel.

---

## Commands Run

```bash
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run pytest -q tests/unit/test_interpreter_test_mode.py -v
```

Result:

```text
15 passed
```

```bash
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run pytest -q tests/unit/test_native_test_runner.py -v
```

Result:

```text
26 passed
```

```bash
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run pytest -q tests/unit/test_native_test_cli.py -v
```

Result:

```text
6 passed
```

```bash
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run pytest -q tests/unit/test_native_test_kernel.py -v
```

Result:

```text
6 passed
```

```bash
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run pytest -q tests/doc/test_semantic_doc_sync.py
```

Result:

```text
85 passed
```

```bash
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run ruff check src/genia/evaluator.py src/genia/test_cli.py src/genia/test_kernel.py tests/unit/test_interpreter_test_mode.py
```

Result:

```text
Failed: ruff was not installed in the uv environment.
```

```bash
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uvx ruff check src/genia/evaluator.py src/genia/test_cli.py src/genia/test_kernel.py tests/unit/test_interpreter_test_mode.py
```

Result:

```text
Failed under sandbox network restrictions while fetching ruff from PyPI.
```

```bash
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uvx ruff check src/genia/evaluator.py src/genia/test_cli.py src/genia/test_kernel.py tests/unit/test_interpreter_test_mode.py
```

Result after approved network access:

```text
All checks passed.
```

---

## Unexpected Findings

- The first focused run after accepting `@test` metadata still returned empty suites because `--test` was running the pre-evaluation legacy registration list directly. The fix was to route `--test` through the existing `discover_test_units(env)` helper after evaluation.

---

## Next Recommended Phase

DOC SYNC
