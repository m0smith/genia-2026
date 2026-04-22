# Issue #132 Eval Shared Contract Design

## 1. Design Summary

- Keep the existing shared eval design: flat YAML files under `spec/eval/`, one case per file, no schema changes, no runner behavior changes.
- Expand coverage by adding a small set of new eval cases for already-proved observable behavior: stdout-only output, stderr-only output, mixed stdout/stderr separation, and duplicate-binding false-path output.
- Keep current arithmetic/function/pattern/pipeline/stdin/failure cases in place; do not rename or reorganize existing files.
- Use conceptual grouping by filename prefix and README wording only; do not add subdirectories or a second fixture format.
- Leave CLI-mode semantics, pipe-mode behavior, REPL behavior, broken-pipe handling, and host-only sink details as local Python runtime tests.

## 2. Case Inventory Plan

### Expressions

- Purpose: keep the current baseline for successful final-result rendering.
- Why shared: these cases already define stable eval output through `stdout` and `exit_code`.
- Representative behavior:
  - arithmetic result rendering
  - assignment/rebinding result rendering
  - named-function and block-body evaluation
  - higher-order apply
  - recursion
  - pipeline-to-final-value evaluation

### Patterns

- Purpose: lock observable pattern-match results that are already implemented and deterministic.
- Why shared: pattern success/failure here is visible only through final rendered output, which is exactly the shared eval surface.
- Representative behavior:
  - list-head/list-rest success path
  - duplicate-binding equality true path
  - duplicate-binding equality false path

### Stdio Output

- Purpose: add direct coverage for observable stdout/stderr behavior, not just final expression rendering.
- Why shared: channel placement and exact emitted text are part of the approved eval contract surface.
- Representative behavior:
  - `print(...)` writes only to `stdout`
  - `log(...)` writes only to `stderr`
  - a single program can produce both `stdout` and `stderr` with exact separation preserved

### Stdin-fed Eval

- Purpose: keep eval coverage for command-source execution with provided stdin when the final observable result is still plain eval output.
- Why shared: stdin text is already part of the current eval case shape.
- Representative behavior:
  - existing `stdin |> lines |> ... |> collect |> sum`
  - no new pipe-mode or CLI-wrapper cases

### Deterministic Failure Output

- Purpose: keep exact failure assertions limited to errors with already-stable wording.
- Why shared: approved eval contract includes exact `stderr` and `exit_code` matching.
- Representative behavior:
  - undefined-name failure
  - bad-rest-pattern failure

## 3. File / Directory Plan

Add:

- `docs/architecture/issue-132-eval-shared-contract-design.md`
- `spec/eval/output-print.yaml`
- `spec/eval/output-log.yaml`
- `spec/eval/output-print-and-log.yaml`
- `spec/eval/pattern-duplicate-binding-false.yaml`

Modify:

- `spec/eval/README.md`
- `tools/spec_runner/README.md`
- `README.md`
- `GENIA_STATE.md`
- `tests/test_spec_ir_runner_blackbox.py`

No directory changes:

- keep `spec/eval/` flat
- keep existing eval YAML filenames unchanged
- do not split eval into subdirectories

Rationale:

- adding new files is lower-risk than editing existing case bodies
- one new file per new behavior keeps diffs obvious
- only one shared-runner test file needs fixture-list expansion if implementation keeps the current explicit fixture assertions

## 4. Shared vs Local Test Boundary

### Shared eval contract case

- Final expression result rendering in command-source eval.
  Reason: this is already the main shared eval surface.
- Deterministic stdout-only output from ordinary eval source.
  Reason: `stdout` is a first-class compared field.
- Deterministic stderr-only output from ordinary eval source.
  Reason: `stderr` is a first-class compared field.
- Mixed stdout/stderr output from one ordinary eval run.
  Reason: exact channel separation is part of the approved contract.
- Duplicate-binding false-path result rendering.
  Reason: same semantic family as the existing true-path shared case, with deterministic plain output.
- Existing stdin-fed command-source eval where the final compared surface is still `stdout`/`stderr`/`exit_code`.
  Reason: stdin is already supported in the current eval schema.

### Local Python runtime test

- File-mode dispatch behavior.
  Reason: this is CLI behavior, not eval shared coverage.
- `-p` / `--pipe` behavior and pipe-specific diagnostics.
  Reason: this belongs to CLI/flow shared categories, not eval.
- REPL output and REPL error handling.
  Reason: REPL is out of scope and not part of command-source eval cases.
- Broken-pipe behavior.
  Reason: host/process behavior, not portable eval contract.
- Injected custom streams, sink object identity, flush behavior, terminal escapes, and `write`/`writeln(stdout, ...)` sink mechanics.
  Reason: these depend on Python sink/runtime setup and are broader than the approved eval contract.
- Exact wording for additional rich pipeline diagnostics not already locked in eval specs.
  Reason: risk of freezing CLI/flow-host phrasing as portable eval contract.

### Not covered in this issue

- New error families beyond deterministic cases already proved by current tests.
  Reason: the issue is coverage hardening, not widening failure taxonomy.
- Any case requiring schema changes or runner behavior changes.
  Reason: out of scope unless unexpectedly required.

## 5. Case Shape / Schema Usage

Use the existing eval YAML schema unchanged.

Required fields:

- `name`
- `category`
- `input.source`
- `expected.stdout`
- `expected.stderr`
- `expected.exit_code`

Optional fields:

- `input.stdin`
- `notes`

Naming conventions:

- keep lowercase kebab-case
- keep filenames identical to `name`
- use plain behavior names, not issue numbers or abstract group IDs
- prefer prefixes only where they make grouping clearer, for example `output-*`

Normalization expectations:

- expected text in YAML should keep explicit newlines exactly as observed
- shared runner continues to normalize only `\r\n` and `\r` to `\n` for actual `stdout` and `stderr`
- no trimming or whitespace folding is added

Schema risk:

- none expected
- if implementation discovers a need for new fields, that should be treated as a stop-and-review issue, not folded in silently

## 6. Runner / Test Impact

Shared spec runner usage:

- no runner behavior changes
- implementation should continue using `python -m tools.spec_runner`

Existing test commands:

- current shared spec runner command remains sufficient
- current targeted doc/contract checks remain sufficient after doc wording updates

Fixture assumptions:

- if `tests/test_spec_ir_runner_blackbox.py` remains explicit, extend it with one eval fixture-coverage assertion that includes the new filenames, or add a small eval parametrization mirroring the existing IR one
- no loader/comparator/executor changes should be needed

CI behavior:

- no workflow changes expected
- expanded eval fixtures should run automatically anywhere the shared spec suite or fixture tests already run

## 7. Doc Sync Plan

### `GENIA_STATE.md`

- Drift risk: top-level contract could still describe eval coverage too narrowly or too vaguely once new cases land.
- Clarify: eval coverage still compares only normalized `stdout`, normalized `stderr`, and exact `exit_code`, but now includes direct stdio-output cases in addition to final-result rendering.

### `README.md`

- Drift risk: high-level spec summary could overclaim or underclaim the practical eval case inventory.
- Clarify: eval shared cases cover final rendered results plus direct stdout/stderr output separation for deterministic programs.

### `spec/eval/README.md`

- Drift risk: current README is too thin to describe what kinds of eval behavior are intentionally covered.
- Clarify: case categories now include expressions, patterns, direct stdio output, stdin-fed eval, and deterministic failures.

### `tools/spec_runner/README.md`

- Drift risk: runner docs may continue to describe the comparison fields correctly but not the broadened fixture inventory.
- Clarify: runner semantics are unchanged; the eval suite now includes direct stdout/stderr separation cases.

### `GENIA_REPL_README.md`

- Drift risk: low.
- Clarify only if implementation wording elsewhere starts implying REPL coverage as part of shared eval; otherwise no change needed for this issue.

## 8. Risk Analysis

- Freezing host quirks as portable contract.
  Mitigation: only promote cases already proven in ordinary command-source eval and avoid sink-object/runtime-injection tests.
- Eval/CLI boundary blur.
  Mitigation: exclude file mode, pipe mode, REPL, and argument-parsing behavior from new shared cases.
- Docs overstating coverage.
  Mitigation: update only the files above and keep wording tied to compared fields, not to the full runtime.
- Schema creep.
  Mitigation: require all new cases to use the current eval schema unchanged.
- Fixture drift between shared cases and black-box tests.
  Mitigation: update the explicit eval fixture assertions in one place during implementation.
- Freezing unstable error wording.
  Mitigation: keep new failure coverage narrow and deterministic; do not add richer pipeline/CLI diagnostic cases in this issue.

## 9. Implementation Handoff

Touch:

- `spec/eval/README.md`
- `spec/eval/output-print.yaml`
- `spec/eval/output-log.yaml`
- `spec/eval/output-print-and-log.yaml`
- `spec/eval/pattern-duplicate-binding-false.yaml`
- `tests/test_spec_ir_runner_blackbox.py`
- `GENIA_STATE.md`
- `README.md`
- `tools/spec_runner/README.md`

Make:

- add the four new eval YAML cases using the existing schema
- keep existing eval files unchanged unless a duplicate/obsolete case must be cleaned up separately
- extend the shared-spec black-box test so the new eval fixtures are explicitly exercised
- update the minimal doc wording needed to keep coverage claims accurate

Avoid:

- changing loader/comparator/executor behavior
- changing eval semantics
- adding pipe-mode, REPL, or file-mode cases
- introducing new schema fields or subdirectories

Validate:

- `python -m tools.spec_runner`
- targeted shared-runner fixture tests
- targeted doc/contract sync tests affected by wording changes
