# Issue 183 Design: Extract `pairs(xs, ys)` to Prelude

## 1. Purpose

Implement the approved `pairs(xs, ys)` contract by moving the successful list-zipping behavior out of the Python host `_pairs` binding and into `src/genia/std/prelude/map.genia`.

This design preserves the existing public API and observable behavior. It does not add a new helper, syntax form, Flow behavior, or map traversal behavior.

## 2. Scope Lock

Included:

- Replace the current public `pairs(xs, ys)` delegation to `_pairs(xs, ys)` with a prelude-level recursive definition.
- Preserve output shape as ordinary list values: `[[x, y], ...]`.
- Preserve shorter-input truncation and empty-list behavior.
- Preserve current non-list TypeError messages.
- Remove the Python `_pairs` binding and `pairs_fn` after tests prove no behavior loss.

Excluded:

- No changes to `map`, `filter`, `reduce`, or `_reduce_error`.
- No changes to Flow `map` / `filter` paths or Flow `zip`.
- No public `zip`, `zip_with`, or `enumerate` helper.
- No public API change.

## 3. Architecture Overview

`pairs` remains a public prelude helper autoloaded from `src/genia/std/prelude/map.genia`.

The success path should live in Genia code:

- pattern-match both arguments as list values
- emit one two-element list per lockstep pair
- stop recursion when either input list is empty

The Python host should no longer provide `_pairs` as the implementation of zipping. The only acceptable remaining host involvement is a private, narrow error helper if needed to preserve the exact existing TypeError text for non-list arguments.

## 4. File / Module Changes

New files:

- None for implementation.

Modified files in later phases:

- `src/genia/std/prelude/map.genia`
  - Replace `_pairs` delegation with recursive Genia clauses.
  - Add any private prelude helper clauses needed for readable structure.

- `src/genia/interpreter.py`
  - Remove `pairs_fn`.
  - Remove `env.set("_pairs", pairs_fn)`.
  - Add or reuse a private error-only helper only if needed for exact non-list TypeError preservation.
  - Keep `env.register_autoload("pairs", 2, "std/prelude/map.genia")`.

- `tests/unit/test_maps.py`
  - Keep existing behavior coverage.
  - Add focused coverage for non-list first and second arguments if absent.

- `spec/eval/`
  - Keep existing public eval specs.
  - Add or update public eval error coverage only in the test phase if shared error behavior is required by the contract stage.

Removed files:

- None.

## 5. Data Shapes

Input:

- `xs`: ordinary Genia list value
- `ys`: ordinary Genia list value

Output:

- ordinary Genia list value
- each item is an ordinary two-element Genia list: `[x, y]`
- no output item may be a host tuple, Pair value from `cons`, Flow value, map item wrapper, or Option value

Failure data:

- first-argument non-list failure message:
  - `pairs expected a list as first argument, received <type>`
- second-argument non-list failure message:
  - `pairs expected a list as second argument, received <type>`

## 6. Function / Interface Design

Public interface:

- `pairs(xs, ys)`
  - unchanged arity and name
  - still autoloaded from `src/genia/std/prelude/map.genia`
  - returns a list of two-element lists

Private implementation interface:

- A recursive prelude helper may be introduced if it keeps the public `pairs` clauses simple.
- A private host error helper may be introduced only for exact TypeError preservation.
- No new public helper is introduced.

## 7. Control Flow

Successful list inputs:

1. If the first list is empty, return `[]`.
2. If the second list is empty, return `[]`.
3. If both lists have a head and tail, produce `[x, y]` followed by the recursive result for the tails.

Failure paths:

1. Detect first-argument non-list values before accepting a catch-all second-argument failure.
2. Detect second-argument non-list values after the first argument is known to be list-shaped.
3. Raise the exact TypeError message required by the contract.

The design must avoid a generic unmatched-function dispatch error for non-list arguments.

## 8. Error Handling Design

Errors are contract-visible and must not drift.

The prelude implementation should route non-list cases to a private error boundary rather than relying on generic function dispatch failure.

The private error boundary must:

- raise `TypeError`
- use `_runtime_type_name`-style Genia runtime type names
- distinguish first and second argument positions
- return no value

The old `_pairs` implementation must not remain as the success-path implementation.

## 9. Integration Points

Autoload:

- `pairs/2` remains registered in `src/genia/interpreter.py`.
- `help("pairs")` remains sourced from the `@doc` metadata in `map.genia`.

Map helpers:

- `map_new`, `map_get`, `map_put`, `map_has?`, `map_remove`, `map_count`, and `map_items` remain host-backed.
- `map_keys` and `map_values` remain prelude compositions over `map_items` and list `map`.
- `pairs` becomes independent of the persistent map runtime.

Flow:

- No integration with Flow `zip`.
- Passing a Flow to `pairs` follows the non-list TypeError contract.

CLI / REPL:

- No mode-specific behavior.
- Display output remains the ordinary list display already covered by existing eval specs.

## 10. Test Design Input

Future test phase should include failing tests before implementation.

Behavior cases:

- equal lists
- shorter first list
- shorter second list
- empty first list
- empty second list
- both lists empty
- string values
- nested/list values if useful for shape confidence

Shape cases:

- output is a list
- each output item is a list
- no output item is a Python tuple
- pattern matching with `[x, y]` works

Pipeline cases:

- `[xs, ys]`-style direct use is not needed
- `pairs(xs, ys) |> map(...)` should continue to work

Error cases:

- non-list first argument preserves the exact first-argument TypeError message
- non-list second argument preserves the exact second-argument TypeError message
- Flow input receives the non-list message with runtime type `flow`

Removal cases:

- `_pairs` is no longer a resolvable Genia name after implementation.

## 11. Doc Impact

Already updated in contract phase:

- `GENIA_STATE.md`
- `GENIA_RULES.md`

Future docs phase:

- Update `README.md` wording where it groups `pairs` with host-backed map helpers.
- Update `GENIA_REPL_README.md` only if it implies `pairs` is host-backed.
- Keep docs concise and implementation-aligned.

## 12. Constraints

Must:

- follow existing prelude recursion and pattern matching style
- preserve current public behavior
- keep the public API unchanged
- keep docs truthful about host-backed map runtime versus pure/prelude `pairs`

Must not:

- add public helpers
- add zip-like APIs
- touch Flow optimization paths
- touch `map`, `filter`, `reduce`, or `_reduce_error`
- keep `_pairs` as the zipping implementation

## 13. Complexity Check

Minimal: yes.

Necessary: yes.

Over-engineered: no.

Explanation:

The success algorithm is a small recursive list function. The only extra complexity is preserving exact non-list TypeError text; that should be isolated at a private error boundary instead of retaining the old host-backed zipping primitive.

## 14. Final Check

- Matches the approved contract.
- Does not introduce new public behavior.
- Does not include implementation code.
- Provides test-stage inputs.
- Ready for failing-test phase.
