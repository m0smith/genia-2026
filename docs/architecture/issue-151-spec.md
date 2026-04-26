# Issue #151 Spec

CHANGE NAME:
Add stdlib contract shared specs

Phase: spec

Issue: #151

Parent: #116

## 1. Purpose

Issue #151 adds executable shared specs for already-implemented core stdlib behavior.

The recovery preflight found that current `main` has stdlib-adjacent shared specs, but does not yet have focused shared contract coverage for `map`, `filter`, `first`, and closely related list/absence behavior. This spec defines that missing executable shared-spec inventory.

This phase defines expected behavior only. It does not add spec YAML files, runner tests, implementation changes, or documentation sync edits.

## 2. Source Of Truth

Final authority:

- `GENIA_STATE.md`

Supporting sources:

- `GENIA_RULES.md`
- `GENIA_REPL_README.md`
- `README.md`
- `spec/README.md`
- `spec/eval/README.md`
- `spec/flow/README.md`
- `spec/cli/README.md`
- `docs/architecture/issue-151-preflight.md`

Relevant existing truths:

- Python is currently the only implemented host and the reference host.
- Active executable shared spec categories are `parse`, `ir`, `eval`, `cli`, `flow`, and `error`.
- Shared eval specs assert normalized `stdout`, normalized `stderr`, and `exit_code`.
- Shared flow specs assert normalized `stdout`, normalized `stderr`, and `exit_code` for deterministic observable Flow behavior.
- Shared CLI specs assert normalized `stdout`, normalized `stderr`, and `exit_code` for deterministic non-interactive CLI behavior.
- `map` and `filter` are polymorphic helpers over lists and flows.
- `first`, `last`, `nth`, `reduce`, `sum`, and `count` are value functions, not Flow stages.
- `first(list)` returns `some(value)` or `none("empty-list")`.
- `last(list)` returns `some(value)` or `none("empty-list")`.
- `nth(index, list)` returns `some(value)` or `none("index-out-of-bounds", { index: i, length: n })`.
- List higher-order functions `reduce`, `map`, and `filter` deliver `none(...)` elements to callbacks instead of short-circuiting the outer call.
- Flow/value boundary misuse already has partial shared coverage and must remain aligned with existing diagnostics.

## 3. Scope

Included:

- Define focused executable shared specs for core stdlib behavior.
- Use existing shared spec categories only: `eval`, `flow`, and, where already relevant, `cli`.
- Cover normal list behavior for `map`, `filter`, and `first`.
- Cover closely related list/absence helpers that make the contract coherent: `last`, `nth`, and list-HOF Option-element callback behavior.
- Cover direct Flow `map`/`filter` observable behavior with explicit materialization.
- Cover only already-implemented behavior documented in `GENIA_STATE.md` and `GENIA_RULES.md`.
- Define runner/discovery expectations for later test phase.

Excluded:

- New language semantics.
- New stdlib functions.
- Broad stdlib normalization.
- Parser, Core IR, CLI mode, REPL, or Flow runtime redesign.
- Host adapter behavior changes.
- Changes to expected behavior of existing shared specs.
- Error-message redesign.
- Documentation updates outside phase artifacts.

## 4. Contract Surface

The shared stdlib contract for #151 is expressed through existing shared spec categories:

- `eval`: command-source evaluation for deterministic list/value stdlib behavior.
- `flow`: command-source execution with `stdin` for deterministic Flow stdlib behavior.
- `cli`: no new CLI behavior is required by this spec; existing CLI stdlib-adjacent cases remain valid.

No new shared spec category is introduced.

The observable comparison surface is unchanged:

- `stdout`
- `stderr`
- `exit_code`

Line-ending normalization follows the existing category behavior documented in `spec/README.md`.

## 5. Required Eval Shared Specs

Later phases must add executable `category: eval` YAML specs for the following cases.

### `stdlib-map-list-basic`

Purpose:

- Prove `map` transforms ordinary list values.

Source:

```genia
[1, 2, 3] |> map((x) -> x + 1)
```

Expected:

- `stdout`: `[2, 3, 4]\n`
- `stderr`: ``
- `exit_code`: `0`

### `stdlib-map-list-empty`

Purpose:

- Prove `map` over an empty list returns an empty list.

Source:

```genia
[] |> map((x) -> x + 1)
```

Expected:

- `stdout`: `[]\n`
- `stderr`: ``
- `exit_code`: `0`

### `stdlib-filter-list-basic`

Purpose:

- Prove `filter` keeps list items whose predicate returns true.

Source:

```genia
[1, 2, 3, 4, 5] |> filter((x) -> x % 2 == 0)
```

Expected:

- `stdout`: `[2, 4]\n`
- `stderr`: ``
- `exit_code`: `0`

### `stdlib-filter-list-no-match`

Purpose:

- Prove `filter` returns an empty list when no items match.

Source:

```genia
[1, 3, 5] |> filter((x) -> x % 2 == 0)
```

Expected:

- `stdout`: `[]\n`
- `stderr`: ``
- `exit_code`: `0`

### `stdlib-first-list-some`

Purpose:

- Prove `first` returns `some(value)` for a non-empty list.

Source:

```genia
first([7, 8, 9])
```

Expected:

- `stdout`: `some(7)\n`
- `stderr`: ``
- `exit_code`: `0`

### `stdlib-first-list-empty`

Purpose:

- Prove `first` returns structured absence for an empty list.

Source:

```genia
first([])
```

Expected:

- `stdout`: `none("empty-list")\n`
- `stderr`: ``
- `exit_code`: `0`

### `stdlib-last-list-some`

Purpose:

- Prove `last` returns `some(value)` for a non-empty list.

Source:

```genia
last([7, 8, 9])
```

Expected:

- `stdout`: `some(9)\n`
- `stderr`: ``
- `exit_code`: `0`

### `stdlib-last-list-empty`

Purpose:

- Prove `last` returns structured absence for an empty list.

Source:

```genia
last([])
```

Expected:

- `stdout`: `none("empty-list")\n`
- `stderr`: ``
- `exit_code`: `0`

### `stdlib-nth-list-some`

Purpose:

- Prove `nth` returns `some(value)` for an in-range index.

Source:

```genia
nth(1, [7, 8, 9])
```

Expected:

- `stdout`: `some(8)\n`
- `stderr`: ``
- `exit_code`: `0`

### `stdlib-nth-list-out-of-bounds`

Purpose:

- Prove `nth` returns structured absence for an out-of-range index.

Source:

```genia
nth(5, [7, 8, 9])
```

Expected:

- `stdout`: `none("index-out-of-bounds", {index: 5, length: 3})\n`
- `stderr`: ``
- `exit_code`: `0`

### `stdlib-map-option-elements`

Purpose:

- Prove list `map` passes `none(...)` list elements to callbacks instead of short-circuiting the outer call.

Source:

```genia
[none("a"), some(2), none("b")] |> map((o) -> unwrap_or(0, o))
```

Expected:

- `stdout`: `[0, 2, 0]\n`
- `stderr`: ``
- `exit_code`: `0`

### `stdlib-filter-option-elements`

Purpose:

- Prove list `filter` passes Option list elements to callbacks and can filter by Option shape.

Source:

```genia
[some(1), none("x"), some(3)] |> filter((o) -> some?(o))
```

Expected:

- `stdout`: `[some(1), some(3)]\n`
- `stderr`: ``
- `exit_code`: `0`

## 6. Required Flow Shared Specs

Later phases must add executable `category: flow` YAML specs for deterministic Flow use of the same contract helpers.

Each Flow spec must include explicit terminal materialization with `collect` or `run`.

### `flow-map-basic`

Purpose:

- Prove `map` over a Flow transforms each item and remains a Flow until collected.

Source:

```genia
stdin |> lines |> map(upper) |> collect
```

Stdin:

```text
a
b
```

Expected:

- `stdout`: `["A", "B"]\n`
- `stderr`: ``
- `exit_code`: `0`

### `flow-filter-basic`

Purpose:

- Prove `filter` over a Flow keeps matching items and remains a Flow until collected.

Source:

```genia
stdin |> lines |> filter((line) -> contains(line, "error")) |> collect
```

Stdin:

```text
ok
error one
warn
error two
```

Expected:

- `stdout`: `["error one", "error two"]\n`
- `stderr`: ``
- `exit_code`: `0`

### `flow-map-filter-chain`

Purpose:

- Prove Flow `map` and `filter` compose deterministically.

Source:

```genia
stdin |> lines |> map(trim) |> filter((line) -> line != "") |> collect
```

Stdin:

```text
  alpha

 beta
```

Expected:

- `stdout`: `["alpha", "beta"]\n`
- `stderr`: ``
- `exit_code`: `0`

## 7. Existing Specs To Preserve

Later phases must preserve existing stdlib-adjacent shared specs unless a separate approved phase changes them:

- `spec/eval/pipeline-map-sum.yaml`
- `spec/eval/map-items.yaml`
- `spec/eval/map-keys.yaml`
- `spec/eval/map-values.yaml`
- `spec/eval/map-items-map-item-key-pipeline.yaml`
- `spec/eval/map-items-map-item-value-pipeline.yaml`
- `spec/eval/first-on-flow-type-error.yaml`
- `spec/eval/reduce-on-flow-type-error.yaml`
- `spec/eval/each-on-list-type-error.yaml`
- `spec/flow/flow-keep-some-parse-int.yaml`
- `spec/flow/count-as-pipe-stage-type-error.yaml`
- `spec/cli/pipe_mode_map_parse_int.yaml`
- `spec/cli/command_mode_collect_sum.yaml`

## 8. Runner Expectations

Later TEST phase must add failing runner/discovery assertions before spec YAML files are implemented.

Required checks:

- Shared spec discovery includes all new eval spec names listed in this spec.
- Shared spec discovery includes all new flow spec names listed in this spec.
- The targeted fixture execution path compares each new case through existing `execute_spec` and `compare_spec`.
- No runner behavior change is expected unless a failing test proves the existing runner cannot load or compare the new cases.

## 9. Error Behavior

This spec does not introduce new error behavior.

Existing Flow/value boundary error specs must remain the source for misuse coverage in this issue:

- `first` given a Flow
- `reduce` given a Flow
- `each` given a list
- `count` used as a Flow stage

Any additional misuse spec must be justified from already-documented `GENIA_STATE.md` / `GENIA_RULES.md` behavior before being added in a later TEST phase.

## 10. Documentation Requirements

This spec phase does not update contract docs.

Later docs phase should:

- update shared-spec coverage descriptions only after executable specs are present and passing
- avoid claiming full stdlib conformance
- describe the new coverage as focused core stdlib shared spec coverage
- keep partial/experimental shared-spec maturity labels aligned with `GENIA_STATE.md`
- fix any stale shared-spec status wording discovered during preflight if it remains in scope for #151 recovery

## 11. Non-Goals

- No new `stdlib` shared spec category.
- No new host.
- No new generic multi-host runner.
- No new `map` / `filter` / `first` semantics.
- No broad audit of all stdlib helpers.
- No normalization of all list/map/string/option helper docs.
- No conversion of host-local tests into shared specs beyond the cases listed here.

## 12. Acceptance Criteria

Issue #151 recovery is spec-complete when:

- this spec artifact is committed with a `spec(stdlib): ... issue #151` commit
- no executable shared specs are added in the spec phase
- no tests are added or changed in the spec phase
- no runtime or docs-sync behavior is changed in the spec phase
- later phases have a precise inventory for failing tests, implementation/spec-file additions, docs sync, and audit

## 13. Final Check

- Scope is limited to already-implemented stdlib behavior.
- No new language semantics are introduced.
- Portable contract is expressed only through existing shared spec categories.
- Python implementation details do not define the contract by themselves.
- `GENIA_STATE.md` remains the final authority.

