# Issue #162 Spec - Stdlib Phase 1 Normalization

## 1. Scope

This issue defines a narrow semantic-normalization contract for the current public stdlib/prelude surface.

Included in this phase:

- contract inventory for public helpers used in common pipelines
- public data-shape rules for visible structured stdlib results
- explicit classification of helpers as value, Flow, bridge, option-aware, polymorphic, sink, or host-only surface
- coordination with issue #140 for pair-like public values
- later executable coverage for only the behavior approved by this spec and design

Excluded from this phase:

- implementation
- executable spec or test additions in the spec phase
- docs sync in the spec phase
- tuple destructuring
- making tuples a public Genia value type
- new syntax
- value templates or type features
- broad Flow redesign
- repo-wide rename
- changes to AST, IR, dispatch tuple, or host-internal tuple structures

This issue is semantic alignment of existing public surface behavior. It is not a general cleanup pass.

## 2. Relationship To Issue #140

Issue #140 owns the narrow pair-like public-value rule:

- public pair-like values must be 2-element Genia lists
- public APIs must not expose Python tuples
- internal tuples remain implementation details

Issue #162 depends on that rule for its first normalization slice.

Spec decision:

- Treat #140 as the pair-shape subtask for #162 unless maintainers choose to complete #140 separately first.
- If #140 lands first, #162 must consume its settled contract and avoid duplicating it.
- If #162 subsumes #140, the first design/test/implementation slice must be limited to the #140 pair-shape contract before broader stdlib classification work proceeds.

No later phase may implement broader stdlib changes while leaving the pair-shape rule ambiguous.

## 3. Public Data-Shape Contract

Public, user-visible structured values returned by stdlib helpers must be pattern-matchable using existing Genia value forms.

Allowed public structured result families:

- lists
- maps
- Options: `some(value)` and `none(...)`
- documented opaque runtime values where already public, such as Flow, Module, map values, refs, process handles, cells, actors, sinks, and host-only handles
- immutable Genia pairs only through the existing `cons` / `car` / `cdr` / `pair?` / `null?` pair surface and quote/stream behavior already documented

Required pair-like shape:

- pair-like public values use 2-element lists
- map entries are `[key, value]`
- zip entries are `[left, right]`
- state-step returns for `scan` are `[next_state, output]`
- helper names that consume pair-like values must consume the same list shape at the public boundary

Forbidden public shape:

- Python tuples must not be part of public stdlib return values
- tuple-like display must not leak through public stdlib results
- host-only tuple structures must not be described as Genia user values

Internal tuples remain allowed for:

- function dispatch argument tuples
- parser, AST, IR, and lowering internals
- map key freezing and host runtime bookkeeping
- host adapter or bridge internals
- Python implementation details that are normalized before crossing the public Genia boundary

## 4. Helper Classification Contract

Later design must classify affected public helpers using these categories. A helper may belong to more than one category only when the current documented behavior already supports that shape.

Value helpers:

- receive ordinary Genia values and return ordinary Genia values or Options
- examples in current surface: list helpers such as `reduce`, `sum`, `count`, `first`, `last`, `nth`, `take`, `drop`, `reverse`; map helpers such as `map_get`, `map_items`, `map_keys`, `map_values`; string helpers such as `parse_int`, `find`, `split`, `split_whitespace`

Flow helpers:

- receive a Flow and return a Flow
- examples in current surface: `keep_some`, `keep_some_else`, `scan`, `rules`, `refine`, `each`, `tee`, `merge`, `zip`, `head`

Polymorphic helpers:

- support both ordinary values and Flows only where already implemented and documented
- current candidates: `map`, `filter`, `take`/`head`
- polymorphism must not silently create new value/Flow bridge behavior

Bridge helpers:

- intentionally cross the value/Flow boundary
- current source bridges: `lines`, `tick`, `stdin_keys`
- current materialization bridge: `collect`
- current effect bridge: `run`

Option-aware helpers:

- explicitly consume, preserve, inspect, recover from, or route `some(...)` / `none(...)`
- examples in current surface: `map_some`, `flat_map_some`, `then_get`, `then_first`, `then_nth`, `then_find`, `unwrap_or`, `or_else`, `or_else_with`, `absence_reason`, `absence_context`, `absence_meta`, `keep_some`, `keep_some_else`

Mode-transparent helpers:

- return the input value shape unchanged except for documented side effects
- current examples: `inspect`, `trace`, `tap`

Host-only public helpers:

- remain Python reference host behavior unless and until promoted through the shared contract
- examples include refs, processes, file/zip, web, cells, actors, simulation, and shell pipeline stage behavior
- host-only helpers must not define language semantics beyond `GENIA_STATE.md`

## 5. Flow And Value Boundary Contract

The existing boundary rule remains unchanged:

- raw values stay values
- Flows stay Flows
- only explicit bridges cross the boundary

This issue must not add implicit Flow/value conversion.

Later behavior coverage should prove:

- reducers such as `sum`, `count`, and `reduce` operate on values and require explicit `collect` when starting from Flow
- Flow stages receive Flow values in Flow contexts
- bare per-item value helpers used directly as pipe-mode stages continue to receive the whole Flow and produce documented guidance where covered
- `collect` materializes Flow to list and leaves later stages in value world
- `run` consumes Flow for effects and is not a general value-returning reducer

## 6. Option Contract

The existing Option pipeline contract remains unchanged:

- `none(...)` short-circuits remaining pipeline stages and returns unchanged
- `some(x)` lifts through ordinary non-Option-aware pipeline stages
- lifted stages receive `x`
- lifted non-Option results are wrapped as `some(result)`
- lifted stages that return `some(...)` or `none(...)` preserve that Option result
- direct calls do not gain pipeline lifting behavior

This issue must not add new implicit unwrapping.

Option-friendly stdlib behavior must be explicit:

- single Option values use direct option helpers such as `map_some`, `flat_map_some`, `then_*`, `unwrap_or`, `or_else`, or metadata helpers
- Flow item Options use Flow helpers such as `keep_some` and `keep_some_else`
- value-side list processing over Option elements must use explicit callbacks or recovery helpers

## 7. Pair-Like Public Shape Inventory

The first later design slice must inventory and settle these pair-like public surfaces:

- `map_items(map)` result entries
- `map_item_key(item)` and `map_item_value(item)` accepted public item shape
- `map_keys(map)` and `map_values(map)` as derived shape consumers
- `zip(flow1, flow2)` output items
- `zip(pair)` where `pair` comes from public `tee(flow)` usage
- `merge(pair)` where `pair` comes from public `tee(flow)` usage
- `scan(step, initial_state, flow)` step return shape
- public display/formatting of returned structured values

Required contract for these surfaces:

- `map_items(m)` returns `[[key, value], ...]`
- `zip(...) |> collect` returns `[[left, right], ...]`
- `scan` step functions return `[next_state, output]`
- helper consumption of public pair-like values accepts the documented list pair shape
- no public examples should require Python tuple knowledge

If a currently implemented helper accepts host tuples for compatibility, that acceptance must be documented as Python reference host implementation tolerance only, not as a portable public value shape.

## 8. Category Placement For Later Executable Coverage

Later executable coverage must use the active shared categories according to behavior under test:

- `eval`
  - value-side stdlib outputs
  - map item/list pair shape
  - pipeline Option propagation that is not CLI-specific
  - value-vs-Flow examples that do not depend on CLI wrapper behavior

- `flow`
  - direct command-source Flow behavior such as `stdin |> lines |> ...`
  - direct Flow helper shape such as `zip`, `scan`, `keep_some`, and `collect`
  - Flow misuse only where the normalized error is already stable enough for shared assertion

- `cli`
  - pipe-mode wrapper behavior
  - pipe-mode guidance for bare per-item helpers, reducers, or non-Flow final values
  - command-mode vs pipe-mode differences

- `error`
  - only stable, documented normalized failures that belong outside CLI mode

Do not use shared specs to assert host-internal object layout, Python traceback details, or undocumented error wording.

## 9. Minimal Later Coverage Inventory

The later design and failing-test phases should choose a small inventory from these contract facts.

Required shape proofs:

- `map_items` returns list entries shaped `[key, value]`
- `map_items |> map(map_item_key)` and `map_items |> map(map_item_value)` work without tuple knowledge
- `zip` emits list pairs
- `scan` accepts only the documented `[next_state, output]` step result shape

Required boundary proofs:

- value pipeline with `map` / `filter` / reducer remains value-side
- Flow pipeline with `map` / `filter` / `keep_some` remains Flow-side until `collect` or `run`
- reducers require explicit `collect` after Flow
- pipe mode remains a Flow-stage wrapper rather than a generic value-eval mode

Required Option proofs:

- direct Option helpers operate on single Option values
- `keep_some` and `keep_some_else` are Flow item-routing helpers
- common parse/filter/sum pipelines use `keep_some`, `keep_some_else`, or explicit recovery before reduction

Regression families:

- `stdin |> lines |> map(split_whitespace) |> map((r) -> nth(4, r)) |> keep_some`
- `stdin |> lines |> map(parse_int) |> keep_some |> collect |> sum`
- `map_items(m) |> map(map_item_key)`
- `source |> tee |> zip |> collect`

The later design phase must reduce this inventory to the smallest useful slice for the next failing-test phase.

## 10. Failure Behavior Constraints

Failure coverage must be narrow and stable.

Candidate failures:

- public pair consumer receives an invalid shape
- `scan` step returns a non-2-element list shape
- a value reducer receives a Flow without `collect`
- a Flow helper receives a value after `collect`
- `keep_some` receives non-Option flow items
- `keep_some_else` stage returns a non-Option result

Failure assertions must use documented normalized surfaces only:

- exact `stdout`, `stderr`, and `exit_code` in shared specs where appropriate
- pytest exception assertions only in later repository tests where host-local behavior is under test

Do not freeze new diagnostic wording in the spec phase.

## 11. Non-Goals

Out of scope:

- public tuple values
- tuple destructuring
- tuple indexing
- new pair syntax
- new Flow ports
- implicit list-to-Flow conversion
- implicit Flow-to-list conversion
- changing pipeline lifting rules
- replacing `rules` with `refine` or removing compatibility names
- replacing `get?`, `first_opt`, or `nth_opt`
- new host adapter behavior
- non-Python host implementation

## 12. Implementation Boundary

This spec is behavior-only.

Later implementation may touch only the minimal files required by the approved design and failing tests.

Implementation must not:

- redefine language behavior inside host adapters
- expose Python tuples to users
- alter Core IR portability boundaries
- change AST/IR internals for public-shape cleanup unless a later design explicitly proves it is required
- rename broad stdlib surfaces in one pass

## 13. Documentation Truth Requirements

Later docs sync must start from `GENIA_STATE.md`.

Docs must:

- describe only implemented and tested normalization behavior
- keep Flow coverage marked partial where appropriate
- keep Python-host-only helpers labeled
- describe tuple tolerance, if any remains, as implementation detail only
- avoid claiming that all stdlib behavior is stable across hosts
- keep examples classified and executable where required by existing doc rules

Potential later truth surfaces:

- `GENIA_STATE.md`
- `GENIA_RULES.md`
- `GENIA_REPL_README.md`
- `README.md`
- `docs/cheatsheet/piepline-flow-vs-value.md`
- `docs/cheatsheet/core.md`
- `docs/cheatsheet/quick-reference.md`
- `docs/cheatsheet/unix-power-mode.md`
- `docs/cheatsheet/unix-to-genia.md`
- `docs/host-interop/*`
- `docs/contract/semantic_facts.json` only if protected semantic facts change

Those edits belong to later docs phase, not this spec phase.

## 14. Acceptance Criteria For Later Phases

Issue #162 is complete only when:

- the public/prelude helper inventory is explicit enough for users to know value vs Flow vs bridge vs Option helper behavior
- public pair-like values use 2-element lists
- public APIs do not expose Python tuples as user values
- common pipeline examples work without tuple or host-shape knowledge
- Flow/value misuse is covered by clear tests or shared specs where appropriate
- Option helper behavior remains explicit and consistent
- issue #140 is either completed first or closed by the first pair-shape slice of #162
- docs are synchronized after implementation and tests land
- audit confirms no broad rename, syntax expansion, or host-leaky contract drift

## Spec Decision Summary

This issue should proceed as a split normalization effort:

1. pair-like public shape contract, coordinated with #140
2. value-vs-Flow helper classification and targeted behavior coverage
3. Option-aware helper consistency for common pipelines
4. docs sync and audit after behavior is tested and implemented

The next Design phase must map this contract into the smallest concrete first slice, with #140 pair-shape coordination resolved before any broader stdlib changes.
