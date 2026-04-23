# Issue #134 Spec — Flow Shared Semantic Coverage

## 1. Scope

This issue defines the first executable shared-semantic coverage for the current Flow contract in the Python reference host.

Included in this phase:

- shared executable coverage for already-implemented, already-documented Flow behavior
- only portable observable behavior
- only the current Python reference host proving that shared contract
- preferred `refine(..steps)` behavior and compatibility `rules(..fns)` behavior where they are already documented as identical
- preferred `step_*` names and compatibility `rule_*` names where their observable results are already documented as identical

Excluded from this phase:

- new Flow semantics
- broader Flow surface coverage than needed to prove the current shared contract
- implementation design, runner plumbing, schema design, or docs-sync edits
- non-Python hosts

This is partial shared-semantic coverage for Flow, not full Flow-system coverage.

## 2. Portable observable contract

The shared Flow contract to prove now is limited to these already-documented observable behaviors:

- Flow is lazy and pull-based at the observable boundary.
- Flow is single-use.
- Flow pipelines produce deterministic observable outputs for deterministic inputs.
- `stdin |> lines` is a valid lazy Flow source boundary.
- `collect` materializes Flow output into an ordinary value.
- `run` consumes a Flow to completion for effectful pipelines.
- `refine(..steps)` and `rules(..fns)` are both supported and behave identically.
- `step_*` and `rule_*` helper names are both supported and behave identically where the result is observable through Flow output.

This contract does not prove Python internals such as iterator classes, generator structure, buffering strategy, or prelude implementation layout.

## 3. Covered behaviors

Shared Flow specs should cover exactly these behaviors in this phase:

- Lazy/pull-based observable behavior.
  A case may prove laziness only through observable results such as early termination without over-reading or without emitting later upstream effects.
- Single-use behavior.
  Consuming the same Flow twice must fail with the documented single-use error.
- Deterministic Flow pipeline outputs.
  For the same deterministic source and deterministic steps, the observable result must match exactly.
- Preferred `refine(..steps)` behavior.
  A case must prove that `refine` works as the preferred public orchestration surface.
- Compatibility `rules(..fns)` behavior.
  A case must prove that `rules` remains supported and yields the same observable result as the corresponding `refine` case.
- Observable `step_*` / `rule_*` equivalence.
  At least one case must prove identical output for equivalent preferred and compatibility helper usage.
- Identity orchestration behavior.
  `rules()` and `refine()` should be covered only if the current implementation and docs support them as identity stages. Current truth documents `rules()` explicitly as identity; `refine()` should only be covered as an alias if proven through identical observable behavior, not as an independently expanded contract.

Narrowing choice:

- This phase should prove only the smallest Flow contract already called out in `GENIA_STATE.md` and `README.md`.
- Documented Flow features such as `tee`, `merge`, `zip`, `scan`, `tick`, `stdin_keys`, `keep_some`, and `keep_some_else` are not required first-wave shared coverage for this issue unless later design work can include them without broadening the contract beyond this note.

## 4. Non-goals

Out of scope for this issue:

- async Flow behavior
- multi-port Flow behavior
- cancellation
- backpressure
- scheduler behavior
- host-interrupt timing behavior
- performance guarantees
- REPL behavior
- pipe-mode CLI wrapper behavior as a Flow-category concern
- Python-host-only shell stage behavior
- `tee`, `merge`, `zip`, `scan`, `tick`, `stdin_keys`, or other broader Flow helpers
- dead-letter routing semantics beyond what is already separately documented for `keep_some_else`
- exact internal state-transition mechanics for `rules` / `refine`
- any non-Python host contract

## 5. Required shared-spec surfaces

A shared Flow spec case must be able to express, at the behavioral level:

- Genia source text for one independently executed case
- optional stdin text when the case uses `stdin |> lines`
- expected observable success result
- expected observable failure result when the case is intentionally failing

The behavioral surface should remain portable and minimal:

- success cases must assert only the observable result of Flow execution after explicit materialization or consumption
- failure cases must assert only documented user-facing failure behavior
- cases must not depend on Python object reprs, internal iterator state, or host-local implementation details

Minimal semantic needs for first-wave Flow cases:

- a way to provide deterministic source input
- a way to choose between value materialization (`collect`) and effectful consumption (`run`)
- a way to assert the final observable result or the documented failure surface

This note does not choose the final YAML schema.

## 6. Core invariants

All shared Flow cases in this phase must preserve these invariants:

- the compared contract is portable and observable
- each case executes independently
- deterministic cases must remain deterministic across repeated runs in the Python reference host
- Flow/value boundary crossings happen only through explicit helpers already documented for that purpose
- shared cases must not depend on Python-specific leakage
- preferred names must not change semantics relative to their documented compatibility aliases
- uncovered Flow behavior remains unguaranteed

## 7. Minimal initial case inventory

Priority 1:

- `stdin-lines-collect-basic`
  - purpose: prove deterministic lazy Flow source plus materialization through `collect`
  - source snippet shape: `stdin |> lines |> collect`
  - expected observable result: rendered collected list for deterministic stdin input

- `stdin-lines-take-early-stop`
  - purpose: prove observable lazy pull behavior through early termination
  - source snippet shape: `stdin |> lines |> take(2) |> collect`
  - expected observable result: only the first two items are present

- `flow-single-use-error`
  - purpose: prove the documented single-use contract
  - source snippet shape: bind one Flow, consume it once, consume it again
  - expected observable result: failure with the documented single-use error

Priority 2:

- `refine-step-emit-deterministic`
  - purpose: prove preferred `refine(..steps)` behavior
  - source snippet shape: `stdin |> lines |> refine((row, ctx) -> ... |> flat_map_some(step_emit)) |> collect`
  - expected observable result: deterministic collected value

- `rules-rule-emit-deterministic`
  - purpose: prove compatibility `rules(..fns)` behavior with the same observable result as the matching `refine` case
  - source snippet shape: `stdin |> lines |> rules((row, ctx) -> ... |> flat_map_some(rule_emit)) |> collect`
  - expected observable result: the same deterministic collected value as the corresponding `refine` case

- `step-rule-helper-equivalence`
  - purpose: prove observable equivalence of preferred and compatibility helper names
  - source snippet shape: paired cases that differ only by `step_emit` vs `rule_emit` or another equivalent helper pair
  - expected observable result: identical collected value

Priority 3:

- `rules-identity-stage`
  - purpose: prove the documented `rules()` identity behavior
  - source snippet shape: `source_flow |> rules() |> collect`
  - expected observable result: unchanged collected items

This first inventory is intentionally small. It proves the current contract without turning Flow shared specs into a broad feature matrix.

## 8. Failure / error cases

Cover now:

- single-use failure on second consumption of the same Flow
- Flow-rule contract violations only if the exact public failure shape is already documented and intentionally part of current public behavior
  - current documented candidate: `invalid-rules-result:` prefix for `rules` contract violations

Wait:

- broader runtime misuse errors not clearly frozen as shared contract
- host-specific traceback shape
- timing-sensitive failures
- pipe-mode guidance errors, except where later design work decides they belong to CLI rather than Flow
- failures for broader helpers not included in the minimal first-wave inventory

Narrowing choice:

- single-use must be covered now because it is core documented Flow behavior.
- `invalid-rules-result:` may be covered now only at the prefix level if later design keeps that assertion portable without freezing more wording than the current contract requires.

## 9. Truth alignment notes

Later steps will need to align repository truth surfaces once executable Flow shared coverage exists.

Expected later alignment points:

- `GENIA_STATE.md` should move Flow from scaffold-only shared coverage language to active executable shared coverage language, but only for the exact covered surface.
- `README.md` should stop saying Flow is public behavior without executable shared coverage if this issue lands that coverage.
- `spec/README.md` should stop describing `flow` as scaffold-only once executable Flow cases exist.
- `tools/spec_runner/README.md` should describe the Flow category only to the exact extent the runner actually executes it.
- `spec/flow/README.md` will need to stop claiming scaffold-only status once executable Flow cases are added.

Those changes belong to later implementation/docs-sync work, not this spec step.

## 10. Acceptance criteria for the later implementation step

This issue is complete only when all of the following are true:

- executable shared Flow cases exist and prove only the contract defined in this note
- the Python reference host executes those Flow cases in the shared spec runner
- first-wave shared Flow coverage includes:
  - lazy/pull-based observable behavior
  - single-use behavior
  - deterministic Flow output
  - `refine(..steps)` preferred behavior
  - `rules(..fns)` compatibility behavior
  - observable `step_*` / `rule_*` equivalence
- no new Flow semantics are introduced
- no non-Python host behavior is implied
- docs and status language are updated later to match the exact implemented shared coverage and no more

## Spec decision summary

This issue now defines shared executable proof for the smallest current Flow contract: lazy pull-based behavior at the observable boundary, single-use enforcement, deterministic outputs, and the documented `refine` / `rules` plus `step_*` / `rule_*` equivalence.

It still does not guarantee the broader Flow surface, advanced runtime behavior, non-Python hosts, or a mature full Flow shared-spec system.

The next Design step must map this exact contract into case shape, runner behavior, and comparison surfaces without changing semantics or expanding scope.
