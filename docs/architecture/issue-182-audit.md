# Audit: Remove dead _map/_filter Python registrations

Issue: #182 (subtask of #117)
Phase: audit
Branch: issue-182-extract-collections-options
Date: 2026-04-28

Pre-flight: `docs/architecture/issue-182-preflight.md`
Contract:   `docs/architecture/issue-182-contract.md`
Design:     `docs/architecture/issue-182-design.md`

---

## 0. BRANCH CHECK

- Work was NOT done on `main` ✓
- Branch: `issue-182-extract-collections-options` matches pre-flight ✓
- Commits on this branch:
  - `241cf9f` — preflight
  - `8e32528` — contract
  - `ad7a6e1` — design
  - `1659d02` — failing tests
  - `e3bf30b` — implementation
  - `7c29dc6` — docs (confirmed no-op)
- Scope matches branch intent ✓
- Files changed against `main`: exactly 5
  - `docs/architecture/issue-182-preflight.md` (new)
  - `docs/architecture/issue-182-contract.md` (new)
  - `docs/architecture/issue-182-design.md` (new)
  - `tests/unit/test_dead_code_removal_182.py` (new)
  - `src/genia/interpreter.py` (18 lines deleted)
- No unrelated changes included ✓

### Violations: None

---

## 3. AUDIT SUMMARY

Status: **PASS**

`map_fn`, `filter_fn`, `env.set("_map", ...)`, and `env.set("_filter", ...)` are removed from `interpreter.py`. Both names were unreachable dead code since issue #190 extracted `map` and `filter` to pure Genia prelude using `apply_raw`. All 65 targeted tests pass, all 147 shared specs pass, and all 1523 suite tests pass with zero regressions.

---

## 4. CONTRACT ↔ IMPLEMENTATION CHECK

| Contract requirement | Verified |
|---|---|
| `_map` not registered in Python environment | ✓ — `env.set("_map", map_fn)` deleted |
| `_filter` not registered in Python environment | ✓ — `env.set("_filter", filter_fn)` deleted |
| `map_fn` function definition removed | ✓ — 7 lines deleted |
| `filter_fn` function definition removed | ✓ — 7 lines deleted |
| `map(f, xs)` public behavior unchanged | ✓ — `map_acc` + `apply_raw` path intact |
| `filter(pred, xs)` public behavior unchanged | ✓ — `filter_acc` + `apply_raw` path intact |
| `reduce(f, acc, xs)` completely unaffected | ✓ — `reduce_fn` and `_reduce` registration untouched |
| `apply_raw` registration untouched | ✓ |
| none propagation for callbacks unchanged | ✓ — `apply_raw` path unchanged |
| Error message for non-list `reduce` input unchanged | ✓ — `_reduce` catch-all arm intact |
| No doc changes (nothing to update) | ✓ — 198 doc sync tests pass |

### Mismatches: None

---

## 5. DESIGN ↔ IMPLEMENTATION CHECK

| Design requirement | Verified |
|---|---|
| Delete `map_fn` definition (~lines 7062–7068) | ✓ |
| Delete `filter_fn` definition (~lines 7070–7076) | ✓ |
| Delete `env.set("_map", map_fn)` | ✓ |
| Delete `env.set("_filter", filter_fn)` | ✓ |
| Leave `reduce_fn` untouched | ✓ |
| Leave `env.set("_reduce", reduce_fn)` untouched | ✓ |
| Leave `env.set("apply_raw", apply_raw_fn)` untouched | ✓ |
| No changes to `list.genia` | ✓ |
| No changes to `option.genia` | ✓ |
| No new Python functions introduced | ✓ |
| One file changed in implementation | ✓ — only `src/genia/interpreter.py` |

### Mismatches: None

---

## 6. TEST VALIDITY

### Failing tests (before implementation):

| Test | Correctly failed? | Correctly passes now? |
|---|---|---|
| `TestDeadCodeRemoved::test_map_internal_not_registered` | ✓ DID NOT RAISE | ✓ PASS |
| `TestDeadCodeRemoved::test_filter_internal_not_registered` | ✓ DID NOT RAISE | ✓ PASS |

### Regression tests (15 tests, passed before and after):

| Group | Invariants covered | Result |
|---|---|---|
| `TestMapRegression` (5 tests) | A1, A4, A8, A9 | ✓ PASS |
| `TestFilterRegression` (6 tests) | A2, A5, A8, A9 | ✓ PASS |
| `TestReduceRegression` (4 tests) | A3, A6, A7, A8 | ✓ PASS |

### HOF regression suite (`test_list_hofs_190.py`, 48 tests): ✓ 48 PASS

### Full suite: 1523 passed, 1 skipped ✓

### Shared spec suite: 147/147 passed ✓

### Missing / weak tests: None

### False confidence risks: None

The two failing tests are correct and non-trivial: they prove `_map` and `_filter` were callable before deletion and raise an error after. The match pattern covers the actual Genia NameError wording. The regression suite covers all contract invariants A1–A10.

---

## 7. TRUTHFULNESS REVIEW

### GENIA_STATE.md

`_map` and `_filter` had no entries. Implementation is consistent with documentation. ✓

### docs/host-interop/capabilities.md

`apply_raw` entry (line 371) reads: "The prelude list HOFs `reduce`, `map`, and `filter` use `apply_raw` directly for callback invocation." This remains accurate — the prelude does use `apply_raw`; `_map` and `_filter` are gone. ✓

### docs/architecture/issue-190-list-hofs-audit.md (historical)

Line 34 references "The three one-line Python delegations (`_reduce`, `_map`, `_filter`) are replaced..." and line 201 recommends removing `_reduce`, `_map`, `_filter` as future follow-up. These are historical records accurately describing the state at the time of writing. They are not live documentation. Leaving them unchanged is correct. ✓

### docs/architecture/issue-188-callbacks-design.md (historical)

References `_map`/`_filter` as they existed at design time. Historical record. Correct to leave unchanged. ✓

### No doc violations found.

---

## 8. CROSS-FILE CONSISTENCY

| Document | Consistent with implementation |
|---|---|
| `GENIA_STATE.md` | ✓ — no `_map`/`_filter` entries; unchanged |
| `GENIA_RULES.md` | ✓ — no relevant entries; unchanged |
| `GENIA_REPL_README.md` | ✓ — no relevant entries; unchanged |
| `README.md` | ✓ — no relevant entries; unchanged |
| `docs/host-interop/capabilities.md` | ✓ — `apply_raw` note accurate |
| `src/genia/std/prelude/list.genia` | ✓ — unchanged; `map_acc`/`filter_acc` use `apply_raw` |
| `tests/unit/test_dead_code_removal_182.py` | ✓ — tests match contract |
| `tests/unit/test_list_hofs_190.py` | ✓ — all 48 pass unchanged |
| `spec/eval/stdlib-map-list-basic.yaml` | ✓ — passes |
| `spec/eval/stdlib-filter-list-basic.yaml` | ✓ — passes |
| `spec/eval/reduce-on-flow-type-error.yaml` | ✓ — exact error message preserved |

### Drift detected: None

Risk level: **Low**

---

## 9. PHILOSOPHY CHECK

- Preserves minimalism? **YES** — 18 lines deleted, nothing added. Net negative complexity.
- Avoids hidden behavior? **YES** — dead code that could mislead future developers is gone.
- Keeps semantics out of host? **YES** — the change moves in the right direction: less in the host, same behavior in the prelude.
- Aligns with pattern-matching-first? **YES** — no pattern-matching changes; prelude implementation is unchanged.

### Violations: None

---

## 10. COMPLEXITY AUDIT

**Minimal and necessary.**

The change is 18 deleted lines in one file. No new code, no new abstractions. Two function definitions and two `env.set` calls that were provably unreachable from all current prelude, tests, and spec cases.

### Anything removable: No — the deletion is already minimal.

---

## 11. ISSUE LIST

None.

---

## 12. RECOMMENDED FIXES

None required.

Potential future follow-up (not blocking, not part of #182):

1. **Replace `_reduce` catch-all with a Genia-native type-error arm** — requires a type-name primitive or error-raising primitive in Genia. Tracked as related to issue #181.
2. **Evaluate `none?`/`some?`/`or_else`/`unwrap_or`/`absence_reason`/`absence_context` extraction** using pattern matching — blocked Items C from the #182 contract. Suitable for a separate issue.

---

## 14. VALIDATION

Evidence:

- `python -m pytest tests/unit/test_dead_code_removal_182.py -v` → **17 passed** ✓
- `python -m pytest tests/unit/test_dead_code_removal_182.py tests/unit/test_list_hofs_190.py -v` → **65 passed** ✓
- `python -m pytest tests/ -q --ignore=tests/demo` → **1523 passed, 1 skipped** ✓
- `python -m tools.spec_runner` → **total=147 passed=147 failed=0 invalid=0** ✓
- `git diff main --name-only` → exactly 5 files, all within scope ✓
- `git diff main -- src/genia/interpreter.py` → 18 deletions only, zero insertions ✓
- Doc sync suite → **198 passed** ✓

---

## FINAL VERDICT

**Ready to merge: YES**

All contract invariants verified. No behavioral drift. No doc violations. No scope expansion. One implementation file changed (18 net lines deleted). Failing tests correctly proved the pre-change state and pass post-change. Full suite clean.
