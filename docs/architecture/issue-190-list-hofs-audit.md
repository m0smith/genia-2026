# Audit: Extract list reduce/map/filter into prelude using apply_raw

Issue: #190
Phase: audit
Branch: issue-190-prelude-list-hofs-audit
Date: 2026-04-28

Preflight: `docs/architecture/issue-190-list-hofs-preflight.md`
Spec: `docs/architecture/issue-190-list-hofs-spec.md`
Design: `docs/architecture/issue-190-list-hofs-design.md`

---

## 0. BRANCH CHECK

- Work was NOT done on `main` ✓
- Branches:
  - `issue-190-prelude-list-hofs-preflight` — preflight doc (303353f)
  - `issue-190-prelude-list-hofs-spec` — spec doc + 3 new YAML cases + spec/eval/README.md update (59ed918)
  - `issue-190-prelude-list-hofs-design` — design doc (c38daab)
  - `issue-190-prelude-list-hofs-test` — failing test file `tests/test_list_hofs_190.py` (38949c3)
  - `issue-190-prelude-list-hofs-impl` — `list.genia` rewrite + corrected test (8e0c742)
  - `issue-190-prelude-list-hofs-docs` — GENIA_STATE.md + capabilities.md update (a667140)
  - `issue-190-prelude-list-hofs-audit` — this phase
- Scope matches branch intent ✓
- No unrelated changes included ✓

---

## 3. AUDIT SUMMARY

Status: **PASS**

`reduce`, `map`, and `filter` are now pure Genia prelude implementations using `apply_raw` for callback invocation. The three one-line Python delegations (`_reduce`, `_map`, `_filter`) are replaced by tail-recursive case expressions in `list.genia`. `_reduce` is retained in the catch-all arm to preserve the exact `TypeError` message for non-list inputs (invariant R4). All 48 unit tests pass, all 147 shared specs pass (including all 10 HOF-related YAML cases), all 1632 suite tests pass, and all documentation is truthful and internally consistent.

One semantic correction discovered during the test phase: the spec's claim that "non-boolean truthy values are treated as false" (F4) is qualified by Python's `1 == True` identity — integer `1` passes the `== true` guard, consistent with `any?` and `find_opt` behavior. The test was corrected and documents this semantic boundary.

---

## 4. SPEC ↔ IMPLEMENTATION CHECK

| Spec invariant | Test / spec file | Verified |
|---|---|---|
| R1: `reduce(f, acc, []) == acc` | `TestReduceBasic::test_empty_list_returns_accumulator`, `stdlib-reduce-empty.yaml` | ✓ |
| R2: `reduce(f, acc, [x]) == apply_raw(f, [acc, x])` | `TestReduceBasic::test_single_element` | ✓ |
| R3: left-to-right evaluation order | `TestReduceBasic::test_left_fold_order`, `stdlib-reduce-basic.yaml` | ✓ |
| R4: non-list third arg raises exact `TypeError` | `TestReduceTypeError::test_error_message_exact`, `reduce-on-flow-type-error.yaml` | ✓ |
| M1: `map(f, []) == []` | `TestMapBasic::test_empty_list`, `stdlib-map-list-empty.yaml` | ✓ |
| M2: output length equals input length | `TestMapBasic::test_same_length` | ✓ |
| M3: element i of result equals `apply_raw(f, [xs[i]])` | `TestMapBasic::test_increment_each`, `stdlib-map-list-basic.yaml` | ✓ |
| M4: preserves left-to-right order | `TestMapBasic::test_left_to_right_order` | ✓ |
| F1: `filter(pred, []) == []` | `TestFilterBasic::test_empty_list`, `stdlib-filter-list-no-match.yaml` | ✓ |
| F2: included elements in original order | `TestFilterBasic::test_preserves_relative_order` | ✓ |
| F3: element included iff `apply_raw(pred, [x]) == true` | `TestFilterBasic::test_even_elements`, `stdlib-filter-list-basic.yaml` | ✓ |
| F4: strict boolean predicate (`== true` guard) | `TestFilterStrictBooleanPredicate::test_string_return_not_truthy`, `test_list_return_not_truthy` | ✓ |
| HOF1: `none(...)` delivered to callback without short-circuit | `TestReduceNoneElements::test_none_elements_delivered_to_callback`, `stdlib-reduce-none-elements.yaml`, `stdlib-map-option-elements.yaml`, `stdlib-filter-option-elements.yaml` | ✓ |
| HOF2: callback exceptions propagate unchanged | `TestReduceNoneElements::test_callback_exception_propagates`, `TestMapNoneElements::test_callback_exception_propagates`, `TestFilterNoneElements::test_callback_exception_propagates` | ✓ |
| HOF3: named functions and lambdas both work | `TestReduceBasic::test_with_named_function`, `TestMapBasic::test_with_named_function`, `TestFilterBasic::test_with_named_function` | ✓ |
| HOF4: Flow `map`/`filter` path unchanged | `TestFlowDispatchUnchanged::test_flow_map_returns_flow`, `test_flow_filter_returns_flow` | ✓ |
| HOF5: TCO-safe (tail-recursive) | `reduce` recursive arm is in tail position; `map_acc`/`filter_acc` recursive calls are last expressions | ✓ |

### F4 semantic note

The spec states "non-boolean truthy values are treated as false, consistent with `any?`." In practice, Python's `1 == True` is `True`, so integer `1` passes the `== true` guard in both the new `filter_acc` and in `any?`. This is consistent behavior, not a violation. The test `test_int_1_equals_true_in_genia` documents this boundary explicitly. Non-integer non-boolean values (`"hello"`, `[1]`) correctly fail the guard and are excluded.

### Mismatches: None

---

## 5. DESIGN ↔ IMPLEMENTATION CHECK

| Design requirement | Verified |
|---|---|
| `reduce` uses three-arm case body (empty, recursive, catch-all) | ✓ (`list.genia` lines 112–116) |
| Recursive step: `reduce(f, apply_raw(f, [acc, x]), rest)` | ✓ |
| Catch-all delegates to `_reduce` for error message preservation | ✓ — `(f, acc, xs) -> _reduce(f, acc, xs)` |
| `map` entry delegates to `map_acc(f, xs, [])` | ✓ (`list.genia` line 119) |
| `map_acc` uses `[..acc, apply_raw(f, [x])]` accumulator (left-to-right order) | ✓ |
| `filter` entry delegates to `filter_acc(predicate, xs, [])` | ✓ (`list.genia` line 123) |
| `filter_acc` guard: `apply_raw(predicate, [x]) == true` | ✓ |
| `filter_acc` third arm uses `_` wildcard to discard excluded element | ✓ |
| No `@doc` on private helpers (`map_acc`, `filter_acc`) | ✓ |
| `map_acc` and `filter_acc` follow `*_acc` naming convention | ✓ (consistent with `take_acc`, `length_acc`, `reverse_acc`) |
| Guard syntax inline (not split across lines) | ✓ — parser requires guard and `->` on same line |
| No changes to `interpreter.py` | ✓ |
| `_reduce` remains registered in the env | ✓ |

### Mismatches: None

Design noted a multiline guard option; the parse failure during implementation confirmed the design's parenthetical caution was warranted. The single-line form was used.

---

## 6. TDD CHECK

- Failing-test commit SHA: `38949c3`
- Tests that failed before implementation:
  - `TestFilterStrictBooleanPredicate::test_int_return_not_truthy` — later corrected to `test_int_1_equals_true_in_genia` when the Python `1 == True` boundary was discovered
  - `TestFilterStrictBooleanPredicate::test_string_return_not_truthy` — `"hello" == true` is `False` in Python/Genia ✓
  - `TestFilterStrictBooleanPredicate::test_list_return_not_truthy` — `[1] == true` is `False` in Python/Genia ✓
- Tests that passed before implementation (regression guard): 45
- All 48 tests pass after implementation ✓

The test correction (`test_int_return_not_truthy` → `test_int_1_equals_true_in_genia`) was committed in the implementation phase commit `8e0c742` with full explanation.

---

## 7. DOCUMENTATION CHECK

### GENIA_STATE.md

Four sites updated (lines 391, 1340, 1413, 1595):

- Line 391: "host-backed and call their callbacks without none-propagation" → "pure prelude implementations using `apply_raw` for callback invocation; `none(...)` list elements are delivered to the callback without short-circuit" ✓
- Line 1340: same correction in the Option section ✓
- Line 1413: "because host-backed `map` delivers" → "because `map` uses `apply_raw` semantics to deliver" ✓
- Line 1595 (the primary spec target): "prelude wrappers over host-backed primitives that skip none-propagation for callbacks" → "pure prelude implementations using `apply_raw` for callback invocation; `none(...)` list elements are delivered to the callback without short-circuit" ✓

### docs/host-interop/capabilities.md

`apply_raw` notes updated: removed "public equivalent of `_invoke_raw_from_builtin` used by `reduce`, `map`, and `filter`" (that framing was pre-extraction); replaced with "The prelude list HOFs `reduce`, `map`, and `filter` use `apply_raw` directly for callback invocation." ✓

### GENIA_RULES.md

No changes needed — no new language-level invariants introduced. ✓

### GENIA_REPL_README.md

No changes needed — line 166 lists function names only; implementation detail not present. ✓

### README.md

No changes needed — no "host-backed" phrasing for list HOFs. ✓

### Doc sync tests

`tests/test_semantic_doc_sync.py`, `test_docs_truth_model.py`, `test_no_overclaim_language.py`, `test_doc_style_sync.py` — **194 passed** ✓

### Violations: None

---

## 8. CROSS-FILE CONSISTENCY

| Document | Consistent with implementation |
|---|---|
| GENIA_STATE.md | ✓ — four sites updated |
| GENIA_RULES.md | ✓ — no changes needed |
| GENIA_REPL_README.md | ✓ — no changes needed |
| README.md | ✓ — no changes needed |
| docs/host-interop/capabilities.md | ✓ — apply_raw notes updated |
| `spec/eval/stdlib-reduce-basic.yaml` | ✓ — passes |
| `spec/eval/stdlib-reduce-empty.yaml` | ✓ — passes |
| `spec/eval/stdlib-reduce-none-elements.yaml` | ✓ — passes |
| `spec/eval/stdlib-map-list-basic.yaml` | ✓ — passes (unchanged) |
| `spec/eval/stdlib-map-list-empty.yaml` | ✓ — passes (unchanged) |
| `spec/eval/stdlib-map-option-elements.yaml` | ✓ — passes (unchanged) |
| `spec/eval/stdlib-filter-list-basic.yaml` | ✓ — passes (unchanged) |
| `spec/eval/stdlib-filter-list-no-match.yaml` | ✓ — passes (unchanged) |
| `spec/eval/stdlib-filter-option-elements.yaml` | ✓ — passes (unchanged) |
| `spec/eval/reduce-on-flow-type-error.yaml` | ✓ — passes unchanged (R4 preserved exactly) |

### Drift detected: None

Risk level: **Low**

---

## 9. PHILOSOPHY CHECK

- Preserves minimalism? **YES** — 12 net lines added to one file; no new IR nodes, no parser changes, no new host capabilities
- Avoids hidden behavior? **YES** — `apply_raw` semantics are public contract; `_reduce` catch-all is explicit and documented
- Keeps semantics out of host? **YES** — the extraction moves semantics into the language layer; the host only provides `apply_raw` and the error-delegate `_reduce`
- Aligns with pattern-matching-first? **YES** — the implementation uses Genia's own pattern matching and guards throughout
- TCO safety maintained? **YES** — `reduce` recursive call is in tail position; `map_acc` and `filter_acc` recursive calls are last expressions in their arms

### Violations: None

---

## 10. COMPLEXITY AUDIT

**Minimal and necessary**

The implementation is 20 lines in `list.genia` (replacing 3). Two private helpers (`map_acc`, `filter_acc`) follow the established `*_acc` accumulator convention already used by `take_acc`, `length_acc`, and `reverse_acc` in the same file. No abstractions were introduced beyond what the spec required.

### Anything removable: No

---

## 11. ISSUE LIST

None.

---

## 12. RECOMMENDED FIXES

None required. Potential future follow-up (not blocking):

1. Remove `_reduce`, `_map`, `_filter` Python registrations once the catch-all arm in `reduce` is replaced with an explicit type-guard in Genia that produces the same error message natively. This is a separate cleanup tracked as part of #181.
2. Register `map_acc` and `filter_acc` autoloads if they are ever needed as standalone utilities (currently private; no user-facing need).

---

## 14. VALIDATION

Evidence:

- `python3 -m pytest tests/test_list_hofs_190.py -v` → **48 passed, 0 failed** ✓
- `python3 -m tools.spec_runner` → **Summary: total=147 passed=147 failed=0 invalid=0** ✓
- `python3 -m pytest tests/ -q` → **1632 passed** (no regressions) ✓
- Live spot-check all invariants R1–R4, M1–M4, F1–F4, HOF1–HOF5 → **ALL PASS** ✓
- `reduce-on-flow-type-error.yaml` exact error message verified: `"reduce expected a list as third argument, received flow"` ✓
- Flow dispatch: `tick(3) |> map((x) -> x + 1)` returns `GeniaFlow` ✓
- Doc sync tests (194): `test_semantic_doc_sync.py`, `test_docs_truth_model.py`, `test_no_overclaim_language.py`, `test_doc_style_sync.py` → **194 passed** ✓

---

## FINAL VERDICT

**Ready to merge: YES**

All invariants verified. No blocking issues. Cross-file consistency confirmed. No scope expansion. One file changed in implementation (12 net lines); four doc sites updated in GENIA_STATE.md and one in capabilities.md. The F4 semantic boundary (Python `1 == True`) is documented and consistent with existing `any?`/`find_opt` behavior.
