# Issue #132 Eval Shared Contract Spec

## 1. Contract Summary

Today, shared `eval` guarantees only the observable result of independently executing a Genia source string in the Python reference host with optional stdin text.

The shared contract surface is:

- `stdout`
- `stderr`
- `exit_code`

The contract does not compare internal runtime values, Python objects, AST/IR shape, timing, or host-local implementation details.

## 2. Observable Surface

Shared eval specs compare exactly these fields:

- `stdout` as text
- `stderr` as text
- `exit_code` as integer process status

Normalization rules:

- `stdout` line endings normalize from `\r\n` and `\r` to `\n`
- `stderr` line endings normalize from `\r\n` and `\r` to `\n`
- `exit_code` is not normalized

Ignored:

- Python object identity
- internal result values not rendered to process output
- memory addresses, spans, or host-local metadata

Not ignored:

- trailing newlines
- blank lines
- whitespace other than line-ending normalization
- `stdout` vs `stderr` placement

## 3. Covered Behavior Categories

These categories are already implemented, observable through the current eval runner, and stable enough to lock with shared cases.

- Arithmetic expression result rendering.
  Safe because existing eval cases already assert successful numeric output.
- Lexical assignment and rebinding result rendering.
  Safe because existing eval cases already assert rebinding through observable output.
- Named function calls and block-body functions.
  Safe because existing eval cases already assert successful function evaluation through output.
- Higher-order function application with callable values.
  Safe because existing eval cases already assert function values passed through ordinary evaluation.
- Recursive evaluation with deterministic numeric output.
  Safe because existing eval cases already assert stable recursion output.
- Pattern matching on lists, including rest capture.
  Safe because existing eval cases already assert successful list-pattern result output.
- Duplicate-binding pattern equality on the success path.
  Safe because an eval case already locks the true-match path, and runtime tests cover the false path.
- Pipeline evaluation producing a final plain value.
  Safe because an eval case already locks a simple `map |> sum` value result.
- Stdin-fed evaluation with existing flow helpers when the final observable result is a plain value.
  Safe because an eval case already locks command-mode stdin input and final stdout output.
- Error rendering for deterministic failing programs.
  Safe because existing eval cases already lock stderr-only failure output plus exit status for undefined-name and bad-rest-pattern errors.

## 4. Explicit Non-Goals

This issue does not add shared eval coverage for:

- parse-only behavior
- CLI argument parsing or mode-selection behavior
- pipe-mode wrapper behavior
- REPL behavior
- IR shape or lowering behavior
- flow semantics as their own shared category
- Python-host-only capability surfaces
- behaviors that are implemented but not yet stable enough to freeze by exact stderr text

## 5. Gap Analysis

Existing behavior that appears implemented and testable, but is not yet covered by shared `spec/eval/*`, includes:

- explicit stdout side effects such as `print(...)`
- explicit stderr side effects such as `log(...)`
- programs that write to both stdout and stderr in one run
- duplicate-binding pattern equality false-path cases
- additional deterministic pattern-failure/error cases beyond the current bad-rest-pattern case
- additional stdin-fed eval success cases that prove current normalization without depending on CLI-only concerns

These are coverage gaps only if added as exact `stdout`/`stderr`/`exit_code` assertions for behavior already proved elsewhere by current runtime tests.

## 6. Spec Case Shapes

Current eval YAML shape:

- required top-level fields: `name`, `category`, `input`, `expected`
- optional top-level field: `notes`
- `name` must be a non-empty string and must match the file stem
- `category` must be `eval`
- `input.source` is required and must be a string
- `input.stdin` is optional and, when present, must be a string
- `expected.stdout` is required and must be a string
- `expected.stderr` is required and must be a string
- `expected.exit_code` is required and must be an integer

Unknown top-level, input, or expected fields are invalid.

## 7. Invariants

The following must remain true for shared eval:

- each case executes independently
- the compared surface is only `stdout`, `stderr`, and `exit_code`
- `stdout` and `stderr` are compared after line-ending normalization only
- success requires exact field equality after that normalization
- failure cases must preserve `stdout`/`stderr` separation
- deterministic cases must not vary across repeated runs in the same host environment

## 8. Failure Modes

A shared eval case fails when:

- the spec file shape is invalid
- execution crashes before producing comparable eval output
- normalized `stdout` differs from expected
- normalized `stderr` differs from expected
- `exit_code` differs from expected

Acceptable variation is limited to line-ending normalization in `stdout` and `stderr`. No other whitespace, text, or channel movement is acceptable variation.

## 9. Risk Notes

- Exact stderr locking can freeze current error wording, including wording that may later need cleanup.
- The shared eval runner executes through the Python reference host command-source path, so behavior that is really CLI-specific should not be widened here accidentally.
- Broadening eval coverage too far can hide the boundary between eval, CLI, and flow shared categories.
- Docs can drift if higher-level summaries claim broader eval guarantees than the current executable comparison surface.
