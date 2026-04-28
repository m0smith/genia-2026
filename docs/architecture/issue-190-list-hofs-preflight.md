# === GENIA PRE-FLIGHT ===

CHANGE NAME: Extract list reduce/map/filter into prelude using apply_raw

Issue: #190
Branch: issue-190-prelude-list-hofs-preflight
Date: 2026-04-28

---

## 1. SCOPE LOCK

### Includes

- Inspect current prelude definitions of `reduce`, `map`, and `filter` in `list.genia`
- Inspect current Python implementations of `_reduce`, `_map`, and `_filter` in `interpreter.py`
- Inspect `apply_raw` behavior and docs from #188
- Inspect current shared specs and regression tests for list `reduce`, `map`, and `filter`
- Determine whether `reduce`, `map`, and `filter` can now be implemented entirely in `src/genia/std/prelude/list.genia`
- Recommend the smallest safe extraction plan

### Does NOT include

- Implementation
- Tests
- Docs sync beyond this preflight artifact
- Removing Python `_reduce`, `_map`, `_filter` builtins
- Changing Flow behavior
- Changing Option semantics
- Touching `map_items`, `pairs`, `map_keys`, or `map_values`
- Parser changes
- Core IR changes
- Broad stdlib extraction beyond these three functions

---

## 2. SOURCE OF TRUTH SUMMARY

### GENIA_STATE.md (final authority)

- Section 9.6.4.1: `apply_raw(f, args)` is a **language-contract host primitive** that calls `f` with the elements of list `args` as positional arguments without triggering the automatic `none(...)` short-circuit.
  - `f` may be any Genia callable (named function, lambda, builtin)
  - `args` must be a Genia list; a non-list second argument raises `TypeError`
  - `none` values in `args` are delivered to `f` unchanged — the body executes
  - exceptions raised inside `f` propagate unchanged
  - use case: implementing higher-order functions (`reduce`, `map`, `filter`) that must deliver `none(...)` list elements to their callback
- Section 19 (Flow): `map` and `filter` are overloaded for Flow and list inputs. The evaluator intercepts calls to named `map`/`filter` when the second argument is a `GeniaFlow`, routing them to the Flow implementation before any prelude code runs. Prelude-backed `map(f, xs)` / `filter(pred, xs)` are only invoked when `xs` is not a Flow.
- Section 1594–1595: `reduce`, `map`, and `filter` are documented as "prelude wrappers over host-backed primitives that skip none-propagation for callbacks".
- Section 9.1: Proper tail-call optimization is guaranteed for calls in tail position, including the final expression in a block and case arm results.
- GENIA_STATE.md is the final authority for all behavior. All other docs and implementation must align with it.

### AGENTS.md

- Change must follow: preflight → spec → design → test → implementation → docs → audit
- Each phase is a separate prompt and a separate commit
- A change should affect only ONE zone; this extraction affects the prelude (host adapter), not Language Contract or Core IR
- Pre-flight phase must NOT implement, test, or sync docs beyond this artifact
- AGENTS.md says "do not invent behavior" and "do not perform repo-wide renames"

### GENIA_RULES.md

- No specific rules governing HOF extraction; the general constraint is: "tests must reflect actual behavior" and "implementation must match STATE + RULES"
- Section 4 (full tuple match model): pattern matching always targets the full argument tuple — relevant when writing multi-arm `reduce(f, acc, []) / reduce(f, acc, [x, ..rest])` forms

### GENIA_REPL_README.md

- Lists `reduce`, `map`, `filter` under autoloaded stdlib functions keyed by `(name, arity)`
- Lists `apply_raw` as a builtin: "raw callback invocation: `apply_raw(f, args)` — language-contract host primitive; bypasses `none(...)` short-circuit; `args` must be a list"
- Flow transforms: `map`, `filter` are also listed under Flow transforms — the overloading is well-documented

### README.md

- Notes autoloaded prelude libraries exist; no specific claim about whether HOFs are Python-backed or prelude-native

### Issue #188 (complete)

- Introduced `apply_raw(f, args)` as a language-contract host primitive
- This removes the primary blocker that required Python-only behavior for `_reduce`, `_map`, `_filter`
- Shared specs for `apply_raw` now validate: basic ordinary-value call, `none(...)` argument body-executes, multi-arg `none(...)`, contrast with normal call, lambda identity with `none(...)`, empty-args case

### Issue #181 (inventory only — must not become implementation)

- Inventory of pure Python helpers for prelude extraction
- Classified `reduce`, `map`, and `filter` as the first safe focused extraction slice after #188 lands
- This issue is inventory/classification only; no implementation

### Issue #117 (parent epic)

- Goal: extract pure runtime helpers from Python into prelude
- `reduce`, `map`, and `filter` are blocked extraction candidates that #190 unlocks

### Issue #190 (this issue)

- Focused implementation target: reimplement `reduce`, `map`, and `filter` in `list.genia` using `apply_raw`
- Preserve exact existing semantics
- Scope is limited to these three list HOFs only

---

## 3. CURRENT BEHAVIOR INSPECTION

### 3.1 Current prelude definitions (`src/genia/std/prelude/list.genia`)

Lines 113–119:

```genia
@doc "Fold a list from left to right."
reduce(f, acc, xs) = _reduce(f, acc, xs)

@doc "Apply a function to every list element."
map(f, xs) = _map(f, xs)

@doc "Keep elements where `predicate(x)` is `true`."
filter(predicate, xs) = _filter(predicate, xs)
```

All three are one-line delegations. No recursive logic in prelude — all semantics live in the Python builtins.

Autoload registrations (`interpreter.py` lines 7816–7818):
```python
env.register_autoload("reduce", 3, "std/prelude/list.genia")
env.register_autoload("map", 2, "std/prelude/list.genia")
env.register_autoload("filter", 2, "std/prelude/list.genia")
```

### 3.2 Python implementations (`interpreter.py` lines 7051–7076)

```python
def reduce_fn(f, acc, xs):
    """Host-backed reduce that calls the callback via invoke_callable with
    skip_none_propagation, so that list elements which are none(...)
    are passed to the callback rather than short-circuiting it."""
    if not isinstance(xs, list):
        raise TypeError(
            f"reduce expected a list as third argument, received {_runtime_type_name(xs)}"
        )
    result = acc
    for x in xs:
        result = _invoke_raw_from_builtin(f, [result, x])
    return result

def map_fn(f, xs):
    """Host-backed map that calls the callback via invoke_callable with
    skip_none_propagation, so that list elements which are none(...)
    are passed to the callback rather than short-circuiting it."""
    if not isinstance(xs, list):
        raise TypeError(
            f"map expected a list as second argument, received {_runtime_type_name(xs)}"
        )
    return [_invoke_raw_from_builtin(f, [x]) for x in xs]

def filter_fn(predicate, xs):
    """Host-backed filter that calls the callback via invoke_callable with
    skip_none_propagation, so that list elements which are none(...)
    are passed to the callback rather than short-circuiting it."""
    if not isinstance(xs, list):
        raise TypeError(
            f"filter expected a list as second argument, received {_runtime_type_name(xs)}"
        )
    return [x for x in xs if truthy(_invoke_raw_from_builtin(predicate, [x]))]
```

Registered in env as `_reduce`, `_map`, `_filter` (underscore-prefixed, internal names) at lines 7776–7778.

`_invoke_raw_from_builtin` is a Python closure that calls `invoke_callable` with `skip_none_propagation=True`.

### 3.3 `apply_raw` implementation (`interpreter.py` lines 6908–6919)

```python
def apply_raw_fn(proc, args):
    if not isinstance(args, list):
        raise TypeError(
            f"apply_raw expected a list as second argument, received {_runtime_type_name(args)}"
        )
    return Evaluator(env, env.debug_hooks, env.debug_mode).invoke_callable(
        proc,
        args,
        tail_position=False,
        callee_node=None,
        skip_none_propagation=True,
    )
```

Registered at line 7779: `env.set("apply_raw", apply_raw_fn)` (not autoloaded — directly set in env).

`apply_raw` is mechanically identical to `_invoke_raw_from_builtin`. The difference is that `apply_raw` is accessible from Genia code, while `_invoke_raw_from_builtin` is Python-internal only.

### 3.4 Flow / list dispatch for `map` and `filter`

At `interpreter.py` line 4651–4689: when `invoke_callable` is called with a `GeniaFunctionGroup` named `"map"` or `"filter"` AND the second argument is a `GeniaFlow`, the evaluator intercepts the call and executes the Flow-specific implementation. This check happens before any prelude code runs.

```python
if isinstance(fn, GeniaFunctionGroup) and isinstance(callee_node, IrVar) \
        and len(args) == 2 and isinstance(args[1], GeniaFlow):
    if callee_node.name == "map":
        # Flow map: yields transformed items lazily
    if callee_node.name == "filter":
        # Flow filter: uses truthy() to test each item lazily
```

Additionally, at line 3833: `if isinstance(callee_node, IrVar) and callee_node.name in {"map", "filter", "take", "scan"}: return True` — these names are listed as explicitly none-aware, so `some(x)` inputs bypass stage-lifting for these calls.

A prelude reimplementation of `map(f, xs)` / `filter(pred, xs)` produces a `GeniaFunctionGroup` (as all prelude-defined named function groups do), so the existing Flow override at line 4652 would still apply. The Flow path is not affected by this extraction.

**`reduce` does not have a Flow path**: calling `reduce(f, acc, flow)` currently hits `_reduce`, which raises `TypeError("reduce expected a list as third argument, received flow")`.

### 3.5 Python `truthy()` semantics (`interpreter.py` line 5150)

```python
def truthy(value):
    if is_none(value): return False
    return bool(value)
```

`truthy()` returns `False` for `none(...)`, `false`, `0`, `0.0`, `""`, and `[]`; returns `True` for any other value. The Python `filter_fn` uses `truthy()` for predicate checks. This means a predicate returning a non-boolean truthy value (e.g., `(x) -> x` on a list of integers) would currently filter correctly in Python but would NOT match `== true` in a Genia prelude pattern guard.

### 3.6 Existing shared specs for list HOFs

**`spec/eval/`:**
- `stdlib-map-list-basic.yaml`: `[1,2,3] |> map((x)->x+1)` → `[2,3,4]`
- `stdlib-map-list-empty.yaml`: `[] |> map(...)` → `[]`
- `stdlib-filter-list-basic.yaml`: filter even numbers
- `stdlib-filter-list-no-match.yaml`: filter with empty result
- `stdlib-filter-option-elements.yaml`: `[some(1), none("x"), some(3)] |> filter(some?)` → `[some(1), some(3)]`
- `stdlib-map-option-elements.yaml`: `[none("a"), some(2), none("b")] |> map((o)->unwrap_or(0,o))` → `[0,2,0]`
- `reduce-on-flow-type-error.yaml`: `reduce(acc, 0, tick(3))` → `stderr: "Error: reduce expected a list as third argument, received flow"`

**`spec/flow/`:**
- `flow-map-basic.yaml`, `flow-filter-basic.yaml`, `flow-map-filter-chain.yaml`: Flow-specific overload; these must remain unaffected

**`spec/eval/apply-raw-*.yaml`:** six specs covering `apply_raw` contract.

No shared spec exists for basic `reduce` behavior (sum, product). That coverage lives in the non-shared `tests/cases/reduce_*.genia` files.

### 3.7 Non-shared regression test

`tests/cases/option/reduce_none_propagation.genia` tests:
- `reduce((acc, o) -> acc + unwrap_or(0, o), 0, [some(1), none("x"), some(3)])` → `4`
- `map((o) -> unwrap_or(0, o), [none("a"), some(2), none("b")])` → `[0, 2, 0]`
- `filter((o) -> some?(o), [some(1), none("x"), some(3)])` → `[some(1), some(3)]`

These are the critical cases requiring `apply_raw` semantics for correct behavior.

### 3.8 Downstream prelude dependency

`count(xs) = reduce((acc, _) -> acc + 1, 0, xs)` in `list.genia`. After extraction, `count` calls the new prelude `reduce`, which is transparent — no call-site changes needed.

---

## 4. PROBLEM STATEMENT

### What logic remains Python-host-backed

`_reduce`, `_map`, `_filter` are Python builtins registered directly into the env. Their critical property is using `_invoke_raw_from_builtin(..., skip_none_propagation=True)`, which delivers `none(...)` list elements to the callback rather than short-circuiting.

### Why it is now safe to move

#188 introduced `apply_raw(f, args)` as a language-contract host primitive that replicates `_invoke_raw_from_builtin` at the Genia level. The prelude can now write:

```genia
reduce(f, acc, [x, ..rest]) = reduce(f, apply_raw(f, [acc, x]), rest)
```

and callbacks will receive `none(...)` elements without short-circuit. The blocker is removed.

### What `apply_raw` solves

`apply_raw` is the Genia-visible equivalent of `_invoke_raw_from_builtin`. It was specifically introduced to unblock this exact extraction (documented in GENIA_STATE.md section 9.6.4.1 use-case note).

### Risks that remain

1. **Error message divergence**: The spec `reduce-on-flow-type-error.yaml` asserts exact stderr `"Error: reduce expected a list as third argument, received flow"`. A prelude `reduce` with pattern-matched arms `[]` and `[x, ..rest]` would not match a Flow argument; the evaluator would raise a pattern-match error with a different message. The spec would fail.

2. **Truthiness narrowing in `filter`**: Python `truthy()` accepts non-none, non-false values. A prelude `filter` using the pattern `apply_raw(predicate, [x]) == true` would only keep elements where the predicate returns boolean `true`, not any truthy value. This is a narrow behavior change for predicates that return non-boolean truthy values (no current test covers this case, but it is a semantic difference).

3. **No type-error guarantee for non-list inputs**: A prelude `reduce`/`map`/`filter` that only pattern-matches `[]` and `[head, ..rest]` will produce a pattern-match error for non-list inputs rather than the current Python `TypeError` with a specific message. This affects only the `reduce-on-flow-type-error.yaml` spec (and the implicit behavior for `map`/`filter` with non-list inputs, though those are not currently spec-tested).

4. **TCO requirement**: `reduce` with tail recursion is safe given Genia's TCO guarantee. `map` and `filter` need accumulator-based implementations to keep the recursive call in tail position.

### Classification

This is a **prelude extraction**. No new language syntax, no Core IR changes, no parser changes. The change affects only the prelude layer (host adapter tier), not Language Contract or Core IR tiers.

---

## 5. DESIGN OPTION INVENTORY

### Option A: Direct recursive prelude implementations using `apply_raw`

Replace the one-line delegation in `list.genia` with multi-arm recursive prelude functions:

```genia
reduce(f, acc, []) = acc
reduce(f, acc, [x, ..rest]) = reduce(f, apply_raw(f, [acc, x]), rest)

map_acc(f, [], acc) = acc
map_acc(f, [x, ..rest], acc) = map_acc(f, rest, [..acc, apply_raw(f, [x])])
map(f, xs) = map_acc(f, xs, [])

filter_acc(pred, [], acc) = acc
filter_acc(pred, [x, ..rest], acc) ? apply_raw(pred, [x]) == true
    -> filter_acc(pred, rest, [..acc, x])
filter_acc(pred, [x, ..rest], acc) -> filter_acc(pred, rest, acc)
filter(pred, xs) = filter_acc(pred, xs, [])
```

**Benefits:**
- Pure prelude code: no Python host coupling for list HOF logic
- `apply_raw` is already spec-tested and language-contract-stable
- TCO-safe via accumulator pattern (`map_acc`, `filter_acc`)
- `reduce` is already tail-recursive in its natural form
- Reduces host-specific semantic surface by 3 builtins
- `count` still works: calls prelude `reduce`, no changes needed

**Risks:**
- Error messages change for non-list inputs (see risk 1 and 3 above)
- Truthiness narrowing for `filter` (risk 2 above)
- Private accumulator helpers (`map_acc`, `filter_acc`) become visible in the prelude env unless prefixed with `_`; if prefixed they are Python-registered; if left as plain names they appear in `help()` — naming convention needs decision in spec phase

**Test impact:**
- `reduce-on-flow-type-error.yaml` must be updated with the new error message
- All existing list HOF specs should continue to pass
- `reduce_none_propagation.genia` regression must continue to pass

**Docs impact:**
- `GENIA_STATE.md` section 1595: change "prelude wrappers over host-backed primitives" to "pure prelude implementations using `apply_raw`"
- `docs/host-interop/capabilities.md`: update `apply_raw` notes (remove reference to `_reduce`/`_map`/`_filter` as the motivation)

**Portability impact:** Reduces host-specific surface. Any future host only needs `apply_raw` (already required); no longer needs to implement `_reduce`/`_map`/`_filter` separately.

---

### Option B: Prelude implementations with private helper functions / accumulators (same as A)

This is effectively the same as Option A — `map_acc` and `filter_acc` are private accumulator helpers. The distinction from Option A is only naming convention: whether helper names use a `_` prefix or not.

**Benefits:** Same as A, with cleaner public API if helpers are prefixed.

**Risks:** If `_map_acc` / `_filter_acc` are Python-registered names, they bypass the autoload system. Alternatively, leaving them as plain names (`map_acc`, `filter_acc`) in the prelude file keeps them within the Genia autoload system but they appear as public-ish names.

**Recommended resolution:** Use plain prelude names (`map_acc`, `filter_acc`) without `_` prefix since the underscore convention signals Python-backed internals. The spec/design phase should confirm the naming.

---

### Option C: Keep Python builtins temporarily as hidden compatibility substrate

Leave `_reduce`, `_map`, `_filter` registered in Python, but also write recursive prelude implementations. During transition, the prelude calls `_reduce`/`_map`/`_filter` only as a fallback or for error handling.

**Benefits:**
- Preserves error messages exactly (risk 1 resolved)
- No spec changes needed for `reduce-on-flow-type-error.yaml`
- Incremental migration possible

**Risks:**
- Semantic duplication: two implementations of the same logic
- `_reduce`/`_map`/`_filter` must remain registered even when not needed
- Portability surface is not reduced until the Python builtins are eventually removed
- Creates a confusing intermediate state

**Recommendation:** Do not choose as the primary direction. If error-message preservation is required, add a narrow explicit error path in the prelude instead (spec phase decision).

---

### Option D: Remove Python `_reduce`, `_map`, `_filter` immediately after migration

After successfully reimplementing in prelude (Option A), immediately unregister `_reduce`, `_map`, `_filter` from the Python env.

**Benefits:**
- Fully removes host-specific HOF logic
- Clean break with no dead code

**Risks:**
- If any existing code directly calls `_reduce(...)` (unlikely but should be verified), it breaks
- Combines the extraction step with a cleanup step — violates single-zone rule
- Hard to bisect if issues arise

**Recommendation:** Defer this to a separate cleanup issue. The extraction (#190) should prove all specs pass first; the removal of Python builtins should be a follow-up committed in a later audit step or separate issue.

---

### Option E: Defer extraction despite #188

Accept that `apply_raw` exists but leave `reduce`, `map`, and `filter` Python-backed for now.

**Benefits:**
- No changes required
- No risk to existing behavior
- No spec updates needed

**Risks:**
- The stated motivation of #188 was to unblock this exact extraction; deferring undermines the goal
- Every future host must still implement three separate HOF builtins
- Portability surface remains unnecessarily large

**Recommendation:** Do not defer. #188 is complete, the blocker is removed, the risk is manageable.

---

## 6. RECOMMENDED DIRECTION

**Recommended: Option A — Direct recursive prelude implementations using `apply_raw` with accumulator helpers, Python builtin removal deferred.**

Reasoning:

1. **`apply_raw` is already proven**: six shared specs validate the none-bypass contract. The extraction path is clear.
2. **Accumulator pattern is established**: `take_acc`, `range_acc`, `length_acc`, `reverse_acc` in `list.genia` use the same pattern. `map_acc` / `filter_acc` follow the convention.
3. **TCO covers deep lists**: Genia guarantees TCO for tail-position calls, so both `reduce` and the accumulator helpers are safe for large lists.
4. **No parser/Core IR changes**: pure prelude replacement.
5. **Flow path is unaffected**: the evaluator-level override for `map`/`filter` with Flow arguments operates on `GeniaFunctionGroup` by name, not by implementation body. A prelude reimplementation still produces a `GeniaFunctionGroup`, so the override continues to work.
6. **Defer Python builtin removal**: keep `_reduce`/`_map`/`_filter` registered during the initial migration. Remove them in a separate follow-up after proving all tests pass.

**On the error-message risk**: The `reduce-on-flow-type-error.yaml` spec asserts a specific Python error message. In the spec phase, decide one of:
- (a) Update the spec to assert the new pattern-match error message the prelude `reduce` produces, or
- (b) Add an explicit type-guard clause to the prelude `reduce` that raises a meaningful error for non-list inputs using `_reduce_type_error` or a similar mechanism

Option (a) is cleaner from a portability standpoint — the error behavior becomes language-defined rather than Python-string-defined. Option (b) preserves backward compatibility exactly.

**On truthiness narrowing**: Use `== true` boolean check for `filter`, consistent with `any?` and `find_opt` in the same file. Document in the spec that `filter` predicates must return boolean `true` or `false`. All existing specs already use boolean predicates; no current test is broken by this.

---

## 7. TEST STRATEGY FOR LATER PHASES

Do not write tests now.

Recommended future tests/specs for the `test` phase:

**`reduce` basic behavior:**
- `reduce((acc, x) -> acc + x, 0, [1,2,3,4])` → `10`
- `reduce((acc, x) -> acc + x, 0, [])` → `0` (empty list returns acc)
- Named function callback: same result as lambda callback

**`map` basic behavior:**
- `map((x) -> x + 1, [1,2,3])` → `[2,3,4]`
- `map((x) -> x + 1, [])` → `[]`
- Order preservation: `map((x) -> x, [3,2,1])` → `[3,2,1]` (identity, must preserve order)

**`filter` basic behavior:**
- `filter((x) -> x % 2 == 0, [1,2,3,4,5])` → `[2,4]`
- `filter((x) -> x % 2 == 0, [1,3,5])` → `[]`
- Order preservation: filtered result preserves original element order

**Empty list behavior:**
- All three HOFs on `[]` return their correct base values without error

**Callback receives `none(...)`:**
- `map((o) -> unwrap_or(0, o), [none("a"), some(2)])` → `[0, some(2)]`... wait, actually `some(2)` is passed as-is to the callback; the callback receives the raw list element. The prelude `map` must pass each element raw via `apply_raw`, so `some(2)` is delivered as `some(2)`. The callback `unwrap_or(0, some(2))` returns `2`. Confirmed expected: `[0, 2]`.
- `reduce((acc, o) -> acc + unwrap_or(0, o), 0, [some(1), none("x"), some(3)])` → `4`
- `filter((o) -> some?(o), [some(1), none("x"), some(3)])` → `[some(1), some(3)]`

**Callback can unwrap `none(...)`:**
- Already covered by the option-element cases above

**Callback errors still propagate:**
- `map((x) -> 1 / 0, [1])` → raises runtime error
- `reduce((acc, x) -> 1 / 0, 0, [1])` → raises runtime error

**Named functions and lambdas both work:**
- Verify `reduce(add, 0, [1,2,3])` (named function) produces same result as lambda form

**Flow `map` / `filter` behavior unchanged:**
- All existing `spec/flow/flow-map-*.yaml` and `spec/flow/flow-filter-*.yaml` must continue to pass

**Non-list `reduce` input:**
- Whatever error the new prelude implementation produces for `reduce(f, 0, flow)` must be documented and spec-tested; update or replace `reduce-on-flow-type-error.yaml` accordingly

**Shared spec coverage proving portability:**
- Add a new `spec/eval/stdlib-reduce-basic.yaml` covering at minimum: sum over `[1,2,3,4]` → `10`
- Add a new `spec/eval/stdlib-reduce-empty.yaml`: sum over `[]` → `0`
- Ensure existing `stdlib-map-*` and `stdlib-filter-*` shared specs still pass

---

## 8. DOC IMPACT

Do not update docs now. Docs likely needing updates in later phases:

- **`GENIA_STATE.md`**: Section 1594–1595 — change "prelude wrappers over host-backed primitives" to reflect that `reduce`, `map`, `filter` are now native prelude functions using `apply_raw`
- **`GENIA_RULES.md`**: No changes expected unless the truthy/boolean contract for predicates is explicitly codified
- **`GENIA_REPL_README.md`**: Section on autoloaded stdlib functions — update the `reduce`, `map`, `filter` description to note pure prelude implementation; the surface names and arities do not change
- **`README.md`**: Minor update to autoloaded prelude description if the "prelude wrappers over host-backed" phrasing appears
- **`docs/host-interop/capabilities.md`**: Update the `apply_raw` notes entry (currently says "This is the public equivalent of the internal `_invoke_raw_from_builtin` used by `reduce`, `map`, and `filter`") to reflect that the internal use is no longer needed; `_reduce`/`_map`/`_filter` may be removed
- **`spec/eval/reduce-on-flow-type-error.yaml`**: Must be updated or replaced to match the error message produced by the prelude implementation

---

## 9. PORTABILITY ANALYSIS

### Classification of the new solution

- **Prelude helper**: `reduce`, `map`, `filter` become pure Genia prelude functions. Their accumulator helpers (`map_acc`, `filter_acc`) are also prelude helpers.
- **Host primitive required**: only `apply_raw` — already required and already part of the language contract since #188.
- **No new language contract**: no new syntax, no new Core IR nodes, no new option semantics.

### How this reduces host-specific semantic surface

Currently, every Genia host must implement three separate HOF builtins (`_reduce`, `_map`, `_filter`) with `skip_none_propagation=True` semantics. After extraction:
- Hosts need only `apply_raw` (already required)
- The list HOF logic lives in the shared prelude layer, executed by any host
- This is a net reduction of 3 host-specific semantic requirements to 0 (beyond `apply_raw`)

### Portability chain

```
apply_raw (host primitive, language contract)
  → reduce/map/filter (prelude, pure Genia, portable)
    → count, find_opt, any? (prelude, already pure)
```

---

## 10. RISK ANALYSIS

| Risk | Severity | Mitigation |
|---|---|---|
| `reduce-on-flow-type-error.yaml` spec fails after extraction | High | Spec phase must update or replace the spec with the new error message, or add explicit error guard in prelude `reduce` |
| `filter` truthiness narrowing (`== true` vs Python `truthy()`) | Low | All current specs use boolean predicates; document predicate contract as boolean-returning; consistent with `any?`/`find_opt` patterns |
| Flow `map`/`filter` path broken | Low | The evaluator Flow override checks `isinstance(fn, GeniaFunctionGroup)` by name; prelude reimplementation still produces a `GeniaFunctionGroup`; override is unaffected |
| TCO assumption violated in deep lists | Low | `reduce` is naturally tail-recursive; `map`/`filter` use accumulator pattern which is also tail-recursive; Genia TCO guarantees cover these |
| Order preservation in `map` changed | Low | Accumulator appends with `[..acc, apply_raw(f,[x])]` — same left-to-right order as Python list comprehension |
| Python builtins removed prematurely | Medium | Do not remove `_reduce`/`_map`/`_filter` in this issue; defer to a follow-up cleanup issue |
| `map_acc`/`filter_acc` exposed as public names | Low | Spec/design phase should confirm naming convention; plain names in prelude are autoloadable but are not doc-exposed unless annotated with `@doc` |
| Callback `none(...)` behavior regressed | Low | `apply_raw` specs already validate the none-bypass contract; `reduce_none_propagation.genia` regression test covers the HOF cases |
| Docs claiming more than implementation proves | Medium | Follow AGENTS.md: only update docs in the docs phase, after implementation and audit confirm behavior |

---

## 11. RELATIONSHIP TO #117 / #181 / #188

- **#117** is the parent extraction epic. Its goal is to reduce host-specific semantic surface by moving pure helpers to prelude. `reduce`, `map`, and `filter` are high-impact candidates.
- **#181** is the inventory issue that classified `reduce`, `map`, and `filter` as the first safe focused extraction slice after the `apply_raw` blocker was resolved. #181 is inventory only and must not become implementation work.
- **#188** removed the raw-callback blocker by introducing `apply_raw`. Without #188, this extraction is impossible. #188 is now complete and its specs are in place.
- **#190** (this issue) is intentionally scoped to only `reduce`, `map`, and `filter`. It must not combine with other extraction candidates from #181 (e.g., `map_items`, `pairs`, display helpers, validation helpers).

Dependency chain:
```
#117 (parent: extract pure helpers)
  → #181 (inventory: identifies reduce/map/filter as first target)
  → #188 (apply_raw: removes the blocker)
  → #190 (this: extracts reduce/map/filter using apply_raw)
```

---

## 12. FINAL GO / NO-GO

**GO for moving to spec phase.**

### Blockers resolved

- `apply_raw` is implemented, tested, and language-contract-stable (#188 complete).
- The mechanism for delivering `none(...)` elements to callbacks from Genia prelude code is proven.
- The Flow / list overloading is verified to be unaffected by prelude reimplementation.
- TCO covers the tail-recursive and accumulator-based implementations.
- Existing specs for list HOFs all use boolean predicates, so the truthiness narrowing does not affect current coverage.

### Remaining items for spec phase (not blockers, but must be decided)

- Confirm the exact prelude structure: pure multi-arm vs public helper delegating to a private recursive helper.
- Confirm naming convention for accumulator helpers (`map_acc` / `filter_acc` vs `_map_acc` / `_filter_acc`).
- Decide on error behavior for `reduce` with non-list input: update `reduce-on-flow-type-error.yaml` with the new message, or add an explicit error guard.
- Add `spec/eval/stdlib-reduce-basic.yaml` and `spec/eval/stdlib-reduce-empty.yaml` to close the shared spec gap for `reduce`.

### Recommended next issue/prompt

Spec phase for issue #190: define the observable behavior of the new prelude `reduce`, `map`, and `filter`, add new shared spec YAML cases for `reduce` basic behavior, and update `reduce-on-flow-type-error.yaml` to match the new error message.

### Recommended branch name for spec

`issue-190-prelude-list-hofs-spec`

### Recommended commit message

```
spec(list): define reduce/map/filter prelude behavior and update error spec for issue #190
```

---

*Preflight complete. No implementation, no tests, no docs sync beyond this artifact. Branch: issue-190-prelude-list-hofs-preflight.*
