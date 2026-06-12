# Test — Issue #480: R3 Non-String Test Metadata Boundary

## Branch

- Starting branch: `feature/issue-480-r3-non-string-test-metadata-boundary`
- Working branch: `feature/issue-480-r3-non-string-test-metadata-boundary`
- Branch status: already existed; no branch creation or switch was needed in this phase

## Selected Metadata Boundary Policy

Policy A: string-only metadata.

- Native test metadata keys must be strings.
- Native test metadata values must be strings.
- Composite metadata values such as lists and maps are invalid.
- Invalid native test metadata must surface as deterministic discovery errors.
- When a test unit location is available, invalid metadata diagnostics should include it.

This is the smallest boundary that matches the current Genia direction: existing annotation metadata for `@test`, `@doc`, `@since`, `@deprecated`, and `@category` is string-valued, and current native-test metadata already uses string fields such as `description` and `discovery_error`.

## Files Changed

- `tests/unit/test_native_test_kernel.py`
- `.genia/process/tmp/handoffs/issue-480-r3-non-string-test-metadata-boundary/03-test.md`

## Tests Added

- `test_valid_string_test_metadata_remains_accepted`
- `test_non_string_metadata_value_is_discovery_error_with_location`
- `test_composite_metadata_values_are_discovery_errors`
- `test_non_string_metadata_key_is_discovery_error`

The existing duplicate-name/location-oriented CLI coverage remains unchanged and continues to pass:

- `test_native_test_cli_reports_duplicate_valid_native_test_names`
- `test_native_test_cli_preserves_malformed_annotation_reason_before_duplicate_name`

## Commands Run

```bash
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run pytest -q tests/unit/test_native_test_kernel.py tests/unit/test_native_test_cli.py -k 'metadata or native or duplicate'
```

Result: expected failure, `3 failed, 21 passed`.

Failing tests:

- `tests/unit/test_native_test_kernel.py::test_non_string_metadata_value_is_discovery_error_with_location`
- `tests/unit/test_native_test_kernel.py::test_composite_metadata_values_are_discovery_errors`
- `tests/unit/test_native_test_kernel.py::test_non_string_metadata_key_is_discovery_error`

Failure summary: invalid metadata currently passes through as normal native tests instead of becoming discovery errors.

```bash
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run pytest -q tests/unit/test_native_test_cli.py -k 'metadata or native'
```

Result: `14 passed`.

```bash
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run pytest -q tests/unit/test_native_test_cli.py
```

Result: `14 passed`.

```bash
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run pytest -q tests/unit/test_native_test_runner.py
```

Result: `26 passed`.

```bash
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run pytest -q tests/unit/test_native_test_kernel.py
```

Result: expected failure, `3 failed, 7 passed`.

Failing tests:

- `tests/unit/test_native_test_kernel.py::test_non_string_metadata_value_is_discovery_error_with_location`
- `tests/unit/test_native_test_kernel.py::test_composite_metadata_values_are_discovery_errors`
- `tests/unit/test_native_test_kernel.py::test_non_string_metadata_key_is_discovery_error`

## Existing Unrelated Failures

None observed in the focused native-test suites run during this phase.

## Commit

- Failing-test commit SHA: `PENDING`

## Implementation Status

Implementation has not been done in this phase.
