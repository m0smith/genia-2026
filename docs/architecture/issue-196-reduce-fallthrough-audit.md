# Audit: Replace `_reduce` Catch-All with `_reduce_error`

**Issue:** #196
**Phase:** audit
**Branch:** issue-reduce-fallthrough-analysis
**Date:** 2026-04-29

---

## 1. Phase Checklist

| Phase | Commit | Status |
|-------|--------|--------|
| preflight | `4a0ac50` | ✓ |
| contract | `049df69` | ✓ |
| design | `81e6dd6` | ✓ |
| test | `d66d5d4` | ✓ |
| implementation | `440b4f0` | ✓ |
| docs | `8c5f203` | ✓ |

---

## 2. Contract Invariant Verification

| ID | Invariant | Verified |
|----|-----------|---------|
| I1 | `reduce(f, acc, flow)` raises `TypeError: "reduce expected a list as third argument, received flow"` | ✓ — `test_reduce_non_list_flow` PASS; `spec/eval/reduce-on-flow-type-error.yaml` PASS |
| I2 | `reduce(f, acc, "string")` raises `TypeError: "reduce expected a list as third argument, received string"` | ✓ — `test_reduce_non_list_string` PASS |
| I3 | `reduce(f, acc, [])` returns `acc` unchanged | ✓ — `test_reduce_empty_list_unaffected` PASS |
| I4 | `reduce(f, acc, [1,2,3])` accumulates left-to-right | ✓ — `test_reduce_list_unaffected` PASS; `test_reduce_sum` PASS |
| I5 | `none(...)` list elements are delivered to the callback | ✓ — `test_reduce_none_elements_delivered` PASS |
| I6 | `_reduce` is no longer registered in the env | ✓ — `test_reduce_internal_not_registered` PASS; no `env.set("_reduce", ...)` in source |
| I7 | No user-visible API changes | ✓ — `reduce` surface identical; all prelude tests pass |

---

## 3. Implementation Verification

### Change A — `src/genia/std/prelude/list.genia:116`

| Claim | Result |
|-------|--------|
| Arm 3 now calls `_reduce_error(xs)` with one argument | ✓ — confirmed at line 116 |
| Arms 1 and 2 unchanged | ✓ — lines 114–115 unmodified |

### Change B — `src/genia/interpreter.py`

| Claim | Result |
|-------|--------|
| `reduce_error_fn` defined at line 7051 (1 arg, raises TypeError with exact message) | ✓ |
| `reduce_fn` and its dead list-iteration body removed | ✓ — no `reduce_fn` in source |
| `env.set("_reduce_error", reduce_error_fn)` at line 7752 | ✓ |
| `env.set("_reduce", ...)` removed | ✓ — no occurrence in source |

### Change C — `docs/host-interop/capabilities.md`

| Claim | Result |
|-------|--------|
| `fn.reduce-error` entry inserted between `fn.apply-raw` and `zip.write` | ✓ — at line 373 |
| Portability marked `language contract` | ✓ |

---

## 4. Test Results

### New tests (`tests/unit/test_reduce_error_196.py`) — 11 passed

| Test | Pre-impl | Post-impl |
|------|----------|-----------|
| `TestReduceErrorPrimitive::test_reduce_error_registered` | FAIL (NameError) | PASS |
| `TestReduceErrorPrimitive::test_reduce_error_flow_message` | FAIL (NameError) | PASS |
| `TestReduceErrorPrimitive::test_reduce_error_string_message` | FAIL (NameError) | PASS |
| `TestReduceErrorPrimitive::test_reduce_error_int_message` | FAIL (NameError) | PASS |
| `TestReduceInternalRemoved::test_reduce_internal_not_registered` | FAIL (match miss) | PASS |
| `TestReduceNonListRegression::*` (6 tests) | PASS | PASS |

### Regression suite

| Suite | Result |
|-------|--------|
| `tests/unit/` (1331 tests) | PASS — 1331 passed, 1 skipped |
| `tests/` excluding unit (247 tests) | PASS — 247 passed |
| **Total** | **1578 passed, 1 skipped, 0 failed** |

### Spec assertions confirmed unchanged

| Spec file | Result |
|-----------|--------|
| `spec/eval/reduce-on-flow-type-error.yaml` | PASS — exact message preserved |
| `spec/flow/count-as-pipe-stage-type-error.yaml` | PASS — embedded message preserved |

---

## 5. Dead Code Removal Verification

The `reduce_fn` body contained:

```python
result = acc
for x in xs:
    result = _invoke_raw_from_builtin(f, [result, x])
return result
```

This iteration path was never reachable from arm-3 (arm-3 fires only for non-lists;
`reduce_fn` would have raised `TypeError` before entering the loop). It is now removed.
No behavior was lost.

`_invoke_raw_from_builtin` is still used by other paths; its removal was not in scope.

---

## 6. Documentation Accuracy Verification

| Document | Claim | Status |
|----------|-------|--------|
| `GENIA_STATE.md` | Does not name `_reduce` or `_reduce_error`; `reduce` described as a pure prelude function | ✓ accurate |
| `docs/host-interop/capabilities.md` | `fn.reduce-error` entry added; `fn.apply-raw` notes unchanged | ✓ accurate |
| `docs/host-interop/HOST_CAPABILITY_MATRIX.md` | No individual primitive rows; no change required | ✓ accurate |
| `tests/unit/test_dead_code_removal_182.py` | Stale `_reduce` comments updated to `_reduce_error` | ✓ accurate |
| `tests/unit/test_reduce_error_196.py` | Pre/post language in comments is historically correct | ✓ accurate |

Historical architecture docs (`issue-182-*.md`, `issue-190-*.md`, etc.) are immutable phase
records. They accurately describe the state at the time of writing and are not updated.

---

## 7. Scope Adherence

| Constraint | Verified |
|-----------|---------|
| Did not change reduce semantics for lists | ✓ |
| Did not modify pairs, map, or filter | ✓ |
| Did not introduce new APIs | ✓ — `_reduce_error` is an internal replacement, not a new public surface |
| Did not change any spec YAML files | ✓ |
| Did not add `type_name` or any general primitive | ✓ |

---

## 8. Verdict

**PASS.** All contracted invariants satisfied. All 1578 tests pass. The `_reduce` registration
is removed. The `_reduce_error` primitive is registered and produces the exact same error
message as the removed `_reduce`. All spec assertions pass without modification. Documentation
is accurate.

**Close #196. Branch `issue-reduce-fallthrough-analysis` is ready to merge.**
