# Issue #162 Design - Stdlib Phase 1 Normalization

## 1. Design Summary

This design maps the issue #162 spec into a split, implementation-ready plan.

The first implementation slice is the pair-like public-shape slice coordinated with issue #140. It is intentionally narrow:

- public pair-like stdlib values use 2-element Genia lists
- Python tuples remain internal implementation details only
- helper behavior is proved through existing eval/flow/cli shared surfaces and focused pytest coverage
- no broad stdlib rename, Flow redesign, syntax work, or docs sync happens in this phase

Later slices cover helper classification and Option consistency after the pair-shape rule is settled.

## 2. Scope Lock

This design follows the approved issue #162 spec.

Included for the first implementation slice:

- `map_items` public output shape
- `map_item_key` / `map_item_value` public input shape
- `zip` public output shape
- `tee` output as consumed by public `merge(pair)` and `zip(pair)` forms
- `scan` step result shape validation
- no public tuple leakage checks for the affected public surfaces
- minimal shared specs and repository tests in the later test phase

Excluded:

- implementation in design phase
- failing tests in design phase
- docs sync in design phase
- tuple destructuring
- public tuple values
- new syntax
- new stdlib helpers
- broad Flow redesign
- `rules` / `refine` rename work
- removing compatibility aliases
- non-Python host implementation
- AST, IR, parser, or Core IR shape changes

## 3. Relationship To Issue #140

Issue #140 is the first concrete subtask of issue #162 unless it is completed separately before implementation starts.

Design decision:

- The first test/implementation slice for #162 should satisfy #140's acceptance criteria for current public pair-like surfaces.
- If #140 remains open, later issue #162 work should explicitly mention that this slice closes or subsumes #140.
- If maintainers want #140 as a separate branch/PR, pause #162 after this design and do #140 first.

This design does not broaden #140 into all stdlib normalization. It uses #140 to settle the pair-like public shape invariant that #162 depends on.

## 4. Architecture Overview

Zones touched by later phases:

- Language Contract:
  - docs phase updates `GENIA_STATE.md` and aligned truth surfaces only after tests/implementation land.
- Docs / Tests / Examples:
  - shared spec cases and targeted pytest coverage prove the public shape contract.
- Host Adapters:
  - no host adapter changes planned for the first slice.
- Core IR:
  - no changes.
- Python reference runtime / prelude:
  - minimal runtime/prelude changes only if tests expose tuple leakage or mismatch with the approved contract.

The first slice should not change parser behavior, lowering, Core IR nodes, pipeline semantics, or shared runner schema.

## 5. Current Surface Findings

Current relevant implementation shape:

- `GeniaMap.items()` returns list-shaped entries, but its Python annotation currently says `list[tuple[Any, Any]]`.
- `map_items(map)` delegates to `_map_items(map)`.
- `map_item_key(item)` and `map_item_value(item)` pattern-match list pair shapes in prelude.
- `tee(flow)` currently returns a Python tuple of two Flow values internally.
- `_split_flow_pair(value, name)` accepts either tuple or list pairs for `merge(pair)` and `zip(pair)`.
- `zip(...)` yields public list pairs shaped `[left, right]`.
- `scan(step, initial_state, flow)` already documents `[next_state, output]` as the step result shape.

Current relevant truth:

- `GENIA_STATE.md` already says `map_items` returns `[key, value]` pairs.
- `GENIA_STATE.md` already says `zip` emits `[left, right]` pairs.
- #140 says public tuple leakage must be removed while internal tuples remain allowed.

## 6. First Slice Design

The first slice is "pair-like public shape normalization".

Design goals:

- make the public contract executable and regression-proof
- preserve internal tuple use where it is not user-visible
- normalize any public-facing return shape that still leaks Python tuples
- leave broader helper classification for later slices

Target public surfaces:

- `map_items(map)`
- `map_item_key(item)`
- `map_item_value(item)`
- `map_keys(map)`
- `map_values(map)`
- `tee(flow)` only through public consumption by `merge(pair)` and `zip(pair)`
- `zip(flow1, flow2)`
- `zip(pair)`
- `scan(step, initial_state, flow)`

Explicit non-targets for the first slice:

- Python tuple keys in maps as runtime interop values
- Python boundary conversion of host tuples to Genia lists
- tuple patterns in function dispatch or pattern matching
- `GeniaPair` / `cons` pair semantics
- stream internals built from pairs

## 7. File / Module Plan

Design artifact added in this phase:

- `docs/architecture/issue-162-stdlib-phase-1-normalization-design.md`

Planned later test/spec files:

- `spec/eval/map-items.yaml` may be kept or strengthened if needed.
- Add or strengthen eval coverage for:
  - `map_items(m) |> map(map_item_key)`
  - `map_items(m) |> map(map_item_value)`
- Add or strengthen flow coverage for:
  - `source |> tee |> zip |> collect`
  - `zip(flow1, flow2) |> collect`
  - `scan` valid `[next_state, output]` result
  - `scan` invalid result shape only if current diagnostic is stable enough for shared assertion
- Add pytest coverage for host-local checks that shared specs cannot observe precisely.

Planned later source/prelude files if tests fail:

- `src/genia/interpreter.py`
  - correct public-shape leakage if any exists
  - correct stale type annotations that imply public tuple return where the runtime returns lists
  - optionally return a list from `tee` if design/test phase confirms tuple return is public-visible and not just internal tolerance
- `src/genia/std/prelude/map.genia`
  - only if public list-pair validation or docstring precision needs prelude-level adjustment
- `src/genia/std/prelude/flow.genia`
  - only if `tee`/`merge`/`zip` public pair wording or validation needs prelude-level adjustment
- `src/genia/utf8.py`
  - only if display formatting leaks tuple-like syntax for public results

Planned later docs files:

- docs phase only, beginning with `GENIA_STATE.md`.

## 8. Data Shape Design

Public data shapes:

- map item: `[key, value]`
- zip item: `[left, right]`
- scan step result: `[next_state, output]`
- list of map items: `[[key, value], ...]`
- list of zip items after `collect`: `[[left, right], ...]`

Internal tolerated shapes:

- Python tuple storage inside map internals
- Python tuple dispatch args
- Python tuple return from helper internals only if normalized before user-visible display/result or explicitly treated as Python-host implementation tolerance

Boundary rule:

- if user code can render it, pattern-match it as a value, pass it to public helpers, or receive it as a final result, it must use Genia list/map/Option/pair/opaque public shapes, not Python tuple shape.

## 9. Function / Interface Design

No new public functions are introduced.

No public function names are renamed.

No arities change.

Existing public interfaces remain:

- `map_items(map)`
- `map_item_key(item)`
- `map_item_value(item)`
- `map_keys(map)`
- `map_values(map)`
- `tee(flow)`
- `merge(flow1, flow2)`
- `merge(pair)`
- `zip(flow1, flow2)`
- `zip(pair)`
- `scan(step, initial_state)`
- `scan(step, initial_state, flow)`

Compatibility choice:

- public helper consumers may continue accepting internal/host tuple pairs as Python reference host tolerance if already implemented.
- the portable public contract must document and test list pairs only.

## 10. Control Flow Design

Later test and implementation flow:

1. Add failing shared specs/pytest tests for first-slice public pair-like shape.
2. Confirm whether current runtime already passes some cases.
3. Implement only the smallest runtime/prelude corrections required by failing tests.
4. Keep internal tuple use unless it crosses the public boundary.
5. Defer value-vs-Flow inventory docs and Option-helper consistency implementation to later issue #162 slices.

No runner control-flow changes are planned.

No pipeline evaluator control-flow changes are planned.

## 11. Error Handling Design

Error behavior in the first slice must stay narrow.

Candidate stable assertions:

- `map_item_key` / `map_item_value` reject non-list-pair public inputs through current pattern-match failure behavior only if already deterministic enough.
- `scan` rejects a non-pair step result with existing clear error behavior if already stable.

Do not invent new diagnostics in the design.

If later tests show current diagnostics are unstable or host-leaky:

- assert only the stable portion in shared specs, or
- keep the check as host-local pytest coverage, or
- defer wording hardening to a later issue slice.

## 12. Shared Spec Placement

Use existing active categories only.

`eval` candidates:

- `map-items` existing case for direct output shape
- `map-item-key` existing case
- `map-item-value` existing case
- new case for `map_items(m) |> map(map_item_key)`
- new case for `map_items(m) |> map(map_item_value)`

`flow` candidates:

- direct `zip(flow1, flow2) |> collect` shape
- `source |> tee |> zip |> collect` shape
- `source |> tee |> merge |> collect` behavior if needed to prove tuple/list pair consumption remains public-safe
- valid `scan` `[next_state, output]` shape if not already covered by existing flow cases

`cli` candidates:

- none required for the first pair-shape slice unless pipe-mode public examples are selected later.

`error` candidates:

- none required unless later design revision selects stable shape failure diagnostics.

## 13. Test Design Input

The next TEST phase should add failing tests/specs before implementation.

Recommended smallest failing-test inventory:

- Shared eval:
  - map entries render as list pairs.
  - `map_items(m) |> map(map_item_key)` returns keys.
  - `map_items(m) |> map(map_item_value)` returns values.
- Shared flow or pytest:
  - `zip` emits list pairs.
  - `tee` output works through `zip(pair)` and produces list pairs after `collect`.
  - `scan` accepts `[next_state, output]`.
- Pytest host-local:
  - `GeniaMap.items()` returns list entries, not tuple entries.
  - public final result from `tee(flow)` is not asserted as portable if it remains an internal tuple tolerance point; if user-visible, test must define the intended public shape before implementation.

Test phase must not update implementation.

## 14. Later Slice Design Outline

After the pair-shape slice lands, later issue #162 design/test phases can address:

- value-vs-Flow classification inventory
- common Flow/value misuse coverage
- Option-aware helper consistency
- pipe-mode guidance coverage
- docs truth synchronization

Those later slices must be separate prompts and commits.

## 15. Documentation Impact

No docs sync in this phase.

Later docs phase should update only what implementation and tests prove:

- `GENIA_STATE.md` first
- then `GENIA_RULES.md`, `GENIA_REPL_README.md`, `README.md`, cheatsheets, and host interop docs only as needed
- semantic facts only if protected cross-doc wording changes

The docs phase must not claim broader stdlib stability or non-Python host support.

## 16. Constraints

Must:

- preserve the #162 spec boundary
- coordinate with #140
- keep public pair-like values pattern-matchable
- leave internal tuples internal
- keep Flow/value semantics unchanged
- keep Option pipeline semantics unchanged
- avoid broad rename

Must not:

- add syntax
- make tuples public
- change Core IR
- redesign Flow
- alter host adapter semantics
- mix implementation or tests into design

## 17. Complexity Check

Assessment:

- Minimal: Yes, for the first slice.
- Necessary: Yes, because #162 depends on settling public pair-like shape first.
- Over-engineered: No, because broader stdlib normalization is deferred.

Reason:

- The first slice reveals structure already claimed by `GENIA_STATE.md` and #140.
- It avoids turning stdlib normalization into a repo-wide cleanup.

## 18. Final Check

- Matches approved issue #162 spec.
- Resolves the #140 coordination decision for the first slice.
- Introduces no new behavior in design phase.
- Provides a concrete test/implementation target for the next phase.
- Keeps docs sync and audit for later prompts.
