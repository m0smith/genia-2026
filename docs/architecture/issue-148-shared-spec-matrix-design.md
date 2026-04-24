# Issue #148 Design — Expand Pipeline, CLI, And Flow Shared Spec Matrix

## 1. Design summary

- Keep the current shared-spec architecture: flat YAML files under existing active category directories, one case per file, no schema changes.
- Expand coverage by adding a small set of new shared cases across `eval` and `cli`; do not move CLI wrapper behavior into `flow`.
- Keep the current category split:
  - ordinary pipeline semantics stay in `eval`
  - file / command / pipe mode behavior stays in `cli`
  - direct Flow command-source behavior stays in `flow`
- Reuse the current CLI runner model exactly:
  - file mode: `input.file`
  - command mode: `input.command` with empty `input.stdin`
  - pipe mode: `input.command` with non-empty `input.stdin` and empty `input.argv`
- Do not redesign runner comparison behavior, loader shape, or subprocess execution paths.
- Use mirrored shared cases, not paired-runner logic, to prove mode differences such as `-c` success vs `-p` failure.

## 2. Current constraints that the design must preserve

### Shared-spec schema

- No new top-level fields.
- No new CLI `mode` field.
- No category-specific comparison extensions.
- Existing compared surfaces remain:
  - eval: `stdout`, `stderr`, `exit_code`
  - cli: `stdout`, `stderr`, `exit_code`
  - flow: `stdout`, `stderr`, `exit_code`

### CLI loader / adapter behavior

- CLI file mode is selected by `input.file`.
- CLI command mode is selected by `input.command` plus empty `input.stdin`.
- CLI pipe mode is selected by `input.command` plus non-empty `input.stdin`.
- Current CLI shared specs require `input.argv: []` in pipe mode.
- Pipe-mode shared proofs therefore must include actual stdin text, even when the main contract point is diagnostic behavior.

### Category boundary

- `spec/flow/` proves direct Flow observable behavior through command-source execution only.
- `spec/cli/` proves CLI wrapper behavior, including `-p`.
- Do not add CLI-wrapper cases to `spec/flow/`.
- Do not add file/command/pipe-mode dispatch proofs to `spec/eval/`.

## 3. Coverage expansion plan

### `eval`: small ordinary pipeline proof

Purpose:

- prove one minimal already-documented `|>` call-shape behavior without involving CLI dispatch or Flow wrappers

Why `eval`:

- the behavior is ordinary source evaluation, not mode selection
- the existing eval runner surface already compares the right observable output

Recommended case:

- `pipeline-call-shape-basic`
  - source shape:
    - define a tiny helper such as `inc(x) = x + 1`
    - evaluate `1 |> inc`
  - expected observable result:
    - deterministic final rendered value through normal eval output

What not to add here:

- file-mode execution
- `-c` / `-p` dispatch
- pipe-mode diagnostics
- direct Flow contract cases

### `cli`: file mode

Purpose:

- strengthen shared proof that file mode is an execution path distinct from `-c` and `-p`
- prove already-documented `main(argv())` behavior only if kept within the current deterministic contract

Recommended additions:

- `file_mode_main_argv`
  - source file returns or prints `argv()` via `main(args) = args`
  - proves file-mode `main/1` dispatch through the shared suite
- optionally `file_mode_main_zero_arity`
  - only if the design step wants explicit proof for `main()` fallback when `main/1` does not exist
  - keep out if one file-mode `main` case is enough for this issue’s minimal matrix

File fixture strategy:

- add one or two tiny `.genia` helper files under `spec/cli/`
- keep them single-purpose
- do not modify existing file-mode fixtures unless necessary

### `cli`: command mode

Purpose:

- strengthen shared proof that `-c` is ordinary program evaluation, not pipe-mode wrapping
- prove a final value can succeed in command mode where the same shape would fail in pipe mode

Recommended additions:

- `command_mode_pipeline_value`
  - simple inline pipeline to final value, for example `inc` or `collect |> sum`
  - proves ordinary command-mode program semantics
- `command_mode_collect_sum`
  - stdin-fed or inline value pipeline that ends in a final reduced/materialized value
  - useful as the success half of a `-c` vs `-p` paired contract proof

What to preserve:

- trailing `argv()` behavior already has shared coverage
- command mode should continue to use empty `stdin` when proving pure inline execution
- if a command-mode case uses stdin text, keep it in ordinary command-source program shape, not pipe-mode wrapper shape

### `cli`: pipe mode

Purpose:

- expand shared proof that `-p` remains a Flow-stage wrapper rather than a generic command-evaluation mode
- bring key documented pipe-mode guidance into the executable shared suite where wording is already stable

Recommended additions:

- `pipe_mode_map_parse_int`
  - stdin lines piped through `map(parse_int)` and an effectful terminal stage such as `each(print)`
  - proves the valid per-item pattern in `-p`
- `pipe_mode_bare_parse_int_error`
  - same general input family as the success case above, but bare `parse_int`
  - proves the documented “Flow stage vs per-item function” distinction
- `pipe_mode_sum_error`
  - bare reducer in `-p`
  - proves current reducer guidance
- `pipe_mode_collect_error`
  - final non-Flow result in `-p`
  - proves current `-c/--command` guidance for non-Flow final values

Already-covered cases that remain:

- `pipe_mode_basic`
- `pipe_mode_argv_empty`
- `pipe_mode_bypass_main`
- explicit unbound `stdin` rejection
- explicit unbound `run` rejection

Design rule for pipe-mode additions:

- all new pipe-mode YAML should keep:
  - `input.command` set
  - non-empty `input.stdin`
  - `input.argv: []`
- all expected failures must stay within documented stable user-facing wording

## 4. Mirrored proof strategy for mode differences

Use separate one-case-one-file assertions instead of any runner feature that compares two cases directly.

### Final value allowed in `-c`, rejected in `-p`

Recommended mirrored pair:

- command-mode success case:
  - `command_mode_collect_sum`
- pipe-mode failure case:
  - `pipe_mode_sum_error` or `pipe_mode_collect_error`

Why this pairing works:

- it proves the mode distinction through observable results
- it avoids runner complexity
- failure reporting stays local to each YAML file

### Per-item function allowed when wrapped, rejected when bare

Recommended mirrored pair:

- pipe-mode success case:
  - `pipe_mode_map_parse_int`
- pipe-mode failure case:
  - `pipe_mode_bare_parse_int_error`

Why this pairing works:

- it proves the current mental model for `-p`
- it makes the valid/invalid distinction explicit without changing semantics

## 5. File and directory plan

Add:

- `docs/architecture/issue-148-shared-spec-matrix-design.md`
- `spec/eval/pipeline-call-shape-basic.yaml`
- `spec/cli/file_mode_main_argv.yaml`
- `spec/cli/file_mode_main_argv.genia`
- `spec/cli/command_mode_collect_sum.yaml`
- `spec/cli/pipe_mode_map_parse_int.yaml`
- `spec/cli/pipe_mode_bare_parse_int_error.yaml`
- `spec/cli/pipe_mode_sum_error.yaml`
- `spec/cli/pipe_mode_collect_error.yaml`

Modify:

- `tests/test_spec_ir_runner_blackbox.py`
- `tests/test_cli_shared_spec_runner.py`

Maybe modify only if needed after implementation confirms current wording is stable:

- `spec/cli/README.md`
- `spec/README.md`
- `tools/spec_runner/README.md`
- `GENIA_STATE.md`
- `GENIA_REPL_README.md`
- `README.md`

No directory changes:

- keep `spec/eval/`, `spec/cli/`, and `spec/flow/` flat
- do not add subdirectories
- do not rename existing cases

## 6. Shared vs local test boundary

### Shared-contract additions

- one minimal ordinary pipeline call-shape proof in `eval`
- file-mode `main(argv())` dispatch proof
- command-mode final-value success proof
- pipe-mode valid per-item Flow-stage proof
- pipe-mode documented invalid bare per-item stage proof
- pipe-mode documented invalid bare reducer proof
- pipe-mode documented invalid non-Flow final result proof

### Keep local-only

- REPL behavior
- every malformed CLI invocation
- debugger runtime behavior beyond current deterministic argument validation
- broken-pipe runtime details
- sink object behavior
- internal wrapper construction details
- any unstable or overly rich diagnostic text not already clearly frozen in authority docs

## 7. Runner and test impact

Expected runner impact:

- none

Expected loader impact:

- none

Expected host-adapter impact:

- none if the new cases fit current behavior

Expected test impact:

- extend `tests/test_spec_ir_runner_blackbox.py` fixture lists for the new eval and cli case filenames
- extend `tests/test_cli_shared_spec_runner.py` discovery assertions and, if needed, add one or two fixture-execution assertions for the new CLI cases

Important constraint:

- if implementation discovers that the current runner or loader cannot express one of the designed cases without schema change, stop and re-evaluate rather than silently expanding the shared-spec format

## 8. YAML case-shape guidance

### `eval` case

Use the existing eval shape unchanged:

- `name`
- `category: eval`
- `input.source`
- optional `input.stdin`
- `expected.stdout`
- `expected.stderr`
- `expected.exit_code`

### `cli` cases

Use the existing CLI shape unchanged:

- `name`
- `category: cli`
- `input.source`
- `input.file` or `input.command`
- `input.stdin`
- `input.argv`
- `input.debug_stdio`
- `expected.stdout`
- `expected.stderr`
- `expected.exit_code`

CLI mode selection guidance:

- file mode:
  - `file` set
  - `command: null`
  - `stdin: ""`
- command mode:
  - `command` set
  - `file: null`
  - `stdin: ""`
- pipe mode:
  - `command` set
  - `file: null`
  - non-empty `stdin`
  - `argv: []`

## 9. Risk analysis

- Overclaiming pipe-mode coverage.
  Mitigation: add only the few documented guidance cases named above.
- Blurring Flow and CLI categories.
  Mitigation: keep all `-p` wrapper behavior in `spec/cli/`.
- Freezing unstable diagnostics.
  Mitigation: only promote wording already reflected in `GENIA_STATE.md`, `GENIA_REPL_README.md`, and `README.md`.
- Schema creep.
  Mitigation: no new fields, no new matcher types, no paired-case runner logic.
- Broad implementation drift.
  Mitigation: keep the added case set small and use mirrored success/failure cases instead of a large matrix.

## 10. Implementation handoff

Touch in the next phase:

- `spec/eval/pipeline-call-shape-basic.yaml`
- `spec/cli/file_mode_main_argv.genia`
- `spec/cli/file_mode_main_argv.yaml`
- `spec/cli/command_mode_collect_sum.yaml`
- `spec/cli/pipe_mode_map_parse_int.yaml`
- `spec/cli/pipe_mode_bare_parse_int_error.yaml`
- `spec/cli/pipe_mode_sum_error.yaml`
- `spec/cli/pipe_mode_collect_error.yaml`
- `tests/test_cli_shared_spec_runner.py`
- `tests/test_spec_ir_runner_blackbox.py`

Only if needed after the executable cases are proven:

- `spec/cli/README.md`
- `spec/README.md`
- `tools/spec_runner/README.md`
- `GENIA_STATE.md`
- `GENIA_REPL_README.md`
- `README.md`

Make:

- add the minimal new YAML cases listed above
- add one tiny file-mode helper program
- extend explicit shared-fixture tests

Avoid:

- changing runner behavior
- changing loader behavior
- changing CLI semantics
- moving CLI wrapper behavior into Flow specs
- broadening docs beyond the exact landed case inventory

Validate in later phases:

- targeted shared-spec runner tests
- targeted black-box fixture tests
- full shared spec suite
- only the doc-sync checks touched by later wording updates
