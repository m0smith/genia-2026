# Test: issue #454 r4-native-test-lifecycle-first-consumer

CHANGE NAME: issue #454 r4-native-test-lifecycle-first-consumer
CHANGE SLUG: issue-454-r4-native-test-lifecycle-first-consumer
ISSUE: #454 -- "R4 lifecycle: align native test lifecycle as the first implemented consumer"
BRANCH: feature/issue-454-r4-native-test-lifecycle-first-consumer
TYPE: test
HANDOFF DIR: .genia/process/tmp/handoffs/issue-454-r4-native-test-lifecycle-first-consumer/

## Branch confirmation

- Starting branch: `feature/issue-454-r4-native-test-lifecycle-first-consumer`
- Working branch: `feature/issue-454-r4-native-test-lifecycle-first-consumer`
- Branch already existed: yes; the checkout was already on the required branch before edits.
- Did not work on `main`.
- Did not merge or rebase.

## Files changed

- `tests/unit/test_native_test_lifecycle_consumer.py`
- `.genia/process/tmp/handoffs/issue-454-r4-native-test-lifecycle-first-consumer/03-test.md`

No implementation files were modified.

## Failing tests added

Added focused TEST-phase coverage for the future internal module:

```text
genia.native_test_lifecycle
```

Expected future API:

```text
native_test_lifecycle_plan()
native_test_lifecycle_scope_tree()
validate_native_test_lifecycle()
```

The tests assert:

- `native_test_lifecycle_plan()` returns inert `GeniaMap` plan-shaped data.
- The plan validates and normalizes through existing lifecycle plan helpers.
- Plan phase names are exactly `discover`, `run`, `report`.
- `native_test_lifecycle_scope_tree()` returns inert `GeniaMap` scope-tree-shaped data.
- The scope tree validates and normalizes through existing lifecycle scope helpers.
- The scope hierarchy is exactly `execution -> suite -> module -> test`.
- `validate_native_test_lifecycle()` returns validated data containing `plan` and `scope_tree`.
- Descriptor actions are identifier symbols, not Python callables.
- The descriptor does not expose lifecycle phase execution APIs.

Regression coverage was inspected in the nearby native-test tests. Existing tests already cover the requested behavior-preservation targets, including legacy units before `@test` units, appended annotated units, deterministic duplicate-name diagnostics, malformed `@test` diagnostics, all-pass exit `0`, fail/error exit `1`, and no-test / invalid invocation exit `2`. No nearby native-test files were changed.

## Validation commands run

```bash
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run pytest -q tests/unit/test_native_test_lifecycle_consumer.py
```

Result:

```text
9 failed in 0.24s
```

All 9 failures are the expected TEST-phase red signal:

```text
ModuleNotFoundError: No module named 'genia.native_test_lifecycle'
```

The failures occur when the tests import the future module boundary through:

```text
importlib.import_module("genia.native_test_lifecycle")
```

## Implementation status

No implementation files were modified.

The tests fail for the expected reason: the native test lifecycle consumer module/API does not exist yet.

## Next phase instruction

The next phase is IMPLEMENTATION only.

Implementation must make these tests pass by adding the smallest behavior-neutral native-test lifecycle consumer. It must preserve observable native-test behavior exactly: no CLI output changes, no exit-code changes, no discovery-order changes, no duplicate or malformed annotation diagnostic changes, no lifecycle phase execution, no setup/teardown, no action registry, no lifecycle runner, and no public Genia prelude lifecycle API.
