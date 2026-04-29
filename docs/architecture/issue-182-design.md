# === GENIA DESIGN ===

CHANGE NAME: #182 Extract collection and option helpers to prelude — Item A only

Issue: #182 (subtask of #117)
Phase: design
Branch: issue-182-extract-collections-options
Date: 2026-04-28
Pre-flight: `docs/architecture/issue-182-preflight.md`
Contract: `docs/architecture/issue-182-contract.md`

---

## 0. BRANCH DISCIPLINE

Current branch: `issue-182-extract-collections-options` ✓ (not `main`)
Matches pre-flight: ✓

---

## 1. PURPOSE

Translate Item A of the contract into an implementable structure.

Item A: Remove the dead `map_fn` and `filter_fn` Python function definitions and their `env.set(...)` registrations from `src/genia/interpreter.py`.

No behavior changes. No new files. No doc changes required.

---

## 2. SCOPE LOCK

### Included:

- Delete `map_fn` function definition from `src/genia/interpreter.py`.
- Delete `filter_fn` function definition from `src/genia/interpreter.py`.
- Delete `env.set("_map", map_fn)` from `src/genia/interpreter.py`.
- Delete `env.set("_filter", filter_fn)` from `src/genia/interpreter.py`.

### Excluded (per contract):

- No changes to `list.genia`.
- No changes to `option.genia`.
- No changes to `reduce_fn` or `_reduce` registration.
- No doc file changes — `_map` and `_filter` are not present in `GENIA_STATE.md`, `docs/host-interop/capabilities.md`, or `HOST_CAPABILITY_MATRIX.md`.
- No new tests — existing tests cover the invariants and must pass unchanged.
- No Items B or C.

---

## 3. ARCHITECTURE OVERVIEW

This change operates entirely within the Python reference host layer of the interpreter. It does not affect:

- the language contract
- Core IR
- any prelude `.genia` file
- the shared semantic spec YAML cases
- the host adapter boundary

The change is a pure deletion in a single file. `map` and `filter` remain fully functional via the prelude's `map_acc` and `filter_acc` helpers, which call `apply_raw` for callback invocation.

---

## 4. FILE / MODULE CHANGES

### New files: none

### Modified files:

- `src/genia/interpreter.py` — two function definitions deleted, two `env.set` calls deleted

### Removed files: none

---

## 5. DATA SHAPES

No new data shapes. No structural changes to the runtime environment beyond the removal of two names.

---

## 6. FUNCTION / INTERFACE DESIGN

### Deleted: `map_fn`

Current location: `src/genia/interpreter.py`, lines 7062–7068 (inside `_setup_builtins`).

```
def map_fn(f: Any, xs: Any) -> Any:
    """Host-backed map ..."""
    if not isinstance(xs, list):
        raise TypeError(...)
    return [_invoke_raw_from_builtin(f, [x]) for x in xs]
```

Action: delete entire function body.

### Deleted: `filter_fn`

Current location: `src/genia/interpreter.py`, lines 7070–7076 (inside `_setup_builtins`).

```
def filter_fn(predicate: Any, xs: Any) -> Any:
    """Host-backed filter ..."""
    if not isinstance(xs, list):
        raise TypeError(...)
    return [x for x in xs if truthy(_invoke_raw_from_builtin(predicate, [x]))]
```

Action: delete entire function body.

### Deleted: `env.set("_map", map_fn)`

Current location: `src/genia/interpreter.py`, line 7777.

Action: delete this line.

### Deleted: `env.set("_filter", filter_fn)`

Current location: `src/genia/interpreter.py`, line 7778.

Action: delete this line.

### Unchanged: `reduce_fn`, `env.set("_reduce", ...)`, `env.set("apply_raw", ...)`

These remain exactly as-is. `reduce_fn` is still referenced by the catch-all arm of `reduce` in `list.genia`.

---

## 7. CONTROL FLOW

No new control flow introduced. The execution path for `map(f, xs)` and `filter(predicate, xs)` is unchanged:

```
map(f, xs)
  → map_acc(f, xs, [])          [list.genia: prelude dispatch]
    → (f, [], acc) → acc        [base case]
    → (f, [x, ..rest], acc)     [recursive: apply_raw(f, [x])]
      → apply_raw(f, [x])       [host primitive: skip none propagation]
```

`_map` was never on this path on current main. Its removal does not alter any branch.

---

## 8. ERROR HANDLING DESIGN

### `map(f, non-list)`:

With `_map` removed, calling `map(f, non-list)` dispatches to `map_acc(f, non-list, [])`. `map_acc` has two arms:
- `(f, [], acc)` — requires empty list; does not match
- `(f, [x, ..rest], acc)` — requires non-empty list; does not match

Result: unmatched-case dispatch error. This is the **pre-existing behavior** since #190 — `_map` was never in the call chain for `map`. The removal does not change this.

### `filter(pred, non-list)`:

Same analysis. `filter_acc` raises an unmatched-case error on non-list input. Pre-existing since #190.

### `reduce(f, acc, non-list)`:

Unchanged. The catch-all arm delegates to `_reduce`, which raises the exact TypeError. Not affected by this change.

### Direct call to `_map` or `_filter` by name:

After removal, any code that directly calls `_map` or `_filter` by name will receive a `NameError`. This is intentional — these are internal symbols, never documented or supported as user-facing names.

---

## 9. INTEGRATION POINTS

- **`list.genia`**: not touched; `map` and `filter` delegate to `map_acc`/`filter_acc` via `apply_raw`, not `_map`/`_filter`.
- **Flow `map` and `filter`**: dispatch to the Flow kernel; not affected.
- **`_NONE_AWARE_PUBLIC_FUNCTIONS`**: `_map` and `_filter` are not in this set; their removal has no interaction with none-propagation logic.
- **`apply_raw`**: unchanged; continues to serve as the callback-invocation primitive for `map_acc` and `filter_acc`.
- **`_reduce`**: unchanged; continues to serve as the error-path delegate for `reduce`'s catch-all arm.

---

## 10. TEST DESIGN INPUT

No new tests are needed. The contract specifies that existing tests must pass unchanged.

Tests that validate the post-change state:

| Test | Invariant validated |
|---|---|
| `tests/test_list_hofs_190.py::TestMapBasic` | A1, A4 |
| `tests/test_list_hofs_190.py::TestFilterBasic` | A2, A5 |
| `tests/test_list_hofs_190.py::TestReduceBasic` | A3, A6 |
| `tests/test_list_hofs_190.py::TestReduceTypeError` | A7 |
| `tests/test_list_hofs_190.py::TestReduceNoneElements` | A8 |
| `tests/test_list_hofs_190.py::TestMapNoneElements` | A8 |
| `tests/test_list_hofs_190.py::TestFilterNoneElements` | A8 |
| `tests/test_list_hofs_190.py::TestReduceBasic::test_with_named_function` | A9 |
| `tests/test_list_hofs_190.py::TestFlowDispatchUnchanged` | A10 |
| `tests/cases/option/reduce_none_propagation.genia` | A8 regression |
| `spec/eval/reduce-on-flow-type-error.yaml` | A7 exact message |
| `spec/eval/stdlib-map-list-basic.yaml` | A1 |
| `spec/eval/stdlib-filter-list-basic.yaml` | A2 |

The implementation phase must run all of these and confirm they remain green.

---

## 11. DOC IMPACT

**None.** Inspection of `GENIA_STATE.md`, `docs/host-interop/capabilities.md`, and `docs/host-interop/HOST_CAPABILITY_MATRIX.md` confirms that `_map` and `_filter` are not documented as capabilities or named primitives in any of these files.

The `apply_raw` entry in `capabilities.md` (line 371) already accurately describes the current state: "The prelude list HOFs `reduce`, `map`, and `filter` use `apply_raw` directly for callback invocation." No change needed.

---

## 12. CONSTRAINTS

Must:
- Delete only `map_fn`, `filter_fn`, `env.set("_map", ...)`, `env.set("_filter", ...)` — nothing else.
- Leave `reduce_fn` and `env.set("_reduce", ...)` untouched.
- Leave `apply_raw_fn` and `env.set("apply_raw", ...)` untouched.
- Leave all prelude files untouched.

Must NOT:
- Touch `list.genia`.
- Touch `option.genia`.
- Alter `_NONE_AWARE_PUBLIC_FUNCTIONS`.
- Alter any shared spec YAML case.
- Introduce any new Python function or registration.

---

## 13. COMPLEXITY CHECK

[x] Minimal
[x] Necessary

### Explain:

Four deletions in one file. No new code. No structural changes. The simplest possible outcome consistent with the contract.

---

## 14. FINAL CHECK

- Matches contract exactly ✓
- No new behavior introduced ✓
- Structure is clear and implementable without ambiguity ✓
- Ready for implementation ✓

---

## IMPLEMENTATION SUMMARY

One file changes. Four deletions, nothing added.

```
src/genia/interpreter.py
  DELETE: def map_fn(...)       [lines ~7062–7068]
  DELETE: def filter_fn(...)    [lines ~7070–7076]
  DELETE: env.set("_map", ...)  [line ~7777]
  DELETE: env.set("_filter",..) [line ~7778]
```

Run full test suite to confirm zero regressions.
