# Design: Extract list reduce/map/filter into prelude using apply_raw

Issue: #190
Phase: design
Branch: issue-190-prelude-list-hofs-design
Date: 2026-04-28

Preflight: `docs/architecture/issue-190-list-hofs-preflight.md`
Spec: `docs/architecture/issue-190-list-hofs-spec.md`

---

## 1. Purpose

Translate the spec for extracting `reduce`, `map`, and `filter` into pure Genia prelude into a concrete implementation structure. No code is written here.

---

## 2. Scope Lock

Follows the spec exactly.

### Included

- `src/genia/std/prelude/list.genia`: replace three one-line delegations with recursive prelude implementations
- New private accumulator helpers `map_acc` and `filter_acc` in `list.genia`
- Multi-arm case body for `reduce` that includes an explicit non-list catch-all arm delegating to `_reduce` for the error message

### Excluded

- `src/genia/interpreter.py`: **no changes** — `_reduce`, `_map`, `_filter` registrations remain untouched; removal is deferred
- Flow `map` / `filter` implementation in the evaluator: unchanged
- Parser, Core IR, or any new syntax
- `count`, `any?`, `find_opt`, or any other list helper
- `map_items`, `pairs`, `map_keys`, `map_values`
- `GENIA_STATE.md` or any other doc (docs phase)

---

## 3. Architecture Overview

### Where it fits

```
Genia source: reduce(f, acc, [1, 2, 3])
    ↓  parse + lower
IrCall(IrVar("reduce"), [f_node, acc_node, xs_node])
    ↓  autoload triggers load of std/prelude/list.genia
prelude reduce/3 (GeniaFunctionGroup, case body)
    ↓  pattern match on (f, acc, xs) tuple
    arm 1: xs == []       →  return acc
    arm 2: xs == [x|rest] →  apply_raw(f, [acc, x]) → recurse
    arm 3: xs = non-list  →  delegate to _reduce(f, acc, xs) → Python TypeError
```

```
Genia source: map(f, [1, 2, 3])
    ↓  autoload triggers load of std/prelude/list.genia
prelude map/2 (GeniaFunctionGroup, single-arm body)
    →  map_acc(f, [1,2,3], [])
       ↓  prelude map_acc/3 (GeniaFunctionGroup, case body)
       arm 1: xs == []       →  return acc
       arm 2: xs == [x|rest] →  map_acc(f, rest, [..acc, apply_raw(f, [x])])
```

```
Genia source: filter(pred, [1, 2, 3])
    ↓  autoload triggers load of std/prelude/list.genia
prelude filter/2 (GeniaFunctionGroup, single-arm body)
    →  filter_acc(pred, [1,2,3], [])
       ↓  prelude filter_acc/3 (GeniaFunctionGroup, case body)
       arm 1: xs == []                               →  return acc
       arm 2: xs == [x|rest], pred(x) == true  →  filter_acc(pred, rest, [..acc, x])
       arm 3: xs == [_|rest], pred(x) != true  →  filter_acc(pred, rest, acc)
```

### Flow dispatch — unchanged

When `map(f, flow)` or `filter(pred, flow)` is called in a pipeline and the second argument is a `GeniaFlow`, the evaluator intercepts at `invoke_callable` (line ~4652) before any prelude code runs. The prelude `map/2` and `filter/2` are never invoked for Flow arguments. **No change to this path.**

### Components involved

| Component | Role | Change |
|---|---|---|
| `src/genia/std/prelude/list.genia` | Hosts `reduce`, `map`, `filter` definitions | Replace three one-liners; add `map_acc`, `filter_acc` |
| `src/genia/interpreter.py` — `setup_env()` | Registers `_reduce`, `_map`, `_filter`, `apply_raw` | **No change** |
| Evaluator `invoke_callable` | Flow override for `map`/`filter` | **No change** |
| Autoload registry | Registers `reduce/3`, `map/2`, `filter/2` from `list.genia` | **No change** — same arities, same file |

---

## 4. File / Module Changes

### Modified files

**`src/genia/std/prelude/list.genia`** — three sections replaced, two helpers added:

1. **`reduce(f, acc, xs)` block** (currently line 113): replace `= _reduce(f, acc, xs)` with a three-arm case body.

2. **`map(f, xs)` block** (currently line 116): replace `= _map(f, xs)` with `= map_acc(f, xs, [])`. Insert new `map_acc/3` definition immediately after.

3. **`filter(predicate, xs)` block** (currently line 119): replace `= _filter(predicate, xs)` with `= filter_acc(predicate, xs, [])`. Insert new `filter_acc/3` definition immediately after.

### New files

None.

### Removed files

None. (`_reduce`, `_map`, `_filter` remain in `interpreter.py`; removal is deferred.)

---

## 5. Data Shapes

All inputs and outputs remain ordinary Genia runtime values. No new value types introduced.

| Parameter | Expected type | Notes |
|---|---|---|
| `f` / `predicate` | Genia callable | Named function or lambda; validated by `apply_raw` dispatch |
| `acc` | any Genia value | Initial accumulator; any runtime value |
| `xs` | Genia list | Empty `[]` or `[head, ..tail]`; non-list triggers error path |
| `acc` (map_acc / filter_acc) | Genia list | Accumulator built left-to-right via `[..acc, element]` |
| Return value | Genia list (map, filter) or any value (reduce) | Same as current; no change |

---

## 6. Function / Interface Design

### 6.1 `reduce(f, acc, xs)` — three-arm case body

**Public entry point.** Arity 3. Autoloaded from `list.genia`.

Arms (matched against the 3-tuple `(f, acc, xs)` in order):

| Arm | Pattern | Guard | Result |
|---|---|---|---|
| 1 | `(f, acc, [])` | none | `acc` — base case |
| 2 | `(f, acc, [x, ..rest])` | none | `reduce(f, apply_raw(f, [acc, x]), rest)` — tail-recursive |
| 3 | `(f, acc, xs)` | none | `_reduce(f, acc, xs)` — catch-all; xs is non-list; Python raises TypeError |

Arm 3 exists solely to preserve the exact error message `"reduce expected a list as third argument, received <type>"` from the current Python `_reduce`. It is only reached when `xs` does not match `[]` or `[head, ..tail]`, i.e., when `xs` is not a list.

**`@doc` annotation**: kept on this definition (unchanged text: `"Fold a list from left to right."`).

### 6.2 `map(f, xs)` — single-arm entry delegating to accumulator

**Public entry point.** Arity 2. Autoloaded from `list.genia`.

Body: `map_acc(f, xs, [])` — delegates to the accumulator helper with an empty initial accumulator.

**`@doc` annotation**: kept (unchanged text: `"Apply a function to every list element."`).

### 6.3 `map_acc(f, xs, acc)` — tail-recursive accumulator

**Private helper.** Arity 3. Not autoloaded directly; loaded as part of `list.genia` when `map` is autoloaded.

Arms (matched against the 3-tuple `(f, xs, acc)` in order):

| Arm | Pattern | Guard | Result |
|---|---|---|---|
| 1 | `(f, [], acc)` | none | `acc` — base case, return accumulated list |
| 2 | `(f, [x, ..rest], acc)` | none | `map_acc(f, rest, [..acc, apply_raw(f, [x])])` — tail-recursive |

`[..acc, apply_raw(f, [x])]` appends the mapped element to the right end of `acc`, preserving left-to-right order.

No `@doc` annotation. No entry in the autoload registry.

### 6.4 `filter(predicate, xs)` — single-arm entry delegating to accumulator

**Public entry point.** Arity 2. Autoloaded from `list.genia`.

Body: `filter_acc(predicate, xs, [])` — delegates to the accumulator helper.

**`@doc` annotation**: kept (unchanged text: `"Keep elements where \`predicate(x)\` is \`true\`."`).

### 6.5 `filter_acc(predicate, xs, acc)` — tail-recursive accumulator

**Private helper.** Arity 3. Not autoloaded directly.

Arms (matched against the 3-tuple `(predicate, xs, acc)` in order):

| Arm | Pattern | Guard | Result |
|---|---|---|---|
| 1 | `(predicate, [], acc)` | none | `acc` — base case |
| 2 | `(predicate, [x, ..rest], acc)` | `apply_raw(predicate, [x]) == true` | `filter_acc(predicate, rest, [..acc, x])` — include `x` |
| 3 | `(predicate, [_, ..rest], acc)` | none | `filter_acc(predicate, rest, acc)` — exclude element |

Guard in arm 2 uses `apply_raw(predicate, [x])` so `none(...)` elements are delivered to the predicate without short-circuit. The strict `== true` check is consistent with `any?` and `find_opt` in the same file.

No `@doc` annotation. No entry in the autoload registry.

---

## 7. Control Flow

### `reduce(f, acc, [x1, x2, x3])`

```
reduce(f, acc, [x1, x2, x3])
  → arm 2 matches: apply_raw(f, [acc, x1]) → acc1
  → reduce(f, acc1, [x2, x3])   [tail call]
    → arm 2 matches: apply_raw(f, [acc1, x2]) → acc2
    → reduce(f, acc2, [x3])     [tail call]
      → arm 2 matches: apply_raw(f, [acc2, x3]) → acc3
      → reduce(f, acc3, [])     [tail call]
        → arm 1 matches: return acc3
```

Each recursive call is in tail position. Genia TCO ensures constant stack space.

### `map(f, [x1, x2, x3])`

```
map(f, [x1, x2, x3])
  → map_acc(f, [x1, x2, x3], [])
    → arm 2: map_acc(f, [x2, x3], [apply_raw(f, [x1])])   [tail call]
      → arm 2: map_acc(f, [x3], [apply_raw(f, [x1]), apply_raw(f, [x2])])   [tail call]
        → arm 2: map_acc(f, [], [apply_raw(f, [x1]), apply_raw(f, [x2]), apply_raw(f, [x3])])   [tail call]
          → arm 1: return [r1, r2, r3]
```

Each `map_acc` call is in tail position. Order is preserved: `r_i = apply_raw(f, [x_i])`.

### `filter(pred, [x1, x2, x3])` where `pred(x1) = true`, `pred(x2) = false`, `pred(x3) = true`

```
filter(pred, [x1, x2, x3])
  → filter_acc(pred, [x1, x2, x3], [])
    → arm 2 guard: apply_raw(pred, [x1]) == true → include
    → filter_acc(pred, [x2, x3], [x1])           [tail call]
      → arm 2 guard: apply_raw(pred, [x2]) == true → false → fall to arm 3
      → arm 3: filter_acc(pred, [x3], [x1])       [tail call]
        → arm 2 guard: apply_raw(pred, [x3]) == true → include
        → filter_acc(pred, [], [x1, x3])           [tail call]
          → arm 1: return [x1, x3]
```

Each `filter_acc` call is in tail position.

### `reduce(f, acc, non-list)` — error path

```
reduce(f, acc, flow)
  → arm 1: (f, acc, []) → no match (flow is not [])
  → arm 2: (f, acc, [x, ..rest]) → no match (flow is not a list)
  → arm 3: (f, acc, xs) → matches (wildcard)
  → _reduce(f, acc, flow)
    → Python: isinstance(flow, list) → False
    → raise TypeError("reduce expected a list as third argument, received flow")
```

---

## 8. Error Handling Design

### `reduce` non-list input (spec invariant R4)

| Detected at | Mechanism | Message |
|---|---|---|
| `reduce` arm 3 catch-all → `_reduce` | Python `_reduce` type check | `"reduce expected a list as third argument, received <type>"` |

The catch-all arm `(f, acc, xs) -> _reduce(f, acc, xs)` is only reached when `xs` is not a list. `_reduce` immediately raises `TypeError` with the exact specified message. The `_runtime_type_name` helper inside `_reduce` produces the `<type>` string.

The `reduce-on-flow-type-error.yaml` shared spec is satisfied unchanged.

### `map` non-list input

No locked spec message. When `xs` is not a list, `map_acc(f, non-list, [])` fails to match any arm of `map_acc/3` and the evaluator raises a runtime pattern-match error. The exact message is not locked and may change.

### `filter` non-list input

Same as `map`. No locked spec message.

### Callback exceptions

`apply_raw` propagates exceptions from the callback body unchanged. The HOF accumulator does not catch or wrap them. This is consistent with the spec invariant HOF2.

---

## 9. Integration Points

### `apply_raw` — existing, unchanged

`apply_raw` is already registered in the env (`env.set("apply_raw", apply_raw_fn)` at line ~7779). The prelude implementations call it as an ordinary named function. No changes needed.

### `_reduce`, `_map`, `_filter` — existing, unchanged registrations

- `_reduce` remains registered and is called from the `reduce` catch-all arm for error handling.
- `_map` and `_filter` remain registered but are no longer called from prelude after this change. They become dormant. Removal is deferred.

### Autoload registry — unchanged

The autoload entries for `reduce/3`, `map/2`, `filter/2` all point to `std/prelude/list.genia`. These entries are not changed. When the runtime autoloads `reduce` for the first time, it loads the entire `list.genia` file, which now contains the new implementations plus `map_acc` and `filter_acc`.

`map_acc` and `filter_acc` are not in the autoload registry. They become available as side effects of loading `list.genia`, which is acceptable since they are private helpers.

### `count(xs) = reduce((acc, _) -> acc + 1, 0, xs)` — unchanged, still works

After extraction, `count` calls the prelude `reduce`. Since `reduce` is autoloaded from `list.genia`, and `count` is also in `list.genia` and calls `reduce`, the call works as before. No change needed.

### Flow `map` / `filter` — unchanged

The evaluator's Flow override at `invoke_callable` (line ~4652) checks `isinstance(fn, GeniaFunctionGroup)` by callee name. The new prelude `map(f, xs) = map_acc(f, xs, [])` still produces a `GeniaFunctionGroup` named `"map"` with arity 2. The override fires identically. Flow behavior is fully protected.

---

## 10. Test Design Input (for test phase)

The test phase uses the spec invariants as test targets. Key cases:

| Invariant | Test approach |
|---|---|
| R1: `reduce(f, acc, []) == acc` | `reduce((a,x)->a+x, 0, []) == 0` |
| R2: single-element reduce | `reduce((a,x)->a+x, 0, [5]) == 5` |
| R3: left-to-right order | `reduce((a,x)->a*10+x, 0, [1,2,3]) == 123` (order-sensitive) |
| R4: non-list TypeError | `reduce(f, 0, tick(3))` → exact stderr match against `reduce-on-flow-type-error.yaml` |
| HOF1 for reduce | `reduce` with `none(...)` in list; callback uses `unwrap_or` |
| M1: `map(f, []) == []` | `map((x)->x+1, []) == []` |
| M2–M4: map basic | `map((x)->x+1, [1,2,3]) == [2,3,4]` |
| HOF1 for map | `map` with `none(...)` elements; callback uses `unwrap_or` |
| F1: `filter(pred, []) == []` | filter with empty input |
| F2–F3: filter basic | filter even numbers from a list |
| F4: boolean predicate contract | predicate must return `true` to include |
| HOF1 for filter | `filter` with `none(...)` elements; predicate is `some?` |
| HOF2: exception propagation | callback that raises; assert exception propagates through HOF |
| HOF3: named function callback | use a named function (not lambda) as `f` |
| HOF5: large list (TCO) | deep recursion; assert no stack overflow |
| Regression | all existing `spec/eval/stdlib-map-*.yaml` and `spec/eval/stdlib-filter-*.yaml` pass |
| Regression | `tests/cases/option/reduce_none_propagation.genia` passes unchanged |
| Flow regression | all `spec/flow/flow-map-*.yaml` and `spec/flow/flow-filter-*.yaml` pass |

New tests for the `test` phase will be failing tests (written before implementation), per the AGENTS.md TDD requirement.

---

## 11. Doc Impact

Doc changes belong in the docs phase. Affected docs identified here:

| Doc | Section | Change needed |
|---|---|---|
| `GENIA_STATE.md` | §1594–1595: list stdlib description | Change "prelude wrappers over host-backed primitives" to "pure prelude implementations using `apply_raw`" |
| `GENIA_REPL_README.md` | autoloaded stdlib — list section | Same wording update |
| `README.md` | autoloaded prelude libraries description | Same wording update if phrasing appears |
| `docs/host-interop/capabilities.md` | `apply_raw` notes | Remove reference to `_reduce`/`_map`/`_filter` as current motivation (after builtins are eventually removed) |

`GENIA_RULES.md`: no changes required.

---

## 12. Constraints

**Follows existing patterns:**
- Multi-arm case body in function definition: same form as `last`, `find_opt`, `any?`, `nth_impl`, `range_acc` in `list.genia`
- Accumulator helper naming (`map_acc`, `filter_acc`): same convention as `length_acc`, `reverse_acc`, `range_acc`, `take_acc`
- `@doc` only on public entry points: same convention as existing helpers (no `@doc` on `length_acc`, `reverse_acc`, etc.)
- `apply_raw` used as ordinary named call: same as any other prelude function call

**Preserves minimalism:**
- No new Python primitives
- No new autoload registrations
- No new Core IR
- Two accumulator helpers (`map_acc`, `filter_acc`) follow established `*_acc` conventions

**Avoids unnecessary abstraction:**
- `map(f, xs) = map_acc(f, xs, [])` is a one-liner delegation; the same pattern as current `head(xs) = take(1, xs)`
- No intermediate data structures
- No shared helper between `map_acc` and `filter_acc` (they serve different purposes)

---

## 13. Complexity Check

[x] Minimal — three in-place replacements in one file; two private helper functions; no new primitives or registrations

**Explanation:** The accumulator pattern (`map_acc`, `filter_acc`) is exactly what `take_acc`, `reverse_acc`, and `range_acc` do in the same file. The `reduce` multi-arm form is exactly what `last`, `find_opt`, and `any?` do. `apply_raw` is already implemented and tested. The total delta is about 15 lines replacing 3 lines, following established conventions.

---

## 14. Final Check

- [x] Matches spec exactly:
  - `reduce` arm 3 preserves the exact TypeError message (spec invariant R4)
  - `filter` uses `== true` guard (spec invariant F4)
  - All HOFs use `apply_raw` for callback invocation (spec invariant HOF1)
  - All implementations are tail-recursive via TCO (spec invariant HOF5)
- [x] No new behavior introduced — only prelude restructuring of existing semantics
- [x] Structure is clear and implementable — directly maps to `list.genia` edits
- [x] Ready for implementation without ambiguity — exact arm patterns and file placement specified
