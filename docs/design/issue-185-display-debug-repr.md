# Issue #185 Design: Representation Entry Points

## Status

Design phase artifact for issue #185.

Distillation classification required later: EXTRACT or DELETE after audit/distillation. `GENIA_STATE.md` remains the authority for behavior.

## Purpose

Implement the approved contract for `display(value)` and `debug_repr(value)` as the first concrete public entry points of the planned Representation System (#166).

This design maps the contract to the current Python reference host structure without designing the broader Representation System.

## Scope Lock

Included:

- expose `display(value)` as a public runtime function that returns the display representation string
- expose `debug_repr(value)` as a public runtime function that returns the debug representation string
- reuse the current representation behavior already used by output sinks and final/debug result display
- preserve existing `print`, `log`, `write`, `writeln`, REPL, CLI final-result, and pipeline behavior
- add focused tests and docs in later phases

Excluded:

- full Representation System design
- strategy or registry mechanisms
- user-defined representations
- representation namespaces/modules
- new syntax
- repo-wide rename
- alternate public naming experiments

## Architecture Overview

The current runtime already has two formatter entry points in `src/genia/utf8.py`:

- `format_display(value) -> str`
- `format_debug(value) -> str`

The #185 implementation should expose these through public Genia callable values registered in the root runtime environment.

Data flow:

1. Genia source calls `display(value)` or `debug_repr(value)`.
2. Ordinary call evaluation resolves the name from the global environment.
3. The host-backed callable receives the evaluated value.
4. The callable returns a Genia string containing the selected representation.
5. Any printing of that returned string is controlled by existing output operations or final-result rendering.

## File / Module Changes

New files:

- none expected for implementation
- test phase may add shared spec YAML cases under `spec/eval/`

Modified files:

- `src/genia/interpreter.py`
  - add root environment callables for `display` and `debug_repr`
  - register them in `make_global_env`
  - keep them pure return-value helpers, with no sink access
- `spec/eval/*.yaml`
  - add user-visible shared eval cases
- `tests/unit/*.py`
  - add or extend focused runtime tests for returned strings and absence of output side effects
- `GENIA_REPL_README.md`
  - document the implemented public surface after implementation
- `README.md`
  - include the public surface after implementation
- `docs/cheatsheet/core.md`
  - add quick-reference mention only after implementation
- `docs/contract/semantic_facts.json`
  - update only if docs add protected wording that semantic sync must guard

Removed files:

- none in design/test/implementation

## Data Shapes

No new runtime value family is introduced.

Inputs:

- any ordinary Genia runtime value accepted by the existing representation formatter

Outputs:

- a Genia string

Representative result strings:

- `display("hello")` returns `hello`
- `debug_repr("hello")` returns `"hello"`
- `display(true)` returns `true`
- `debug_repr(false)` returns `false`
- `display(none("missing-key", {key: "name"}))` returns `none("missing-key", {key: "name"})`
- `debug_repr([some("x"), false])` returns `[some("x"), false]`

Runtime capability values and function-like values retain host-specific opaque text in this phase.

## Function / Interface Design

Public Genia functions:

- `display(value)`
  - parameters: one evaluated value
  - returns: string
  - behavior: returns the user-facing display representation
- `debug_repr(value)`
  - parameters: one evaluated value
  - returns: string
  - behavior: returns the debug representation

Implementation-facing helper use:

- `display(value)` delegates to the existing display formatter.
- `debug_repr(value)` delegates to the existing debug formatter.

No new callable protocol, value type, module, namespace, or parser form is needed.

## Control Flow

Normal evaluation path:

1. Evaluate the argument expression.
2. Invoke the resolved runtime callable.
3. Format the already-evaluated value.
4. Return the resulting string.

There is no special evaluation rule, no lazy behavior, no pattern matching behavior, and no pipeline-specific path.

## Error Handling Design

Wrong arity:

- use the ordinary callable arity/type-error path already used for host-backed callables

Formatter failures:

- no new failure category is defined
- any unexpected formatter failure propagates through the existing runtime error path

Side effects:

- these functions must not write to `stdout` or `stderr`
- they must not mutate runtime state

## Integration Points

Runtime/interpreter:

- register the two callables in `make_global_env`
- keep `print`, `log`, `_write`, `_writeln`, `_emit_result`, REPL output, and CLI paths unchanged

CLI and eval specs:

- shared eval specs should observe behavior through `stdout`, `stderr`, and `exit_code`
- because final-result rendering debug-formats returned strings, specs that need raw representation text should use `print(display(...))` or `print(debug_repr(...))`

REPL:

- no REPL-specific behavior changes

Flow:

- no Flow-specific behavior changes
- these functions may be used as ordinary value functions in pipelines according to existing call and pipeline rules

## Test Design Input

Shared eval spec cases:

- `display` for string, number, boolean, `none`, `some`, list, and map
- `debug_repr` for string escaping and structured values
- output side-effect distinction using `print(display(...))`

Python unit tests:

- direct return value from `run_source('display("x")')`
- direct return value from `run_source('debug_repr("x")')`
- no stdout/stderr output from bare calls
- existing `print`, `log`, `write`, `writeln` tests continue unchanged
- wrong arity follows ordinary callable failure behavior

Docs/semantic sync tests:

- run existing semantic doc sync if docs wording touches protected facts
- add protected facts only if later docs need cross-doc enforcement

## Doc Impact

Already updated in contract phase:

- `GENIA_STATE.md`
- `GENIA_RULES.md`

Later docs phase:

- `GENIA_REPL_README.md`
- `README.md`
- `docs/cheatsheet/core.md`

No `docs/book/*` files exist in the current repository.

## Constraints

Must:

- follow existing formatter behavior
- remain minimal
- preserve output operation semantics
- keep #166 as owner of the broader representation model
- use only `display` and `debug_repr` as public names for #185

Must not:

- add new syntax
- add a representation registry
- add user-defined representation hooks
- add namespaces/modules for representation
- add alternate public names
- change final-result rendering
- change output sink behavior

## Complexity Check

Minimal: yes.

Necessary: yes, because the contract exposes existing representation behavior through two public entry points.

Over-engineered: no, as long as implementation only registers two runtime callables over existing formatter functions.

## Final Check

- Matches the approved #185 contract.
- Does not design the full Representation System.
- Reserves broader naming/model decisions for #166.
- Does not introduce competing public terminology.
- Ready for failing-test phase.
