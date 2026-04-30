# Issue #186 Flow-Adjacent Prelude Extraction Design

## Purpose

Design the no-behavior-change extraction for Flow-adjacent helpers covered by issue #186.

This design follows the contract added in `GENIA_STATE.md`: pure helpers that operate on ordinary Genia values may live in prelude, while Flow creation, consumption, pull-loop mechanics, cleanup, and host execution stay in the Python Flow kernel and host adapters.

## Scope Lock

Included:

- Pure rule/refine result constructors.
- Stage composition wrappers already implemented in prelude.
- Rule/refine result defaulting and value-shape validation already implemented in prelude.
- Autoload registration changes needed to make the public helper family match the Flow prelude boundary.

Excluded:

- Core Flow execution loop.
- Host pull loop and early-close/resource cleanup.
- Scheduling, concurrency, async behavior, multi-port stages, or backpressure.
- New Flow semantics, new syntax, new implicit Flow/Value conversion, or changed diagnostics.

## Architecture Overview

Current Flow architecture has two layers:

- `src/genia/std/prelude/flow.genia` owns public Flow helper wrappers plus pure `rules` / `refine` orchestration, dispatch, defaulting, and most contract validation.
- `src/genia/interpreter.py` owns host-backed Flow primitives exposed to prelude as underscored functions such as `_lines`, `_scan`, `_rules_kernel`, `_collect`, and `_run`.

The remaining misplaced pure Flow-adjacent helpers are the rule/refine result constructors currently in `src/genia/std/prelude/fn.genia`:

- `rule_skip`, `rule_emit`, `rule_emit_many`, `rule_set`, `rule_ctx`, `rule_halt`, `rule_step`
- `step_skip`, `step_emit`, `step_emit_many`, `step_set`, `step_ctx`, `step_halt`, `step_step`

These helpers only construct ordinary `none` / `some(map)` Genia values. They do not create, consume, or schedule Flow values. They should live next to `rules` / `refine` in `flow.genia`.

## File / Module Changes

## New Files

- None.

## Modified Files

- `src/genia/std/prelude/flow.genia`
  - Add the public `rule_*` constructors.
  - Add the public `step_*` preferred aliases.
  - Keep `rules` / `refine` orchestration and validation in this file.

- `src/genia/std/prelude/fn.genia`
  - Remove the moved `rule_*` and `step_*` definitions from the generic function-helper module.
  - Leave generic helpers such as `apply`, `compose`, `inspect`, `trace`, and `tap` in place.

- `src/genia/interpreter.py`
  - Update autoload registrations for `rule_*` and `step_*` names from `std/prelude/fn.genia` to `std/prelude/flow.genia`.
  - Do not change host Flow primitive implementations.

## Removed Files

- None.

## Data Shapes

No data shapes change.

Existing rule/refine result values remain:

- Skip/no effect: `none`
- Emit one value: `some({ emit: [value] })`
- Emit many values: `some({ emit: values })`
- Replace record: `some({ record: record })`
- Replace ctx: `some({ ctx: ctx })`
- Halt current input item: `some({ halt: true })`
- Combined step: `some({ record: record, ctx: ctx, emit: out })`

Existing `rules` / `refine` result map fields remain:

- `emit`: list, default `[]`
- `record`: ordinary value, default current record
- `ctx`: ordinary value, default current ctx
- `halt`: boolean, default `false`

## Function / Interface Design

Public helper names and arities stay unchanged:

- `rule_skip() -> none`
- `rule_emit(x) -> some({ emit: [x] })`
- `rule_emit_many(xs) -> some({ emit: xs })`
- `rule_set(record) -> some({ record: record })`
- `rule_ctx(ctx) -> some({ ctx: ctx })`
- `rule_halt() -> some({ halt: true })`
- `rule_step(record, ctx, out) -> some({ record: record, ctx: ctx, emit: out })`
- `step_skip() -> rule_skip()`
- `step_emit(x) -> rule_emit(x)`
- `step_emit_many(xs) -> rule_emit_many(xs)`
- `step_set(record) -> rule_set(record)`
- `step_ctx(ctx) -> rule_ctx(ctx)`
- `step_halt() -> rule_halt()`
- `step_step(record, ctx, out) -> rule_step(record, ctx, out)`

Existing Flow helper interfaces stay unchanged:

- `rules(..fns)`
- `refine(..steps)`
- `rules(..., flow)` / `flow |> rules(...)`
- `refine(..., flow)` / `flow |> refine(...)`

## Control Flow

Autoload flow after implementation:

1. A program references `rule_emit`, `step_emit`, `rules`, or `refine`.
2. The environment autoloads `std/prelude/flow.genia`.
3. `flow.genia` defines the public Flow helper family.
4. Rule/refine helper constructors return ordinary Genia values.
5. `rules` / `refine` orchestration consumes those ordinary values and passes the final pure step function to `_rules_kernel`.
6. `_rules_kernel` remains the host-backed Flow-producing primitive that iterates the upstream Flow and preserves ctx across items.

No Flow value is created or consumed by the moved constructors.

## Error Handling Design

Error behavior must not change.

- `invalid-rules-result:` diagnostics remain produced through the current prelude validation path and `_rules_error`.
- Host primitive type checks for actual Flow values remain host-side.
- Callable validation for actual stage invocation remains governed by existing runtime callable behavior and host primitive boundaries.
- Pipeline stage error wrapping remains in `Evaluator.eval_pipeline`.

The relocation must not change exact user-facing error text asserted by current tests/specs.

## Integration Points

- `flow.genia` becomes the single public prelude home for Flow orchestration helpers and rule/refine result constructors.
- `fn.genia` remains the home for generic function/pipeline debugging helpers.
- `interpreter.py` only changes autoload paths for the moved public names.
- `hosts/python/exec_flow.py`, `hosts/python/adapter.py`, and shared spec execution stay unchanged.
- CLI pipe mode remains `stdin |> lines |> <stage_expr> |> run`.

## Test Design Input

The test phase should add or adjust tests before implementation to fail on the current placement/autoload plan.

Coverage should prove:

- `rule_*` helpers still produce the same values.
- `step_*` helpers remain exact aliases for `rule_*`.
- `rules` and `refine` still accept the helper results.
- `rules()` remains the identity stage.
- Invalid result diagnostics still include `invalid-rules-result:`.
- Higher-order/autoload use still works when `rule_emit` or `step_emit` is referenced before `rules` / `refine`.
- No host Flow behavior changed: single-use, early termination, and collect/run boundaries stay covered by existing tests.

Likely test locations:

- `tests/unit/test_fn_stdlib.py`
- `tests/unit/test_flow_phase1.py`
- `tests/unit/test_stdlib_prelude_basics.py`
- `spec/flow/step-rule-helper-equivalence.yaml`
- `spec/flow/refine-step-emit-deterministic.yaml`
- `spec/flow/rules-rule-emit-deterministic.yaml`

## Doc Impact

Later docs phase should sync:

- `GENIA_STATE.md`, if implementation changes the stated module home for rule/step helpers.
- `GENIA_REPL_README.md`, where rule helpers are listed.
- `README.md`, where `refine` / `step_*` and `rules` / `rule_*` are described.
- Cheatsheets only if they list helper module homes or public helper inventory.

No docs are changed in this design phase beyond this design artifact.

## Constraints

Must:

- Preserve all public names, arities, return shapes, and diagnostics.
- Keep the host Flow kernel responsible for Flow mechanics.
- Keep relocation small and reversible.
- Avoid adding new abstraction layers.

Must not:

- Change `rules` / `refine` semantics.
- Move `_rules_kernel`, `_scan`, `_keep_some_else`, `_collect`, `_run`, or other Flow primitives into prelude.
- Introduce implicit Flow/Value conversion.
- Redefine Flow behavior inside host adapters.

## Complexity Check

[x] Minimal
[x] Necessary
[ ] Over-engineered

Explanation:

The design moves only pure constructors into the Flow prelude and updates autoload metadata. The rest of the Flow architecture remains as-is.

## Final Check

- Matches the contract exactly.
- Introduces no new behavior.
- Keeps Core IR and host boundaries intact.
- Ready for test phase.
