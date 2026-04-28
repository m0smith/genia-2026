# Spec: Extract list reduce/map/filter into prelude using apply_raw

Issue: #190
Phase: spec
Branch: issue-190-prelude-list-hofs-spec
Date: 2026-04-28

---

## 1. Change Name

Extract list `reduce`, `map`, and `filter` from Python host-backed implementations into pure Genia prelude using `apply_raw`.

---

## 2. Scope (from pre-flight)

### Included

- Observable behavior contract for `reduce(f, acc, xs)`
- Observable behavior contract for `map(f, xs)`
- Observable behavior contract for `filter(predicate, xs)`
- Callback invocation semantics using `apply_raw`
- Error behavior for non-list inputs
- Interaction with `none(...)` list elements
- Flow / list dispatch invariant
- New shared spec YAML cases for `reduce` (basic, empty, none-elements)

### Excluded

- Implementation code
- `_reduce`, `_map`, `_filter` Python builtin removal
- Flow `map` / `filter` behavior (evaluator-level; unaffected)
- `map_items`, `pairs`, `map_keys`, `map_values`
- `count`, `any?`, `find_opt` (downstream; unaffected by extraction)
- Parser changes
- Core IR changes
- Any other #181 extraction candidates

---

## 3. Behavior Definition

### 3.1 `reduce(f, acc, xs)`

Folds a list `xs` from left to right, applying `f(accumulator, element)` at each step.

**Signature:**
```
reduce(f, acc, xs) -> value
```

- `f` — any Genia callable; receives `(accumulator, element)` as positional arguments
- `acc` — the initial accumulator value
- `xs` — a list of runtime values

**Evaluation:**
1. If `xs` is empty, return `acc` unchanged. The callback is never invoked.
2. If `xs` is `[x, ..rest]`, compute `next_acc = apply_raw(f, [acc, x])`, then recurse: `reduce(f, next_acc, rest)`.
3. The result of the final step is the result of `reduce`.

**Callback invocation uses `apply_raw` semantics**: `none(...)` elements in `xs` are delivered to `f` without triggering the automatic `none(...)` short-circuit.

### 3.2 `map(f, xs)`

Applies `f` to every element of `xs` and returns a new list of results in the same order.

**Signature:**
```
map(f, xs) -> list
```

- `f` — any Genia callable; receives one element as its positional argument
- `xs` — a list of runtime values

**Evaluation:**
1. If `xs` is empty, return `[]`.
2. If `xs` is `[x, ..rest]`, the result is `[apply_raw(f, [x]), ..map(f, rest)]` — or equivalently via a tail-recursive accumulator in the same left-to-right order.
3. The result list preserves the order of `xs`: element `i` in the result corresponds to element `i` in `xs`.

**Callback invocation uses `apply_raw` semantics**: `none(...)` elements in `xs` are delivered to `f` without triggering the automatic `none(...)` short-circuit.

### 3.3 `filter(predicate, xs)`

Keeps only elements of `xs` for which `predicate(element)` returns boolean `true`.

**Signature:**
```
filter(predicate, xs) -> list
```

- `predicate` — any Genia callable; must return boolean `true` or `false`
- `xs` — a list of runtime values

**Evaluation:**
1. If `xs` is empty, return `[]`.
2. For each element `x` in left-to-right order: if `apply_raw(predicate, [x]) == true`, include `x` in the result; otherwise exclude it.
3. The result list preserves the relative order of included elements.

**Callback invocation uses `apply_raw` semantics**: `none(...)` elements in `xs` are delivered to `predicate` without triggering the automatic `none(...)` short-circuit.

**Predicate contract**: predicates must return boolean `true` or `false`. Non-boolean truthy values (e.g., non-zero numbers, non-empty strings) are treated as `false`. This is consistent with `any?` and `find_opt` in the same prelude.

---

## 4. Semantics

### 4.1 Callback invocation via `apply_raw`

All three HOFs invoke their callbacks using `apply_raw` semantics. This means:
- `none(...)` values in the element position are delivered to the callback as-is; the callback body executes.
- The callback's return value is used as-is (no re-wrapping).
- Exceptions raised inside the callback propagate through the HOF unchanged.

This is the critical semantic property that requires `apply_raw`. Without it, a naive recursive Genia implementation would short-circuit on `none(...)` list elements and return `none(...)` instead of calling the body.

### 4.2 Left-to-right evaluation order

All three HOFs process elements in left-to-right order:
- `reduce`: accumulator is updated left-to-right.
- `map`: output list elements correspond left-to-right to input list elements.
- `filter`: included elements appear in their original left-to-right order.

### 4.3 Flow / list dispatch

`map` and `filter` are overloaded for both Flow and list inputs at the evaluator level. When the second argument is a `GeniaFlow`, the evaluator intercepts the call before any prelude code runs and routes it to the Flow-specific implementation.

**This spec does not change Flow behavior.** The Flow path is fully independent of the list prelude implementation.

`reduce` is list-only. There is no Flow `reduce`. Calling `reduce` with a Flow third argument is an error.

### 4.4 Tail-call safety

The prelude implementations must be tail-recursive (or use tail-recursive accumulators) so they execute in constant stack space for arbitrarily large lists, as guaranteed by Genia's TCO contract.

---

## 5. Failure Behavior

### 5.1 `reduce` with non-list third argument

When `xs` is not a list (including when it is a Flow), `reduce` must raise:

```
TypeError: reduce expected a list as third argument, received <type>
```

where `<type>` is the runtime type name of the actual third argument (e.g., `"flow"`, `"string"`, `"int"`).

This error message is identical to the current Python host behavior. The `reduce-on-flow-type-error.yaml` shared spec is unchanged.

**Implementation implication:** the prelude `reduce` must include an explicit non-list error clause (not rely on pattern-match fallthrough) in order to preserve this exact message. The design phase must decide the mechanism.

### 5.2 `map` with non-list second argument

When `xs` is not a list, `map` raises a runtime error. The exact message is not currently locked by a shared spec and may differ from the current Python TypeError. The design phase may specify the exact message.

### 5.3 `filter` with non-list second argument

When `xs` is not a list, `filter` raises a runtime error. The exact message is not currently locked by a shared spec and may differ from the current Python TypeError. The design phase may specify the exact message.

### 5.4 Callback runtime errors

Exceptions raised inside any callback propagate through the HOF unchanged. The HOF does not catch or wrap them.

---

## 6. Invariants

| # | Invariant |
|---|---|
| R1 | `reduce(f, acc, []) == acc` for all `f`, `acc` |
| R2 | `reduce(f, acc, [x]) == apply_raw(f, [acc, x])` for all `f`, `acc`, `x` |
| R3 | `reduce` processes elements left to right |
| R4 | `reduce` with a non-list third argument raises `TypeError` with the exact message `"reduce expected a list as third argument, received <type>"` |
| M1 | `map(f, []) == []` for all `f` |
| M2 | `map(f, xs)` has the same length as `xs` |
| M3 | Element `i` of `map(f, xs)` equals `apply_raw(f, [xs[i]])` |
| M4 | `map` preserves left-to-right element order |
| F1 | `filter(pred, []) == []` for all `pred` |
| F2 | Every element of `filter(pred, xs)` appears in `xs` at an earlier or equal index than the next element |
| F3 | An element `x` is included in `filter(pred, xs)` iff `apply_raw(pred, [x]) == true` |
| F4 | `filter` predicates must return boolean `true` or `false` |
| HOF1 | `none(...)` list elements are delivered to the callback without short-circuit (requires `apply_raw` semantics) |
| HOF2 | Callback exceptions propagate through all three HOFs unchanged |
| HOF3 | Named functions and lambdas both work as callbacks |
| HOF4 | Flow `map` and `filter` behavior is unchanged |
| HOF5 | All three implementations must be tail-recursive (TCO-safe) |

---

## 7. Examples

### `reduce` sum
```genia
reduce((acc, x) -> acc + x, 0, [1, 2, 3, 4])
# → 10
```

### `reduce` empty list
```genia
reduce((acc, x) -> acc + x, 0, [])
# → 0
```

### `reduce` with none elements (callback receives none)
```genia
reduce((acc, o) -> acc + unwrap_or(0, o), 0, [some(1), none("x"), some(3)])
# → 4  (none("x") is delivered to callback; unwrap_or(0, none("x")) = 0)
```

### `map` basic
```genia
[1, 2, 3] |> map((x) -> x + 1)
# → [2, 3, 4]
```

### `map` empty
```genia
[] |> map((x) -> x + 1)
# → []
```

### `map` with none elements
```genia
[none("a"), some(2), none("b")] |> map((o) -> unwrap_or(0, o))
# → [0, 2, 0]  (none elements delivered to callback)
```

### `filter` basic
```genia
[1, 2, 3, 4, 5] |> filter((x) -> x % 2 == 0)
# → [2, 4]
```

### `filter` with none elements
```genia
[some(1), none("x"), some(3)] |> filter((o) -> some?(o))
# → [some(1), some(3)]
```

### `reduce` non-list error
```genia
reduce(acc, 0, tick(3))
# → TypeError: reduce expected a list as third argument, received flow
```

---

## 8. Non-Goals

This spec explicitly does NOT define:

- The internal prelude structure (accumulator helpers, naming) — that is the design phase
- Removal of Python `_reduce`, `_map`, `_filter` builtins — deferred to cleanup
- Any change to Flow `map` or `filter`
- Error messages for `map` or `filter` with non-list inputs
- `count`, `any?`, `find_opt`, or any other list helper
- Multi-host implementation details beyond the abstract contract

---

## 9. Implementation Boundary

This spec describes behavior independent of host:

- The contract is: `reduce`, `map`, `filter` produce the results defined in §3 and fail as defined in §5.
- The mechanism (`apply_raw`) is already a language-contract primitive (#188), not Python-specific.
- Any future host that provides `apply_raw` can implement these HOFs in its own prelude layer without Python.
- The Python host is the only current implementation; it will validate the contract.

---

## 10. Shared Spec Cases Added

### New files (spec/eval/)

| File | Invariant covered | Expected stdout |
|---|---|---|
| `stdlib-reduce-basic.yaml` | R1, R2, R3 | `10\n` |
| `stdlib-reduce-empty.yaml` | R1 (base case) | `0\n` |
| `stdlib-reduce-none-elements.yaml` | HOF1 (none delivered to callback) | `4\n` |

### Existing files unchanged

| File | Status |
|---|---|
| `stdlib-map-list-basic.yaml` | unchanged — covers M1–M4 |
| `stdlib-map-list-empty.yaml` | unchanged — covers M1 |
| `stdlib-filter-list-basic.yaml` | unchanged — covers F1–F3 |
| `stdlib-filter-list-no-match.yaml` | unchanged — covers F1 |
| `stdlib-filter-option-elements.yaml` | unchanged — covers HOF1 for filter |
| `stdlib-map-option-elements.yaml` | unchanged — covers HOF1 for map |
| `reduce-on-flow-type-error.yaml` | **unchanged** — R4 preserved exactly |

---

## 11. Doc Requirements

### `GENIA_STATE.md` wording update needed (docs phase)

Section 1594–1595 currently reads:
> `reduce`, `map`, and `filter` are prelude wrappers over host-backed primitives that skip none-propagation for callbacks

After extraction, this should read:
> `reduce`, `map`, and `filter` are pure prelude implementations using `apply_raw` for callback invocation; `none(...)` list elements are delivered to the callback without short-circuit

No other truth-hierarchy doc requires changes in the docs phase:
- **`GENIA_RULES.md`**: no change — no new invariants at the Rules level
- **`GENIA_REPL_README.md`**: minor update to the stdlib list description; surface names/arities unchanged
- **`README.md`**: minor update if "prelude wrappers over host-backed" phrasing appears
- **`docs/host-interop/capabilities.md`**: update the `apply_raw` notes (remove reference to `_reduce`/`_map`/`_filter` as motivation after builtins are removed)

---

## 12. Complexity Check

[x] Minimal  
[x] Necessary  
[ ] Overly complex

The scope is deliberately narrow: three related list HOFs, one new mechanism (`apply_raw`), no new syntax, no Core IR changes. The accumulator pattern is already established in `list.genia`. The only non-trivial decision is the error-message preservation for `reduce`, which requires an explicit type guard in the implementation.

---

## 13. Final Check

- [x] No implementation details included
- [x] No scope expansion beyond pre-flight
- [x] Consistent with `GENIA_STATE.md` (apply_raw section 9.6.4.1; list HOF section 1594–1595; TCO section 9.1)
- [x] Behavior is precise and testable
- [x] `reduce-on-flow-type-error.yaml` unchanged
- [x] Flow path explicitly confirmed unaffected
- [x] Three new shared spec YAML files pass against current implementation

---

## 14. Phase Sign-off

**GO for design phase.**

Remaining items for design phase:
- Decide exact prelude structure (multi-arm `reduce` + accumulator helpers for `map`/`filter`)
- Decide naming convention for `map_acc` / `filter_acc` helpers
- Design explicit non-list error guard for `reduce` to preserve `TypeError` message (invariant R4)
- Confirm `map` and `filter` non-list error behavior (not spec-locked; design phase decides)

Recommended next branch: `issue-190-prelude-list-hofs-design`

Recommended commit message:
```
design(list): plan reduce/map/filter prelude structure for issue #190
```
