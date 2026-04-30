# Issue 202 Design: Internal `ExecutionMode` CLI Refactor

## 1. Purpose

Translate the no-behavior-change contract into a minimal internal structure for CLI execution mode selection.

This design is about organization only. It does not define new language behavior, new CLI flags, new user-facing modes, new lifecycle semantics, or new output/error behavior.

## 2. Scope Lock

Must follow:

- [Issue 202 contract](issue-202-execution-mode-cli-contract.md)
- `GENIA_STATE.md` CLI behavior
- `AGENTS.md` phase discipline
- current `-c`, `-p`, file, REPL, and `--debug-stdio` behavior

Must not:

- change CLI argument parsing semantics
- change `stdout`, `stderr`, or exit codes
- change pipe wrapping
- change `argv()` exposure
- change file/command `main/1` then `main/0` dispatch
- add rows/awk mode, lifecycle hooks, annotation behavior, module behavior, or public API

## 3. Architecture Overview

Current CLI execution is concentrated in `src/genia/interpreter.py::_main`.

The design keeps that ownership boundary. `_main` remains the public entrypoint for command-line execution, while a private `ExecutionMode` shape captures the already-selected mode after argparse has produced:

- command source, if `-c` / `--command` was used
- pipe stage expression, if `-p` / `--pipe` was used
- program path and script args, if file mode was selected
- empty execution input, if REPL fallback was selected
- debug-stdio request, if `--debug-stdio` was selected

Data flow remains:

1. `_main` receives raw argv.
2. argparse parses existing flags and remaining args.
3. existing validation rejects invalid combinations.
4. private mode selection creates an internal `ExecutionMode`.
5. execution dispatch runs the same existing code path for that mode.
6. observable result remains the same return code plus current stdout/stderr effects.

No parser, evaluator, IR, Flow, stdlib, host adapter, or REPL semantics move into this abstraction.

## 4. File / Module Changes

New files:

- none expected for implementation

Modified files:

- `src/genia/interpreter.py`
  - add the private mode data shape near CLI helpers
  - split mode selection from mode execution inside the existing CLI area
  - keep `_main` as the callable entrypoint

Future test phase files:

- `tests/unit/test_cli_args.py`
- `tests/unit/test_cli_pipe_mode.py`
- `tests/spec/test_cli_shared_spec_runner.py`
- `spec/cli/*.yaml`, if a shared regression case is needed

Future docs phase files:

- likely no user-facing docs required
- if needed, a short internal/no-behavior-change note only

Removed files:

- none

## 5. Data Shapes

Private mode kind values:

- `file`
- `command`
- `pipe`
- `repl`
- `debug_stdio`

Private `ExecutionMode` structure:

- `kind`: one of the private mode kind values
- `source`: inline command source or pipe stage expression, where applicable
- `program_path`: file/debug program path, where applicable
- `script_args`: argv values exposed through `argv()` for file, command, and pipe modes

Design constraints:

- `ExecutionMode` is internal to the Python reference CLI implementation.
- It is not a Genia value shape.
- It is not Core IR.
- It is not a public host adapter contract.
- It must not introduce a registry or generic plugin/mode framework.

## 6. Function / Interface Design

Private helper: `_select_execution_mode(args, remaining_args, explicit_terminator_used, terminator_index, parser) -> ExecutionMode`

Responsibility:

- preserve the existing option-like path validation
- derive `program_path` and `script_args`
- validate `--debug-stdio` combinations exactly as today
- return the selected private `ExecutionMode`

Private helper: `_run_execution_mode(mode: ExecutionMode) -> int`

Responsibility:

- dispatch to the existing file, command, pipe, REPL, or debug-stdio path
- preserve current exception handling and result emission
- return the same integer exit code as `_main` returns today

Private helper: `_resolve_program_result(run_result, env) -> Any`

Responsibility:

- preserve existing file/command `main/1` then `main/0` dispatch
- remain shared only by file and command execution
- stay out of pipe and REPL execution

Existing public/internal entrypoints retained:

- `_main(argv: Optional[list[str]] = None) -> int`
- `run_debug_stdio(...) -> int`
- `repl() -> None`
- `run_source(...) -> Any`

## 7. Control Flow

`_main` should remain the top-level CLI orchestration point:

1. copy raw argv
2. find `--` terminator exactly as today
3. configure argparse exactly as today
4. parse args exactly as today
5. handle `--version` exactly as today
6. normalize leading `--` in `remaining_args` exactly as today
7. call mode selection
8. call mode execution

Mode execution design:

- `debug_stdio`: call `run_debug_stdio(program_path)`
- `pipe`: create env with `cli_args`, wrap the pipe expression, call `run_source(..., filename="<pipe>")`, return 0 or current pipe error code
- `command`: create env with `cli_args`, call `run_source(..., filename="<command>")`, apply main dispatch, emit final result when currently emitted
- `file`: create env with `cli_args`, read file, call `run_source(..., filename=resolved_path)`, apply main dispatch, emit final result when currently emitted
- `repl`: call `repl()` and return 0

The mode abstraction must only reorder code into named boundaries. It must not reorder observable validation or execution effects.

## 8. Error Handling Design

Argument validation errors remain argparse `parser.error(...)` failures with code 2 and current message text.

Pipe mode keeps its separate error path:

- `GeniaQuietBrokenPipe` returns 0
- other exceptions emit `Error: {_format_pipe_mode_error(e)}`
- return code remains 1

Command and file mode keep their shared error shape:

- `GeniaQuietBrokenPipe` returns 0
- other exceptions emit `Error: {e}`
- return code remains 1

Debug-stdio validation remains before calling `run_debug_stdio`.

No error should be normalized into a different exception category, `none(...)`, success value, or altered string.

## 9. Integration Points

Interpreter:

- `make_global_env(cli_args=...)` remains the boundary for `argv()`.
- `run_source(...)` remains the evaluator entrypoint.
- `_emit_result(...)` and `_emit_error(...)` remain the stdout/stderr boundary.
- `_wrap_pipe_mode_expr(...)` remains the only pipe expression wrapper.

REPL:

- REPL fallback remains direct and does not use `main`.

Debug adapter:

- `run_debug_stdio(...)` remains unchanged.
- `ExecutionMode` only selects the existing debug path after existing validation.

Host/shared specs:

- `hosts/python/exec_cli.py` should not need behavior changes.
- Shared CLI specs remain the conformance surface for stdout/stderr/exit_code.

## 10. Test Design Input

The future test phase should create failing or regression tests before implementation. The design points to exact equivalence coverage rather than new behavior.

Regression areas:

- command mode stdout/stderr/exit_code
- command mode trailing `argv()`, including option-like trailing args after `--`
- pipe mode stdout/stderr/exit_code
- pipe mode bypasses `main`
- pipe mode explicit `stdin` / `run` diagnostics
- pipe mode guidance for per-item functions, reducers, and final values
- file mode stdout/stderr/exit_code
- file mode `main(argv())`
- file mode option-like path validation
- REPL fallback remains selected only when no file/command/pipe/debug mode applies
- debug-stdio validation messages and code 2
- broken-pipe quiet return behavior

Potential test locations:

- shared CLI specs for portable observable cases
- unit CLI tests for argparse, debug-stdio validation, broken-pipe, and REPL selection
- existing subprocess adapter tests for exact argv construction where relevant

## 11. Doc Impact

No user-facing documentation should claim a new feature.

`GENIA_STATE.md` should not gain new behavior semantics for this refactor. The existing CLI contract already covers file, command, pipe, and REPL modes.

Docs phase may add or update only an internal/no-behavior-change note if needed. It must not claim:

- new CLI modes
- lifecycle support
- rows/awk mode
- annotation changes
- module system changes
- public `ExecutionMode` API

## 12. Constraints

Must:

- keep the abstraction private and small
- keep mode selection explicit and readable
- reuse existing helper functions and error paths
- keep behavior pinned to `GENIA_STATE.md` and existing specs

Must not:

- introduce a generalized command registry
- introduce polymorphic lifecycle hooks
- hide behavior in clever dynamic dispatch
- change mode priority
- move language semantics into the Python host abstraction

## 13. Complexity Check

Minimal: yes.

Necessary: yes.

Overly complex: no, if implementation uses a small private data shape and one dispatch helper.

Too broad if:

- it adds a public API
- it anticipates future modes with unused extension points
- it changes parser setup
- it changes behavior while reducing duplication

## 14. Ready For Test Phase

This design maps the contract to one implementation module, existing CLI tests/specs, and no new user-visible behavior.

Ready for the test phase.
