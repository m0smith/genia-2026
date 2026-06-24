# === GENIA TEST PHASE ===

CHANGE NAME: issue #490 r4-scope-validator-edge-tests
CHANGE SLUG: issue-490-r4-scope-validator-edge-tests
ISSUE: #490
TYPE: feature
BRANCH: feature/issue-490-r4-scope-validator-edge-tests
HANDOFF DIR: .genia/process/tmp/handoffs/issue-490-r4-scope-validator-edge-tests
OUTPUT: .genia/process/tmp/handoffs/issue-490-r4-scope-validator-edge-tests/03-test.md

GENIA_STATE.md is final authority.

STOP: TEST phase only. Implementation has not begun.

---

## 0. BRANCH INFORMATION

Starting branch:

```text
feature/issue-490-r4-scope-validator-edge-tests
```

Working branch:

```text
feature/issue-490-r4-scope-validator-edge-tests
```

Branch status:

- Branch already existed.
- Worktree was clean before TEST edits.
- No work was performed on `main`.

Process note:

- The prompt named `docs/process/03-test.md`, but this branch has `docs/process/04-test.md`.
- The repo's test-phase template names `03-failing-tests.md`; the user prompt explicitly requested this file, `03-test.md`.
- The approved preflight/contract/design handoffs target lifecycle scope-tree validation in `tests/unit/test_lifecycle_scope.py`, not lifecycle-plan validation in `tests/unit/test_lifecycle_plan.py`. The plan test file was run only as nearby regression coverage.

---

## 1. SCOPE SUMMARY

Added focused edge/regression coverage for the existing R4 lifecycle scope-tree validator.

Covered approved issue #490 edge cases:

- invalid root `description` type
- invalid root `metadata` type
- `parent = some(non-symbol)`
- explicit unsupported `source` and `flow` scope names
- non-root scope using `none` parent

No production behavior was changed.

---

## 2. TESTS ADDED

Updated:

```text
tests/unit/test_lifecycle_scope.py
```

Added/expanded tests:

- `test_rejects_non_string_root_description`
- `test_rejects_non_map_root_metadata`
- `test_rejects_some_non_symbol_parent`
- `test_rejects_unsupported_scope_names_with_supported_scope_hint` now includes `source` and `flow`
- `test_rejects_non_root_scope_with_none_parent`

The tests use existing helpers and assert deterministic path-specific diagnostics.

---

## 3. VALIDATION COMMANDS AND OUTPUT SUMMARY

Initial sandbox attempt:

```bash
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run pytest -q tests/unit/test_lifecycle_scope.py -v
```

Result:

```text
Failed before test execution while resolving hatchling from PyPI due sandbox/network DNS failure.
```

Focused validation after dependency resolution:

```bash
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run pytest -q tests/unit/test_lifecycle_scope.py -v
```

Result:

```text
20 passed in 0.14s
```

Nearby lifecycle regression validation:

```bash
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run pytest -q tests/unit/test_lifecycle_plan.py tests/unit/test_lifecycle_scope.py -v
```

Result:

```text
52 passed in 0.23s
```

---

## 4. FAILING EVIDENCE

No implementation-gap failure remains.

The new edge tests pass against current `src/genia/lifecycle_scope.py`, confirming the approved behavior was already implemented and only missing focused coverage.

Transient test-authoring correction:

- First real pytest run reported 2 failures in `test_rejects_some_non_symbol_parent`.
- The validator produced the expected messages, but the test regex did not escape `some(string)` / `some(int)` parentheses.
- The test assertion was corrected before committing.

Final failing tests:

```text
None.
```

Expected phase interpretation:

- This is acceptable under `02-design.md`, which states the TEST phase is expected to produce tests that already pass if the validator already implements all five behaviors.
- Implementation phase should be a no-op unless the process requires a separate no-op handoff.

---

## 5. FILES CHANGED

```text
tests/unit/test_lifecycle_scope.py
.genia/process/tmp/handoffs/issue-490-r4-scope-validator-edge-tests/03-test.md
```

No production code changed.
No source-of-truth docs changed.
No parser, Core IR, prelude, CLI, native-test runner, runtime, or host adapter code changed.

---

## 6. STOP MARKER

STOP.

TEST phase is complete.
Implementation has not begun.
Do not continue into implementation without an explicit implementation-phase prompt.
