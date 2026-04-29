# === GENIA PRE-FLIGHT ===

CHANGE NAME: #182 Extract collection and option helpers to prelude

Issue: #182 (subtask of #117)
Phase: preflight
Branch: issue-182-extract-collections-options
Date: 2026-04-28

---

## 0. BRANCH

Branch required: YES

Branch type: [x] refactor

Branch slug: issue-182-extract-collections-options

Expected branch: issue-182-extract-collections-options

Base branch: main

---

## BRANCHING REPORT

- Starting branch: `main`
- Working branch: `issue-182-extract-collections-options`
- Branch was newly created

---

## 1. SCOPE LOCK

### Change includes:

- Evaluate #182 against current main.
- Confirm whether reduce, map, and filter can be moved safely into Genia prelude.
- Identify parity tests needed if they are not already present.
- Determine whether the correct outcome is extraction, no-op/documented blocker, or a smaller follow-up issue.
- Assess remaining dead-code Python registrations (`_map`, `_filter`) and the `_reduce` catch-all.
- Evaluate whether "option helpers" have any remaining Python-backed equivalents outside of prelude.

### Change does NOT include:

- No Flow refactor.
- No map_items, map_keys, map_values, pairs, or keep_some changes.
- No new Option semantics.
- No tuple/public-shape changes.
- No error-message redesign.
- No semantic cleanup.
- No implementation in this phase.

---

## KEY FINDING: #190 COMPLETED THE CORE EXTRACTION

Before proceeding further, the pre-flight must record this critical discovery:

**Issue #190 ("Extract list reduce/map/filter into prelude using apply_raw") was completed on 2026-04-28 and merged to main with a passing audit.**

Evidence from current main:

- `list.genia` lines 113–131: `reduce`, `map`, and `filter` are now pure Genia prelude implementations using `apply_raw` for callback invocation.
- The `apply_raw` primitive was added to the language contract (GENIA_RULES.md §9.6.4.1) specifically to allow higher-order prelude functions to pass `none(...)` list elements to callbacks without triggering automatic none-propagation short-circuit.
- The audit for #190 PASSED: all 48 unit tests, all 147 shared specs, and all 1632 suite tests pass.
- `tests/cases/option/reduce_none_propagation.genia` regression test continues to pass.

This means **the primary blocker that was described in #182 ("Python callback invocation uses skip_none_propagation=True which Genia-native prelude calls cannot currently reproduce without behavior drift") has been resolved by the addition of `apply_raw`.**

---

## 2. SOURCE OF TRUTH

Authoritative files:

- GENIA_STATE.md (final authority)
- GENIA_RULES.md
- GENIA_REPL_README.md
- README.md
- AGENTS.md

### Additional relevant:

- `src/genia/std/prelude/list.genia` — current reduce/map/filter implementation
- `src/genia/interpreter.py` lines 7051–7076 — Python-backed `_reduce`, `_map`, `_filter`
- `src/genia/interpreter.py` lines 7776–7779 — env registrations for `_reduce`, `_map`, `_filter`, `apply_raw`
- `docs/architecture/issue-190-list-hofs-audit.md` — audit confirming extraction complete
- `tests/cases/option/reduce_none_propagation.genia` — regression test
- `tests/test_list_hofs_190.py` — HOF parity tests added in #190

### Notes:

- GENIA_STATE.md describes reduce/map/filter as "pure prelude implementations using `apply_raw` for callback invocation" as of the #190 docs phase.
- Python is the only implemented host and reference host.
- Do not treat future host portability as permission to change current Python behavior.

---

## 3. CURRENT STATE ASSESSMENT

### reduce (current main)

```genia
reduce(f, acc, xs) =
  (f, acc, []) -> acc |
  (f, acc, [x, ..rest]) -> reduce(f, apply_raw(f, [acc, x]), rest) |
  (f, acc, xs) -> _reduce(f, acc, xs)
```

Status: **Extracted to Genia prelude using `apply_raw`.**

The third arm `(f, acc, xs) -> _reduce(f, acc, xs)` is a catch-all that delegates to the Python-backed `_reduce` for non-list inputs. This is intentional: it preserves the exact `TypeError` message `"reduce expected a list as third argument, received <type>"` that is asserted by the shared spec case `reduce-on-flow-type-error.yaml`.

Remaining Python dependency: `_reduce` is still registered and called as the error-path catch-all.

### map (current main)

```genia
map(f, xs) = map_acc(f, xs, [])
map_acc(f, xs, acc) =
  (f, [], acc) -> acc |
  (f, [x, ..rest], acc) -> map_acc(f, rest, [..acc, apply_raw(f, [x])])
```

Status: **Fully extracted to Genia prelude using `apply_raw`.**

`_map` remains registered in the Python environment (`env.set("_map", map_fn)`) but is **not called** from `list.genia`. It is dead code from the prelude perspective.

### filter (current main)

```genia
filter(predicate, xs) = filter_acc(predicate, xs, [])
filter_acc(predicate, xs, acc) =
  (predicate, [], acc) -> acc |
  (predicate, [x, ..rest], acc) ? apply_raw(predicate, [x]) == true -> filter_acc(predicate, rest, [..acc, x]) |
  (predicate, [_, ..rest], acc) -> filter_acc(predicate, rest, acc)
```

Status: **Fully extracted to Genia prelude using `apply_raw`.**

`_filter` remains registered in the Python environment but is **not called** from `list.genia`. Dead code from the prelude perspective.

### F4 semantic note (from #190 audit)

Filter uses `apply_raw(predicate, [x]) == true` as a strict boolean guard. In Python, `1 == True` is `True`, so integer `1` passes the guard. Non-integer non-boolean values (`"hello"`, `[1]`) correctly fail the guard. This is consistent with `any?` and `find_opt` behavior and is documented.

---

## 3a. REMAINING WORK AFTER #190

The following items remain as potential scope for #182:

### Item A: Remove dead `_map` and `_filter` Python registrations

`_map` and `_filter` are registered in the environment but never called from prelude. They are true dead code from the user/prelude perspective. Removing them would clean up the interpreter without changing any public behavior.

**Risk:** Low. No prelude code calls these. The only risk is if an undocumented user code path calls `_map` or `_filter` directly by name — which is not a supported or documented surface.

**Blocker:** None. Safe to remove.

### Item B: Replace `_reduce` catch-all with a Genia-native type guard

Currently `reduce`'s third arm calls `_reduce` purely to generate the same error message. A Genia-native guard could produce the same error without the Python dependency:

```genia
(f, acc, xs) -> _reduce(f, acc, xs)
```

Could become a host-independent error arm if a type-error primitive or native runtime error is available in Genia. This is related to issue #181 (noted in the #190 audit as future follow-up).

**Risk:** Medium. The exact error message `"reduce expected a list as third argument, received <type>"` is asserted by a shared spec case. Any replacement must reproduce the exact message.

**Blocker:** Requires either a Genia-native error-raising primitive or the ability to format type-name strings without `_reduce`. This may require a separate prelude or host capability.

### Item C: Assess "option helpers" extraction scope

The issue title mentions "collection and option helpers". The option prelude (`src/genia/std/prelude/option.genia`) exists. The question is whether any option helpers are still Python-backed in a way that could be moved to prelude.

This requires inspecting `option.genia` and cross-referencing with Python-backed option builtins. This investigation is deferred to the contract/design phase.

---

## 4. FEATURE MATURITY

Stage: [x] Partial

How this must be described:

- Prelude extraction of reduce/map/filter is complete (via #190).
- Python-backed `_map` and `_filter` are dead code; `_reduce` is an error-path delegate.
- The "collection helpers" extraction is complete for the three primary HOFs.
- The "option helpers" extraction scope requires further assessment.

---

## 4a. PORTABILITY ANALYSIS

**Portability zone:** `prelude` (primary) + `Python reference host` (for dead-code removal)

**Core IR impact:** none — no new or modified `Ir*` node families.

**Capability categories affected:** eval (prelude behavior change visible in eval results)

**Shared spec impact:** none expected for dead-code removal. Item B (reduce catch-all cleanup) would require verifying `reduce-on-flow-type-error.yaml` continues to pass.

**Python reference host impact:**
- Item A: Remove `env.set("_map", ...)` and `env.set("_filter", ...)` from `src/genia/interpreter.py`.
- Item B: Remove `env.set("_reduce", ...)` from `src/genia/interpreter.py` if and only if the Genia-native error arm can reproduce the exact error message.
- Items A and B do not change user-visible behavior (dead code removal + error message preservation).

**Host adapter impact:** none.

**Future host impact:** Dead-code removal is Python-host-only cleanup. Future hosts are not affected.

---

## 5. CONTRACT vs IMPLEMENTATION

### Contract (portable semantics):

- Existing user-visible behavior of reduce/map/filter must remain identical.
- Existing none propagation behavior must remain identical.
- Existing error behavior must remain identical (exact TypeError message for non-list input).
- Existing lambda and named-function callback behavior must remain identical.

### Implementation today:

- reduce/map/filter are pure Genia prelude implementations using `apply_raw`.
- `_reduce` is called only for non-list inputs (error path).
- `_map` and `_filter` are registered but never called.
- `apply_raw` is the language contract primitive for raw callback invocation without none-propagation short-circuit.

### Not implemented:

- A Genia-native error-raising mechanism that can replicate the `_reduce` catch-all error message without the Python delegate.
- Assessment of option helper extraction scope (to be done in design phase).

---

## 6. TEST STRATEGY

### Core invariants (already verified by #190):

- Empty list behavior unchanged.
- Order of callback application unchanged.
- reduce accumulator behavior unchanged (left-to-right).
- filter predicate behavior unchanged (strict `== true` boolean guard).
- none values passed to callbacks are delivered without short-circuit.
- Non-list input errors remain compatible (exact TypeError message preserved by `_reduce` catch-all).

### Expected behaviors for #182 remaining scope:

- Removing `_map` / `_filter`: no test change needed (they are dead code; existing tests remain green).
- Replacing `_reduce` catch-all: `reduce-on-flow-type-error.yaml` must continue to assert `"reduce expected a list as third argument, received flow"` exactly.

### Failure cases:

- Regression in `reduce-on-flow-type-error.yaml` error message if `_reduce` catch-all is removed without a Genia-native equivalent.
- Regression in `reduce_none_propagation.genia` if callback delivery changes.

### How this will be tested:

- Run existing test suite (`tests/test_list_hofs_190.py`, full pytest suite) to confirm no regression from dead-code removal.
- If Item B is in scope: write failing tests first before modifying the reduce catch-all.

---

## 7. COMPLEXITY CHECK

Is this:
[x] Revealing structure (confirming #190 resolved the core blocker; identifying what remains)

### Justification:

- The core extraction is already done.
- The remaining items are dead-code cleanup (Items A/B) and further scope assessment (Item C).
- No new behavior is added.

---

## 8. CROSS-FILE IMPACT

### Files that may change in later phases:

- `src/genia/interpreter.py`: remove `_map`, `_filter` registrations (Item A); optionally `_reduce` (Item B).
- `src/genia/std/prelude/list.genia`: replace `_reduce` catch-all if Item B is resolved.
- `GENIA_STATE.md`: update if any implementation status changes.
- `docs/host-interop/capabilities.md`: update `_reduce`/`_map`/`_filter` entries if removed.
- `spec/eval/reduce-on-flow-type-error.yaml`: must pass unchanged throughout.

Risk of drift: [x] Low (for Items A and B) / Medium (for Item C, pending assessment)

---

## 9. PHILOSOPHY CHECK

Does this:

- preserve minimalism? YES — removing dead code and documenting reality is minimal.
- avoid hidden behavior? YES — the dead-code status of `_map`/`_filter` is now explicit.
- keep semantics out of host? YES — extraction is complete; host is only an error delegate and dead code.
- align with pattern-matching-first? YES — nothing changes the pattern model.

---

## 10. PROMPT PLAN

Will use full pipeline? YES (if scope warrants further phases beyond no-op)

Recommended next phases:

1. **Contract**: Define exact remaining work — Item A (remove `_map`/`_filter`), Item B (`_reduce` catch-all), Item C (option helper assessment). Determine which are in scope for this issue.
2. **Design**: For each in-scope item, specify exact changes. For Item B, determine whether a Genia-native type-error arm exists or must be introduced.
3. **Test**: Add failing tests if any behavioral change is possible (Item B). Item A requires no new tests.
4. **Implementation**: Remove dead code; optionally replace `_reduce` catch-all.
5. **Docs**: Update GENIA_STATE.md and capabilities.md to reflect removed registrations.
6. **Audit**: Verify no behavior drift and docs do not overclaim.

---

## FINAL GO / NO-GO

Ready to proceed?
YES — for contract/design investigation of remaining scope (Items A, B, C above).

**If contract reveals that Item B cannot preserve the exact error message and Item C has no extractable helpers, the correct outcome is:**
- Perform Item A (dead-code removal of `_map`/`_filter`) as a simple cleanup.
- Document that `_reduce` must remain as an error-path delegate until a Genia-native error primitive is available.
- Close #182 with those items done and Item C assessed.

**If #182 scope is determined to be fully subsumed by #190 with only trivial cleanup remaining**, it may be appropriate to close this issue with a brief documented summary rather than a full implementation phase.
