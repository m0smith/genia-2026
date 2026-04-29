# Pre-flight: Issue #195 — Resolve remaining _map/_filter host cleanup

**Issue:** #195  
**Branch:** `issue-cleanup-map-filter-host-leftovers`  
**Phase:** pre-flight  
**Date:** 2026-04-29  

---

## 1. Scope Lock

**In scope:**
- Verify whether `env.set("_map", ...)` and `env.set("_filter", ...)` host registrations remain in `src/genia/interpreter.py`.
- Verify whether `map_fn` / `filter_fn` dead-code bodies remain in `src/genia/interpreter.py`.
- Verify that no prelude `.genia` files still call `_map` or `_filter`.
- Identify any docs or tests that still describe `_map` / `_filter` as active host-backed helpers.

**Out of scope:**
- Public `map` / `filter` semantics — not touched.
- Flow optimization paths.
- `pairs(xs, ys)` implementation (belongs to #183).
- `_reduce` — not subject to this cleanup.
- Broad collection refactoring.

---

## 2. Source-of-Truth Files

Priority order per AGENTS.md:

1. `GENIA_STATE.md` — does not mention `_map` / `_filter` as named primitives; `map` and `filter` are described as stdlib list helpers
2. `GENIA_RULES.md` — no reference to `_map` / `_filter`
3. `src/genia/interpreter.py` — Python host implementation
4. `src/genia/std/prelude/list.genia` — Genia-level `map` / `filter` implementations
5. `tests/unit/test_dead_code_removal_182.py` — contract-guarding tests written for #182

---

## 3. Current Repo Evidence (grep/search results)

### 3.1 `env.set("_map", ...)` registrations

```
grep -rn 'env\.set.*"_map"' src/genia/interpreter.py
```
**Result: no output.** No `env.set("_map", ...)` registration exists.

### 3.2 `env.set("_filter", ...)` registrations

```
grep -rn 'env\.set.*"_filter"' src/genia/interpreter.py
```
**Result: no output.** No `env.set("_filter", ...)` registration exists.

### 3.3 `map_fn` / `filter_fn` dead code bodies

```
grep -rn 'map_fn\|filter_fn' src/genia/interpreter.py
```
**Result: no output.** No `map_fn` or `filter_fn` helper bodies remain.

### 3.4 Prelude `_map` / `_filter` calls

```
grep -n '_map\b\|_filter\b' src/genia/std/prelude/list.genia
```
**Result: no output.** `list.genia` uses `map_acc` / `filter_acc` via `apply_raw`, not `_map` / `_filter`.

### 3.5 Comprehensive source scan (all .py, .genia, .yaml)

```
grep -rn '\b_map\b\|\b_filter\b' . --include="*.py" --include="*.genia" --include="*.yaml"
  (excluding internal map builtins: _map_new, _map_get, _map_put, _map_has, _map_remove, _map_count, _map_items, _map_some)
```
**Result: no output.** No active `_map` or `_filter` references found in source, prelude, or spec files.

### 3.6 Test suite confirmation

```
pytest tests/unit/test_dead_code_removal_182.py -v
```
**Result: 17/17 PASSED**, including:
- `TestDeadCodeRemoved::test_map_internal_not_registered` — PASSED (confirms `_map` is not registered)
- `TestDeadCodeRemoved::test_filter_internal_not_registered` — PASSED (confirms `_filter` is not registered)
- All 15 regression tests for public `map`, `filter`, `reduce` — PASSED

### 3.7 `list.genia` implementation (confirmed)

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

Both are pure Genia tail-recursive implementations. No Python delegation.

### 3.8 Architecture docs (historical records, not overclaims)

The following `docs/architecture/` files reference `_map` / `_filter` in a historical context:
- `issue-182-design.md` — documents what was deleted (accurate historical record)
- `issue-182-preflight.md` — pre-flight that found and scoped the removal
- `issue-190-list-hofs-audit.md` — audit that documented the cleanup as a follow-on item
- `issue-190-list-hofs-preflight.md` — pre-flight that first identified `_map` / `_filter` as registered
- `issue-188-callbacks-design.md` — design doc that described the pre-#182 state

These are correct historical records. They do not claim `_map` / `_filter` are currently active. No updates needed.

---

## 4. Suspected Files Impacted

**None.** The cleanup is complete. There are no files requiring modification.

If this pre-flight had found active leftovers, the impacted files would have been:
- `src/genia/interpreter.py` (env.set / helper bodies)
- `src/genia/std/prelude/list.genia` (any call sites)
- `tests/unit/test_dead_code_removal_182.py` (contract guard)
- Relevant doc files

---

## 5. Contract vs Implementation Boundary

This issue is cleanup verification only — not a behavioral change.

- **Language contract** (GENIA_STATE.md): unaffected. `map` and `filter` are stdlib list helpers; `_map` / `_filter` were never part of the public contract.
- **Core IR**: unaffected. No IR nodes reference `_map` / `_filter`.
- **Host adapter** (`src/genia/interpreter.py`): cleanup already applied by #182.
- **Prelude** (`list.genia`): already uses `apply_raw`-based implementations since #190.

---

## 6. Test Strategy

No new tests are needed for #195.

**Existing coverage is sufficient and passing:**

| Test | Status | Covers |
|---|---|---|
| `TestDeadCodeRemoved::test_map_internal_not_registered` | PASS | `_map` is not registered |
| `TestDeadCodeRemoved::test_filter_internal_not_registered` | PASS | `_filter` is not registered |
| `TestMapRegression::*` (5 tests) | PASS | Public `map` unchanged |
| `TestFilterRegression::*` (6 tests) | PASS | Public `filter` unchanged |
| `TestReduceRegression::*` (4 tests) | PASS | `_reduce` unaffected |

If a follow-up issue wished to add an explicit "no _map/_filter in interpreter source" static assertion, that would be a test in the `audit` phase of a cleanup issue, not here.

---

## 7. Docs Impact

**None.** No doc changes are required.

- `GENIA_STATE.md`: correct — does not mention `_map` / `_filter`
- `docs/host-interop/capabilities.md`: correct — does not list `_map` / `_filter`
- `docs/architecture/issue-182-*`: accurate historical records of the #182 removal
- `docs/architecture/issue-190-list-hofs-audit.md` line 201 mentions a follow-on cleanup item tracked as "#181" — this was resolved by #182 and the audit doc is a snapshot. No update needed.

---

## 8. Risk of Drift

**Low / None.** The cleanup is already complete and guarded by passing tests.

The one residual risk is the `issue-190-list-hofs-audit.md` line 201 note:
> "Remove `_reduce`, `_map`, `_filter` Python registrations ... tracked as part of #181."

This note is stale (the work was done under #182, not #181), but it is inside a historical design audit doc. It does not drive any behavior and does not constitute a documentation overclaim. The issue number in the note is a minor inaccuracy in a historical record, not a truth-hierarchy violation.

---

## 9. Go / No-Go Recommendation

**NO-GO for implementation.** There is no work to do.

**The cleanup is already complete.** All of the following were verified:

- `env.set("_map", ...)` — absent from interpreter.py ✓
- `env.set("_filter", ...)` — absent from interpreter.py ✓
- `map_fn` / `filter_fn` bodies — absent from interpreter.py ✓
- Prelude `list.genia` — uses `apply_raw`-based Genia implementations, no `_map`/`_filter` calls ✓
- `test_dead_code_removal_182.py` — 17/17 PASS, including both dead-code guard tests ✓
- No active source, test, or spec files reference `_map` or `_filter` ✓

This issue was raised as a precautionary verification before #183 proceeds with `pairs(xs, ys)`. The verification confirms the field is clear.

---

## 10. Next Prompt Recommendation

**Recommended action: close #195 with a short verification commit and audit note.**

Since no code changes are needed, the pipeline reduces to:

1. **pre-flight** (this document) — commit as `preflight(list): _map/_filter cleanup verified complete issue #195`
2. **audit** — commit a one-paragraph audit note confirming the grep results and test pass, similar to the #182 audit. No contract/design/test/impl/docs phases needed.
3. **Close #195** with a link to the audit commit.

**Then proceed to #183** (`pairs(xs, ys)`) with confidence that the `_map`/`_filter` host layer is clean.
