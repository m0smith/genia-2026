# Issue #140 Design — Normalize Pair-Like Values to Lists

**Phase:** design
**Branch:** `issue-140-pair-lists-preflight`
**Issue:** #140 — Normalize Pair-Like Values to Lists (Remove Tuple Leakage from Public API)

This phase describes the implementation plan only.
It does not add failing tests, implementation code, or documentation sync edits.

---

## 1. Design Summary

Add `pairs(xs, ys)` as a host-backed primitive with a thin Genia prelude wrapper, following the exact same pattern as `map_items`. The function zips two lists into a list of 2-element Genia lists, bounded by the shorter input.

This is the only code change required for issue #140. All other public pair-like surfaces (`map_items`, `tee`, `zip`) were already normalized by issue #162 first slice.

---

## 2. Scope Lock

### Included

- New `pairs_fn` host primitive in `src/genia/interpreter.py`
- New `pairs` prelude wrapper in `src/genia/std/prelude/map.genia`
- `env.set("_pairs", ...)` registration adjacent to `env.set("_map_items", ...)`
- `env.register_autoload("pairs", 2, "std/prelude/map.genia")` adjacent to the other map autoloads
- `@doc` annotation on the prelude wrapper

### Excluded

- `pairs(xs)` single-arg form — not in scope
- Flow inputs to `pairs` — type error, not a new feature
- Pure-Genia recursive implementation — host primitive is chosen for correctness and performance
- Changes to existing map helpers, tee, zip, or scan
- Changes to Core IR, AST, parser, or lowering
- New syntax
- Tests — test phase only
- Docs sync — docs phase only
- Implementation code in this phase

---

## 3. Implementation Approach Decision

### Options evaluated

**Option A: Pure Genia recursive prelude function**

```genia
pairs([], _) = []
pairs(_, []) = []
pairs([x, ..xs], [y, ..ys]) = [[x, y], ..pairs(xs, ys)]
```

Pros: portable, no host dependency.
Cons: Genia-level recursion hits Python stack limits for large lists; not tail-recursive in the current evaluator.

**Option B: Host primitive + thin prelude wrapper** *(chosen)*

```python
# interpreter.py
def pairs_fn(xs: Any, ys: Any) -> list[list[Any]]:
    if not isinstance(xs, list):
        raise TypeError(f"pairs expected a list as first argument, received {_runtime_type_name(xs)}")
    if not isinstance(ys, list):
        raise TypeError(f"pairs expected a list as second argument, received {_runtime_type_name(ys)}")
    return [[x, y] for x, y in zip(xs, ys)]
```

```genia
# map.genia
pairs(xs, ys) = _pairs(xs, ys)
```

Pros: consistent with `map_items` pattern; uses Python `zip` which is bounded by shorter input; no recursion risk; clear type validation using `_runtime_type_name`.
Cons: host-backed, but all other pair-like helpers are also host-backed.

**Decision: Option B.** Consistent pattern, correct behavior, safe at scale.

---

## 4. File and Module Plan

### `src/genia/interpreter.py`

**Where to add `pairs_fn`:**

Place the function definition immediately after `map_items_fn` (currently around line 6824–6826), within the same function scope that defines all map helper functions.

**Where to register:**

Add `env.set("_pairs", pairs_fn)` immediately after `env.set("_map_items", map_items_fn)` (currently line 7709).

**Where to add autoload:**

Add `env.register_autoload("pairs", 2, "std/prelude/map.genia")` immediately after `env.register_autoload("map_values", 1, "std/prelude/map.genia")` (currently the last map autoload, around line 7839).

### `src/genia/std/prelude/map.genia`

Add the `pairs` wrapper and `@doc` annotation after the `map_values` definition (the current last helper in the file).

**Exact text to add at the end of `map.genia`:**

```genia
@doc """Zip two lists into a list of `[x, y]` pairs.

Returns a list of 2-element lists, one per index, bounded by the shorter input.
Elements are pattern-matchable as `[a, b]` without tuple knowledge.

## Arguments
- `xs` — a list
- `ys` — a list

## Returns
A list of `[xs_item, ys_item]` pairs. Length equals `min(count(xs), count(ys))`.

## Examples

```genia
pairs([1, 2], [3, 4])
```
```text
[[1, 3], [2, 4]]
```
"""
pairs(xs, ys) = _pairs(xs, ys)
```

---

## 5. Function and Interface Design

### Public surface

```
pairs(xs, ys) -> [[xs_item, ys_item], ...]
```

- Arity: exactly 2
- Both args must be Genia lists
- Result: Python `list` of Python `list` items (same type as `map_items` entries)
- Result length: `min(len(xs), len(ys))` — bounded by the shorter input
- If either input is empty: result is `[]`

### Classification

- **Value helper** (list → list, no Flow, no Option, no host-only behavior)
- Portable: pure data operation, no Python-specific side effects
- No pipeline special behavior; works as an ordinary function in both call and pipeline position

### Type errors

| Condition | Error message |
|---|---|
| First arg is not a list | `"pairs expected a list as first argument, received <type>"` |
| Second arg is not a list | `"pairs expected a list as second argument, received <type>"` |

Type string uses `_runtime_type_name(value)` for consistency with all other type errors in the interpreter.

---

## 6. Data Shape Design

Output shape:
- Each element is a Python `list` of length 2: `[xs_item, ys_item]`
- The outer result is a Python `list` of those inner Python `list` values
- `format_debug` handles this correctly with existing `list` branch — no changes to `utf8.py` needed
- Pattern matching `[a, b] -> ...` works against each element without any new syntax

This matches the shape of `map_items` entries and `zip`-emitted items. All three are `[[a, b], ...]`.

---

## 7. `@doc` Annotation Design

The `@doc` annotation on `pairs` must pass the existing `@doc` linter (DOC001–DOC007):

- Non-empty first-line summary, ends with `.` (DOC001, DOC002)
- Only allowed sections: `## Arguments`, `## Returns`, `## Examples` (DOC003)
- No raw HTML (DOC004)
- No pipe tables (DOC005)
- Behavior mention: `none`, `flow`, or `lazy` is not applicable here — `pairs` is a plain list helper with no absence or flow semantics (DOC006 only triggers for helpers that interact with those concepts)
- Fences labeled `genia` or `text` (DOC007)

The `@doc` text in section 4 above satisfies these constraints.

---

## 8. Control Flow

Implementation flow for later phases:

1. **Test phase** — add failing spec YAML cases under `spec/eval/` and failing pytest cases in `tests/test_maps.py`; register spec names in `tests/test_spec_ir_runner_blackbox.py`; confirm all new tests are red; commit with `test(pairs): ...`
2. **Implementation phase** — add `pairs_fn` in `interpreter.py`, add `pairs` wrapper in `map.genia`, register both; reference the failing-test commit SHA in the commit message; confirm all tests turn green; commit with `feat(pairs): ...`
3. **Docs phase** — update `GENIA_STATE.md`, then `README.md`, then `GENIA_REPL_README.md` and cheatsheets as warranted; commit with `docs(pairs): ...`
4. **Audit phase** — run full test suite, spec runner, semantic doc sync; confirm no regression; commit with `audit(pairs): ...`

No step may merge into a previous step.

---

## 9. Error Handling Design

Two explicit type errors as described in section 5.

No new error categories are introduced.

The existing `_runtime_type_name` helper is sufficient for human-readable type names in error messages.

No shared `error` spec cases are required for `pairs` type errors in this phase — the error surface is new and narrow; pytest coverage is sufficient.

---

## 10. Shared Spec Placement

New cases go under `spec/eval/` only. `pairs` is a pure value helper — no Flow or CLI cases needed.

Planned spec case files (to be written in test phase):
- `spec/eval/pairs-basic.yaml`
- `spec/eval/pairs-shorter-first.yaml`
- `spec/eval/pairs-shorter-second.yaml`
- `spec/eval/pairs-empty-first.yaml`
- `spec/eval/pairs-empty-both.yaml`
- `spec/eval/pairs-strings.yaml`
- `spec/eval/pairs-pattern-match.yaml`

These cases are defined in `docs/architecture/issue-140-pairs-spec.md`.

---

## 11. Documentation Impact

No docs sync in this phase.

For the docs phase:
1. `GENIA_STATE.md` — add `pairs` to the map helper surface (§11); note Experimental maturity; add one-line description
2. `README.md` — add `pairs` to the autoloaded prelude list in the map helper family line
3. `GENIA_REPL_README.md` — add `pairs` to the autoloaded stdlib list at the appropriate location
4. `docs/cheatsheet/core.md` — add `pairs` example if the format already includes map helper examples
5. `docs/cheatsheet/quick-reference.md` — add `pairs` entry if the map helper section exists
6. `GENIA_RULES.md` — no change required

No doc may be updated until after the implementation phase confirms correct behavior.

---

## 12. Constraints

Must:
- follow the `map_items` host-primitive pattern exactly
- use `_runtime_type_name` for error messages
- place `_pairs` registration adjacent to `_map_items`
- place `register_autoload` adjacent to other `map.genia` autoloads
- write tests before implementation

Must not:
- add a single-arg `pairs(xs)` form
- accept Flow values
- change `map_items`, `tee`, `zip`, or any existing helper
- write implementation in this phase

---

## 13. Complexity Check

- Minimal: YES — one new function, one host primitive, one prelude wrapper, one registration
- Necessary: YES — `pairs` is the only unimplemented surface named in issue #140
- Over-engineered: NO — no optional forms, no Flow support, no Option wrapping

---

## 14. Recommended next prompt (TEST phase)

```
You are working in the Genia repo on issue #140:
Normalize Pair-Like Values to Lists (Remove Tuple Leakage from Public API)

Design is complete. Branch: issue-140-pair-lists-preflight.
Design doc: docs/architecture/issue-140-pairs-design.md
Spec doc: docs/architecture/issue-140-pairs-spec.md

Test phase task — write FAILING tests only, no implementation:

1. Create these shared spec YAML files under spec/eval/:
   - pairs-basic.yaml        pairs([1, 2], [3, 4])           → "[[1, 3], [2, 4]]\n"
   - pairs-shorter-first.yaml  pairs([1, 2], [10, 20, 30])   → "[[1, 10], [2, 20]]\n"
   - pairs-shorter-second.yaml pairs([1, 2, 3], [10, 20])    → "[[1, 10], [2, 20]]\n"
   - pairs-empty-first.yaml  pairs([], [1, 2])                → "[]\n"
   - pairs-empty-both.yaml   pairs([], [])                    → "[]\n"
   - pairs-strings.yaml      pairs(["a","b"],["x","y"])       → "[[\"a\", \"x\"], [\"b\", \"y\"]]\n"
   - pairs-pattern-match.yaml pairs([1,2],[3,4]) |> map(([a,b]) -> a+b) → "[4, 6]\n"

2. Register all 7 new spec case names in tests/test_spec_ir_runner_blackbox.py.

3. Add failing pytest cases in tests/test_maps.py:
   - test_pairs_basic
   - test_pairs_shorter_bound
   - test_pairs_empty
   - test_pairs_items_are_lists_not_tuples  (assert isinstance(item, list) for each)

4. Run the tests and confirm they are RED (failing). Show the failure output.

5. Commit with prefix: test(pairs): failing tests for pairs(xs, ys) issue #140

Do NOT implement pairs. Do NOT update GENIA_STATE.md or any behavior docs.
All tests must be failing when committed.
```
