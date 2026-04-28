# === GENIA CONTRACT ===

CHANGE NAME: #182 Extract collection and option helpers to prelude

Issue: #182 (subtask of #117)
Phase: contract
Branch: issue-182-extract-collections-options
Date: 2026-04-28
Pre-flight: `docs/architecture/issue-182-preflight.md`

---

## 0. BRANCH DISCIPLINE

Current branch: `issue-182-extract-collections-options` ✓ (not `main`)
Matches pre-flight: ✓

---

## 1. PURPOSE

Define the exact outcome for issue #182 given current main state.

The primary extraction goal of #182 (reduce/map/filter to Genia prelude) was completed by issue #190. This contract defines what remains:

- **Item A**: Remove the dead `_map` and `_filter` Python environment registrations.
- **Item B**: `_reduce` remains registered; its catch-all arm in `reduce` must not be changed. Documented blocker.
- **Item C**: Option helper extraction is not possible in this phase. Documented blocker.

This contract is the source of truth for all later steps.

---

## 2. SCOPE (FROM PRE-FLIGHT)

### Included:

- Item A: Remove `env.set("_map", ...)` and `env.set("_filter", ...)` from `src/genia/interpreter.py`.
- Item A docs: Update `GENIA_STATE.md` and `docs/host-interop/capabilities.md` to remove any documentation of `_map` and `_filter` as registered capabilities.
- Item B: Document blocker — `_reduce` catch-all cannot be removed without a Genia-native type-name error primitive.
- Item C: Document blocker — option helpers cannot be extracted to pure Genia prelude in this phase.

### Excluded:

- No changes to `list.genia`.
- No changes to `option.genia`.
- No new Option semantics.
- No Flow refactor.
- No map_items, map_keys, map_values, pairs, or keep_some changes.
- No tuple/public-shape changes.
- No error-message redesign.
- No introduction of a Genia-native error-raising primitive (out of scope).
- No extraction of `none?`, `some?`, `or_else`, `unwrap_or`, etc. in this phase.

---

## 3. BEHAVIOR DEFINITION

### Item A: Remove `_map` and `_filter` registrations

**Current behavior:**
- `_map` and `_filter` are registered in the Python environment.
- Neither is called from any prelude file on current main.
- They are dead code from the user/prelude perspective.

**Contracted behavior after change:**
- `_map` and `_filter` are no longer registered in the Python environment.
- All user-accessible `map` and `filter` behavior is **unchanged**:
  - `map(f, xs)` continues to delegate to `map_acc` using `apply_raw` for callback invocation.
  - `filter(predicate, xs)` continues to delegate to `filter_acc` using `apply_raw` for callback invocation.
  - none-propagation behavior for callbacks is unchanged (delivered via `apply_raw`).
  - order of result elements is unchanged.
  - empty list behavior is unchanged.
- No test changes are required; existing tests must continue to pass.
- If any code directly calls `_map` or `_filter` by name, it will receive a `NameError`. This is intentional — `_map` and `_filter` are internal symbols, never part of the public API.

**State changes:**
- Two `env.set(...)` calls are removed from `interpreter.py`.
- Two Python function definitions (`map_fn`, `filter_fn`) become dead code and may be removed at the same time.

### Item B: `_reduce` remains — documented blocker

**Current behavior:**
```genia
reduce(f, acc, xs) =
  (f, acc, []) -> acc |
  (f, acc, [x, ..rest]) -> reduce(f, apply_raw(f, [acc, x]), rest) |
  (f, acc, xs) -> _reduce(f, acc, xs)
```

The third arm catches all non-list inputs and delegates to the Python-backed `_reduce`, which raises:
```
TypeError: reduce expected a list as third argument, received <type-name>
```

This exact message is asserted by `spec/eval/reduce-on-flow-type-error.yaml`.

**Why `_reduce` cannot be removed in this phase:**

Genia has no current mechanism to:
1. Raise a `TypeError` with a formatted message from prelude code, or
2. Obtain the runtime type name of a value as a string in Genia.

A Genia-native replacement would require one of:
- A `type_name(value)` Genia primitive returning the type name string, OR
- A general error-raising primitive (e.g., `raise_type_error(message)`), OR
- A shared spec change relaxing the exact error-message assertion.

None of these are in scope for #182.

**Contracted behavior:** No change to `reduce`. The catch-all arm remains. `_reduce` remains registered. The exact error message is preserved.

**This is a documented blocker.** Future resolution belongs to a separate issue (noted in #190 audit as related to #181).

### Item C: Option helper extraction — documented blocker

**Current state:** All helpers in `src/genia/std/prelude/option.genia` are thin wrappers over Python-backed `_`-prefixed primitives:

| Genia name | Python primitive | Extraction possible? |
|---|---|---|
| `some(value)` | `_some(value)` | NO — `GeniaOptionSome` is a Python runtime type |
| `none?(value)` | `_none?(value)` | Partially — see note |
| `some?(value)` | `_some?(value)` | Partially — see note |
| `get(key, target)` | `_get(key, target)` | NO — requires Python-level map type inspection |
| `get?(key, target)` | `_get?(key, target)` | NO — same |
| `map_some(f, opt)` | `_map_some(f, opt)` | Partially — see note |
| `flat_map_some(f, opt)` | `_flat_map_some(f, opt)` | Partially — see note |
| `then_get(key, target)` | `_then_get(key, target)` | NO — requires map type inspection |
| `then_first(target)` | `_then_first(target)` | NO — requires list/option type inspection |
| `then_nth(index, target)` | `_then_nth(index, target)` | NO — same |
| `then_find(needle, target)` | `_then_find(needle, target)` | NO — requires string/option inspection |
| `or_else(opt, fallback)` | `_or_else(opt, fallback)` | Partially — see note |
| `or_else_with(opt, thunk)` | `_or_else_with(opt, thunk)` | Partially — see note |
| `unwrap_or(default, opt)` | `_unwrap_or(default, opt)` | Partially — see note |
| `absence_reason(opt)` | `_absence_reason(opt)` | Partially — see note |
| `absence_context(opt)` | `_absence_context(opt)` | Partially — see note |
| `absence_meta(opt)` | `_absence_meta(opt)` | NO — requires constructing a map; complex |
| `is_some?(opt)` | `_is_some?(opt)` | Same as `some?` |
| `is_none?(opt)` | `_is_none?(opt)` | Same as `none?` |

**Note on "Partially":**
Helpers marked "Partially" could theoretically be implemented using Genia pattern matching on `some(v)`, `none`, `none(r)`, and `none(r, ctx)` forms. However:

1. This is out of scope for #182 as defined in the pre-flight.
2. Each such helper is in `_NONE_AWARE_PUBLIC_FUNCTIONS`, which means Python's none-propagation bypass is applied when calling them. A Genia-native implementation using none patterns in case arms would automatically become none-aware via the pattern-detection mechanism — but this requires its own design and test phase.
3. Extracting even one option helper without a separate design phase risks behavioral drift.

**Contracted behavior:** No option helpers are extracted in this phase. The thin-wrapper pattern remains for all helpers. No changes to `option.genia` or to any `_`-prefixed option Python registrations.

**This is a documented blocker.** Extraction of `none?`, `some?`, `or_else`, `unwrap_or`, and `absence_reason`/`absence_context` using pattern matching should be evaluated in a separate issue.

---

## 4. SEMANTICS

### `map(f, xs)` and `filter(predicate, xs)` — unchanged

All semantics are preserved identically. The `map_acc` and `filter_acc` helpers continue to use `apply_raw` for callback invocation. Removing `_map` and `_filter` from the environment does not affect these functions.

### `reduce(f, acc, xs)` — unchanged

The catch-all arm and `_reduce` registration are unchanged. The TypeError message for non-list third argument remains exactly:
```
reduce expected a list as third argument, received <type-name>
```

### none propagation

None propagation behavior for all collection and option helpers is unchanged. `apply_raw` continues to deliver `none(...)` list elements to callbacks without short-circuit.

---

## 5. FAILURE BEHAVIOR

### After Item A:

- `map(f, xs)` on a non-list `xs`: no Python-level TypeError from `_map`. Currently, `map_acc` would fall through all arms with a non-list; the catch-all arm catches only `(f, [], acc)` and `(f, [x, ..rest], acc)` patterns. A non-list `xs` would raise an unmatched dispatch error. **This is a pre-existing limitation** — the removal of `_map` does not introduce this failure; it existed when #190 was implemented. (See below for exact determination.)

Wait — this requires clarification. Let me reconsider.

`map(f, xs) = map_acc(f, xs, [])` — this calls `map_acc` with the non-list `xs`. `map_acc` has arms:
1. `(f, [], acc)` — matches only empty list
2. `(f, [x, ..rest], acc)` — matches non-empty list

A non-list `xs` would match neither arm and raise an unmatched-case error:
```
TypeError: No matching case for map_acc(f, <type-name>, [])
```

This behavior is **unchanged from current main** — `_map` was never called from `map` in the prelude (only `map_acc` is called). The only difference after Item A is that `_map` is no longer in the environment at all, which does not affect `map_acc`'s dispatch.

- `filter(predicate, xs)` on a non-list `xs`: same analysis — `filter_acc` raises an unmatched-case error. `_filter` was never called from `filter`; this behavior is unchanged.

- `reduce(f, acc, xs)` on a non-list `xs`: **unchanged** — `_reduce` catch-all arm still raises the exact TypeError.

---

## 6. INVARIANTS

These must hold before and after the change:

**A1**: `map(f, [1, 2, 3])` returns `[f(1), f(2), f(3)]` with elements in original order.
**A2**: `filter(pred, [1, 2, 3])` returns elements where `apply_raw(pred, [x]) == true`, in original order.
**A3**: `reduce(f, acc, [1, 2, 3])` accumulates left-to-right: `f(f(f(acc, 1), 2), 3)`.
**A4**: `map(f, [])` returns `[]`.
**A5**: `filter(pred, [])` returns `[]`.
**A6**: `reduce(f, acc, [])` returns `acc`.
**A7**: `reduce(f, acc, <non-list>)` raises `TypeError` with the exact message `"reduce expected a list as third argument, received <type-name>"`.
**A8**: `none(...)` elements in lists are delivered to callbacks via `apply_raw` without short-circuit.
**A9**: Named function callbacks and lambda callbacks both work for all three HOFs.
**A10**: Flow `map` and Flow `filter` dispatch is unchanged (they call into the Flow kernel, not `map_acc`/`filter_acc`).
**A11**: All invariants A1–A10 pass with all existing tests green and no regressions in the full test suite.

---

## 7. EXAMPLES

### Minimal (Item A — verifying no regression):

```genia
map((x) -> x + 1, [1, 2, 3])
```
Expected: `[2, 3, 4]`

```genia
filter((x) -> x > 1, [1, 2, 3])
```
Expected: `[2, 3]`

```genia
reduce((acc, x) -> acc + x, 0, [1, 2, 3])
```
Expected: `6`

```genia
map((o) -> unwrap_or(0, o), [none("a"), some(2), none("b")])
```
Expected: `[0, 2, 0]`

### Error case (Item B — unchanged):

```genia
reduce((acc, x) -> acc + x, 0, "not-a-list")
```
Expected error: `TypeError: reduce expected a list as third argument, received string`

### Regression guard (from `tests/cases/option/reduce_none_propagation.genia`):

```genia
map((o) -> unwrap_or(0, o), [none("a"), some(2), none("b")])
```
Expected: `[0, 2, 0]`

```genia
filter((o) -> some?(o), [some(1), none("x"), some(3)])
```
Expected: `[some(1), some(3)]`

```genia
reduce((acc, o) -> acc + unwrap_or(0, o), 0, [some(1), none("x"), some(3)])
```
Expected: `4`

---

## 8. NON-GOALS

- Does NOT change any user-visible behavior of `map`, `filter`, or `reduce`.
- Does NOT extract option helpers from Python.
- Does NOT introduce a Genia-native error-raising primitive.
- Does NOT resolve the `_reduce` catch-all (deferred to a future issue related to #181).
- Does NOT change `list.genia`.
- Does NOT change `option.genia`.
- Does NOT add new language features or syntax.
- Does NOT affect Flow `map` or Flow `filter` dispatch.

---

## 9. IMPLEMENTATION BOUNDARY

The change is confined to:
- `src/genia/interpreter.py`: two `env.set(...)` calls removed; two Python function definitions removed.
- Documentation updates to `GENIA_STATE.md` and `docs/host-interop/capabilities.md`.

This is a Python-host-only change. It does not affect the language contract, Core IR, shared spec YAML cases, or any prelude files.

Future hosts are not affected — `_map` and `_filter` were never part of the portable contract.

---

## 10. DOC REQUIREMENTS

### GENIA_STATE.md

- Remove any mention of `_map` and `_filter` as registered environment names (if present).
- If there is a capabilities table or list referencing `_map`/`_filter`, remove those entries.
- No other changes needed; `reduce`/`map`/`filter` documentation remains unchanged (already updated by #190).

### docs/host-interop/capabilities.md

- If `_map` or `_filter` appear as capability entries, remove them.
- Confirm `apply_raw` entry remains accurate (no change needed — already updated by #190).
- Add or update a note that `_reduce` remains as an error-path delegate (already documented implicitly by the catch-all arm description).

### Maturity label: `Partial` — unchanged.

### No new warnings needed.

---

## 11. COMPLEXITY CHECK

[x] Minimal
[x] Necessary

### Explain:

Item A is a two-line removal in the interpreter. No behavioral change. No tests to add. The cleanup removes code that cannot be reached from any current prelude or test. It is strictly simpler than the current state.

Items B and C are documented no-ops — they produce documentation, not code. Documentation of blockers is necessary to prevent future agents from attempting the same blocked extraction without context.

---

## 12. FINAL CHECK

- No implementation details included in this contract ✓
- No scope expansion ✓
- Consistent with GENIA_STATE.md (reduce/map/filter are pure prelude via apply_raw) ✓
- Behavior is precise and testable ✓
- Pre-flight scope lock respected ✓
- No code written ✓
- No design included ✓

---

## SUMMARY

| Item | Action | Blocker |
|---|---|---|
| A: Remove `_map`/`_filter` | Proceed — safe dead-code removal | None |
| B: Remove `_reduce` | Do not proceed | No Genia-native type-name error primitive |
| C: Extract option helpers | Do not proceed | Python runtime type inspection required for most; pattern-based extraction requires separate design issue |

**Correct outcome for #182:** Perform Item A (dead-code removal); document Items B and C as blockers; close scope.
