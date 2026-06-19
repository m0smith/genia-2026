# Implementation: issue #454 r4-native-test-lifecycle-first-consumer

CHANGE NAME: issue #454 r4-native-test-lifecycle-first-consumer
CHANGE SLUG: issue-454-r4-native-test-lifecycle-first-consumer
ISSUE: #454 -- "R4 lifecycle: align native test lifecycle as the first implemented consumer"
BRANCH: feature/issue-454-r4-native-test-lifecycle-first-consumer
TYPE: implementation
HANDOFF DIR: .genia/process/tmp/handoffs/issue-454-r4-native-test-lifecycle-first-consumer/

## Branch confirmation

- Starting branch: `feature/issue-454-r4-native-test-lifecycle-first-consumer`
- Working branch: `feature/issue-454-r4-native-test-lifecycle-first-consumer`
- Branch already existed: yes; the checkout was already on the required branch before edits.
- Did not work on `main`.
- Did not merge or rebase.

## Referenced failing-test commit

```text
d477a67017e697580c4b819786b6b7110a6fb568
```

## Files changed

- `src/genia/native_test_lifecycle.py`
- `src/genia/test_cli.py`
- `.genia/process/tmp/handoffs/issue-454-r4-native-test-lifecycle-first-consumer/04-implementation.md`

## Implementation summary

- Added `src/genia/native_test_lifecycle.py` with:
  - `native_test_lifecycle_plan()`
  - `native_test_lifecycle_scope_tree()`
  - `validate_native_test_lifecycle()`
- The descriptor uses existing `GeniaMap`, `GeniaSymbol`, `OPTION_NONE`, and `GeniaOptionSome` value conventions.
- The lifecycle plan describes the current native test phases as `discover -> run -> report`.
- The lifecycle scope tree describes the canonical R4 hierarchy `execution -> suite -> module -> test`.
- `validate_native_test_lifecycle()` normalizes the plan and scope tree through the existing lifecycle helpers.
- Integrated `validate_native_test_lifecycle()` into `src/genia/test_cli.py::run_native_tests_from_file(...)` as a silent behavior-neutral validation call.
- Did not route `@test` discovery through `discover_lifecycle_participants(...)`.
- Did not add lifecycle execution, action resolution, setup/teardown, a lifecycle runner, or a public prelude API.

Observable native-test behavior was not intentionally changed.

No docs sync was performed in this phase.

## Validation commands run

```bash
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run pytest -q tests/unit/test_native_test_lifecycle_consumer.py
```

Result:

```text
9 passed in 0.08s
```

```bash
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run pytest -q tests/unit/test_native_test_cli.py tests/unit/test_native_test_runner.py tests/unit/test_native_test_kernel.py tests/unit/test_interpreter_test_mode.py
```

Result:

```text
75 passed in 0.59s
```

```bash
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run pytest -q
```

Result:

```text
8 failed, 2590 passed in 231.26s (0:03:51)
```

Failure summary:

```text
PermissionError: [Errno 1] Operation not permitted
```

The 8 failures were local-socket HTTP/demo tests blocked by the sandbox:

- `tests/demo/test_ants_web_demo.py::test_ants_web_http_routes_serve_assets_and_state_updates`
- `tests/unit/test_http_web.py`

Reran the failed HTTP/demo subset outside the sandbox:

```bash
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run pytest -q tests/demo/test_ants_web_demo.py::test_ants_web_http_routes_serve_assets_and_state_updates tests/unit/test_http_web.py
```

Result:

```text
8 passed in 0.93s
```

Attempted touched-file lint:

```bash
uv run ruff check src/genia/native_test_lifecycle.py src/genia/test_cli.py tests/unit/test_native_test_lifecycle_consumer.py
```

Result:

```text
error: Failed to spawn: `ruff`
Caused by: No such file or directory (os error 2)
```

## Next phase instruction

The next phase is DOCS SYNC only.

Docs sync should document only the implemented, verified internal native-test lifecycle consumer descriptor and must continue to state that there is no lifecycle runner, no phase execution, no setup/teardown, no discovery-routing through lifecycle binding, no observable native-test behavior change, and no public lifecycle prelude API.
