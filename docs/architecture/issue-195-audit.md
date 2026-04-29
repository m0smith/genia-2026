# Audit: Issue #195 — _map/_filter host cleanup verification

**Issue:** #195  
**Branch:** `issue-cleanup-map-filter-host-leftovers`  
**Phase:** audit  
**Date:** 2026-04-29  
**Verdict:** PASS

---

## Audit checklist and evidence

Each item below was verified independently via fresh grep and test execution — not taken on trust from the pre-flight.

---

### A1 — No `env.set("_map", ...)` registration in interpreter.py

```
grep -n 'env\.set' src/genia/interpreter.py | grep '"_map"'
```

**Result: no output.** Confirmed absent.

---

### A2 — No `env.set("_filter", ...)` registration in interpreter.py

```
grep -n 'env\.set' src/genia/interpreter.py | grep '"_filter"'
```

**Result: no output.** Confirmed absent.

---

### A3 — No `map_fn` / `filter_fn` dead helper bodies in interpreter.py

```
grep -n 'map_fn\|filter_fn' src/genia/interpreter.py
```

**Result: no output.** Confirmed absent.

---

### A4 — `list.genia` does not call `_map` or `_filter`

```
grep -n '\b_map\b\|\b_filter\b' src/genia/std/prelude/list.genia
```

**Result: no output.** `map` and `filter` are implemented as pure Genia tail-recursive functions using `map_acc` / `filter_acc` / `apply_raw`:

```genia
map(f, xs) = map_acc(f, xs, [])
map_acc(f, xs, acc) =
  (f, [], acc) -> acc |
  (f, [x, ..rest], acc) -> map_acc(f, rest, [..acc, apply_raw(f, [x])])

filter(predicate, xs) = filter_acc(predicate, xs, [])
filter_acc(predicate, xs, acc) =
  (predicate, [], acc) -> acc |
  (predicate, [x, ..rest], acc) ? apply_raw(predicate, [x]) == true -> filter_acc(predicate, rest, [..acc, x]) |
  (predicate, [_, ..rest], acc) -> filter_acc(predicate, rest, acc)
```

No Python delegation. No `_map` or `_filter` call site.

---

### A5 — No active `_map` / `_filter` references in any source, prelude, or spec file

```
grep -rn '\b_map\b\|\b_filter\b' . --include="*.py" --include="*.genia" --include="*.yaml" --include="*.yml"
  (excluding legitimate internal names: _map_new, _map_get, _map_put, _map_has,
   _map_remove, _map_count, _map_items, _map_some, and similar)
```

**Result:** Remaining hits are in:

- `tests/unit/test_dead_code_removal_182.py` — contract-guard test asserting `_map`/`_filter` are NOT registered (correct use)
- `tests/unit/test_list_hofs_190.py:3` — module docstring describing the historical pre-#190 state ("Extracts reduce, map, and filter from Python host-backed `_reduce/_map/_filter`"). This is a snapshot description, not a live call.
- `tests/unit/test_list_hofs_190.py:235` — inline comment ("Both old Python `_filter` (truthy(1)==True) and new prelude..."). Historical context in a comment.
- `tests/unit/test_function_docstrings.py:107` — `assert "\n    _map" not in out`. This asserts `_map` is absent from `help()` output. Correct guard.

None of these are active call sites. All are guards or historical notes confirming the cleanup is in place.

---

### A6 — `tests/unit/test_dead_code_removal_182.py` passes

```
pytest tests/unit/test_dead_code_removal_182.py -v
```

**Result: 17/17 PASSED**

| Test | Result |
|---|---|
| `TestDeadCodeRemoved::test_map_internal_not_registered` | PASS |
| `TestDeadCodeRemoved::test_filter_internal_not_registered` | PASS |
| `TestMapRegression::test_map_basic` | PASS |
| `TestMapRegression::test_map_empty` | PASS |
| `TestMapRegression::test_map_preserves_order` | PASS |
| `TestMapRegression::test_map_none_elements_delivered` | PASS |
| `TestMapRegression::test_map_named_function` | PASS |
| `TestFilterRegression::test_filter_basic` | PASS |
| `TestFilterRegression::test_filter_empty` | PASS |
| `TestFilterRegression::test_filter_all_kept` | PASS |
| `TestFilterRegression::test_filter_none_kept` | PASS |
| `TestFilterRegression::test_filter_none_elements_delivered` | PASS |
| `TestFilterRegression::test_filter_named_function` | PASS |
| `TestReduceRegression::test_reduce_sum` | PASS |
| `TestReduceRegression::test_reduce_empty` | PASS |
| `TestReduceRegression::test_reduce_non_list_error` | PASS |
| `TestReduceRegression::test_reduce_none_elements_delivered` | PASS |

The two key dead-code guards (`test_map_internal_not_registered`, `test_filter_internal_not_registered`) confirm that calling `_map(...)` or `_filter(...)` by name now raises an exception — i.e., they are not registered in the environment.

---

### A7 — Additional regression suites pass

```
pytest tests/unit/test_list_hofs_190.py -v   → 48/48 PASSED
pytest tests/unit/test_function_docstrings.py -k "_map" -v  → 1/1 PASSED
```

The `test_function_docstrings` test explicitly asserts `"\n    _map" not in out`, confirming `_map` does not appear in the autoloaded public `help()` surface.

---

### A8 — Docs do not falsely claim `_map`/`_filter` are active public helpers

Checked: `GENIA_STATE.md`, `GENIA_RULES.md`, `README.md`, `GENIA_REPL_README.md`, `docs/host-interop/capabilities.md`.

**Result: no output** after filtering out legitimate compound names (`flat_map_some`, `map_some`, `_map_new`, `request_map`, etc.).

None of the top-level truth-hierarchy docs mention `_map` or `_filter` as named primitives or active capabilities.

Architecture docs under `docs/architecture/` (`issue-182-*`, `issue-188-*`, `issue-190-*`) reference `_map`/`_filter` only as historical records of what was removed and why. These are accurate snapshots, not overclaims.

The one minor inaccuracy noted in the pre-flight — `issue-190-list-hofs-audit.md` line 201 saying "tracked as part of #181" when the work was done under #182 — remains a stale issue number in a historical doc. It does not constitute a truth-hierarchy violation and does not require correction.

---

## Blocking issues

**None.**

---

## Verdict

**PASS**

All six acceptance criteria from the issue are satisfied:

| Criterion | Status |
|---|---|
| No dead `env.set("_map", ...)` registration | PASS — absent |
| No dead `env.set("_filter", ...)` registration | PASS — absent |
| No dead `map_fn` / `filter_fn` bodies | PASS — absent |
| Prelude `map`/`filter` behavior unchanged | PASS — `apply_raw`-based Genia implementation confirmed |
| `test_dead_code_removal_182.py` passes | PASS — 17/17 |
| Docs describing `_map`/`_filter` as active helpers | PASS — none found |

---

## Recommendation

**Close #195. Proceed to #183 (`pairs(xs, ys)`).**

The `_map`/`_filter` host layer is clean. The pre-flight claim is proven by independent verification. No implementation, contract, design, or docs phases are needed for #195 — it is a verification-only issue and the verification passes.
