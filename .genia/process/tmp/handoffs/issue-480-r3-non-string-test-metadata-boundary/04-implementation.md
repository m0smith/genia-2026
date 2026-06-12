# Implementation — Issue #480: R3 Non-String Test Metadata Boundary

## Branch

- Starting branch: `feature/issue-480-r3-non-string-test-metadata-boundary`
- Working branch: `feature/issue-480-r3-non-string-test-metadata-boundary`
- Branch status: already existed; no branch creation or switch was needed in this phase

## Failing-Test Commit Referenced

- `4df6fef6bca0b1333946ac8f4ebb9a35382ffe30`

## Selected Policy Confirmed

Policy A: native test metadata keys and values must be strings.

Invalid metadata is reported as a deterministic discovery error before the native test body is run.

## Implementation Summary

- Added one metadata validation boundary in `src/genia/test_kernel.py`.
- `run_test_unit(...)` now checks native test metadata after test-unit name validation and before discovery-error/body validation.
- Invalid metadata keys report:
  - `invalid native test metadata key: expected string, received <type>`
- Invalid metadata values report:
  - `invalid native test metadata value for key '<key>': expected string, received <type>`
- Existing `TestUnit.location` is appended when it is already available.
- Diagnostics use Genia runtime type names rather than raw Python `repr`.
- Existing valid string metadata, explicit discovery errors, duplicate-name discovery behavior, and native-test reporting remain unchanged.

## Files Changed

- `src/genia/test_kernel.py`
- `.genia/process/tmp/handoffs/issue-480-r3-non-string-test-metadata-boundary/04-implementation.md`

## Commands Run

```bash
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run pytest -q tests/unit/test_native_test_kernel.py -k 'metadata'
```

Result: `4 passed, 6 deselected`.

```bash
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run pytest -q tests/unit/test_native_test_kernel.py tests/unit/test_native_test_cli.py -k 'metadata or native or duplicate'
```

Result: `24 passed`.

```bash
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run pytest -q tests/unit/test_native_test_kernel.py
```

Result: `10 passed`.

```bash
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run pytest -q tests/unit/test_native_test_cli.py
```

Result: `14 passed`.

```bash
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run pytest -q tests/unit/test_native_test_runner.py
```

Result: `26 passed`.

```bash
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run pytest -q tests/unit/test_interpreter_test_mode.py
```

Result: `20 passed`.

```bash
uv run ruff check src/genia/test_kernel.py tests/unit/test_native_test_kernel.py
```

Result: not run successfully; `ruff` is not installed in the project environment (`Failed to spawn: ruff`).

## Implementation Commit SHA

- Commit SHA: recorded in final phase report after commit creation.

## Known Follow-Ups

- Docs sync has not been done in this phase.
- Audit has not been done in this phase.
