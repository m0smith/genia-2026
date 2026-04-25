
# Shared Spec Runner

The shared spec runner loads shared spec cases, executes them against the Python reference host, and compares normalized observable outputs.

**Python is the only implemented host today.**

## Runner Scope (Current Phase)

- **Active categories:** `eval`, `ir`, `cli`, `flow`, `error`, `parse` (executable shared spec files)
- YAML spec files are loaded from `spec/eval/`, `spec/ir/`, `spec/cli/`, `spec/flow/`, `spec/error/`, and `spec/parse/`
- The loader uses one shared top-level envelope for active executable categories: `name`, `id`, `category`, `description`, `input`, `expected`, and `notes`
- Comparison fields:
  - eval: `stdout`, `stderr`, `exit_code`
  - cli: `stdout`, `stderr`, `exit_code`
  - flow: `stdout`, `stderr`, `exit_code`
  - error: `stdout`, `stderr`, `exit_code`
  - ir: normalized portable Core IR
  - parse: normalized AST (exact match for `kind: ok`) or error type + message substring (for `kind: error`)

Browser execution is planned to use the Python reference host on a backend service in the current playground direction; this does not add a second implemented host today.

## Dependencies

- `PyYAML` is required to load shared spec `.yaml` files.

## How to run the spec suite

```bash
python -m tools.spec_runner
```

## How it works

- Cases are loaded from `spec/eval/*.yaml`, `spec/cli/*.yaml`, `spec/ir/*.yaml`, `spec/flow/*.yaml`, `spec/error/*.yaml`, and `spec/parse/*.yaml`
- Each case is executed independently against the Python reference host
- CLI cases are executed through the Python host adapter
- Flow cases are executed through command-source execution in the Python host adapter; the runner does not route Flow cases through CLI pipe mode
- Error cases reuse the eval execution path; there is no separate error subprocess or error-specific execution path
- Parse cases call the Python host parse adapter directly (`parse_and_normalize`); no subprocess is invoked
- CLI file mode uses `input.file`; command mode uses `input.command` with empty `input.stdin`; pipe mode uses `input.command` as `-p <command>` when `input.stdin` is non-empty, with that stdin passed directly as subprocess input
- The runner does not construct shell pipelines for CLI specs
- Eval, CLI, and Flow cases normalize `stdout`/`stderr` line endings before comparison
- Error cases use the same line-ending normalization as eval before comparison
- The current CLI suite covers deterministic non-interactive file, command, and pipe cases, including file-mode `main(argv())` dispatch, command-mode final-value execution, valid pipe-mode Flow-stage usage, and current pipe-mode guidance/error cases for explicit `stdin`, explicit `run`, bare per-item stages, bare reducers, and non-Flow final results. REPL is not covered by shared executable specs
- The current Flow suite covers first-wave observable contract cases only: lazy pull-based observable behavior through early termination, single-use enforcement, deterministic outputs, `refine(..steps)`, `rules(..fns)`, `step_*` / `rule_*` equivalence, `rules()` identity, and error propagation via invalid-reducer-on-flow diagnostic
- The current Error suite covers initial normalized observable contract cases only: `stdout`, `stderr`, and `exit_code`, with `stdout` expected to be `""`, `stderr` matched exactly, and `exit_code` expected to be `1`
- IR cases normalize portable Core IR before comparison and fail if host-local optimized IR appears in the shared IR path
- Failures are reported per spec with expected vs actual fields
- `notes` is informational only and is not read by the runner; phase/category/message remain contract concepts, not structured runner fields in this phase

**Example failure output:**

```
FAIL eval arithmetic-basic (/path/to/spec/eval/arithmetic-basic.yaml)
  field: stdout
    expected: '42\n'
    actual:   '41\n'
```

**Normalization:**
- For eval, the runner normalizes line endings for `stdout`/`stderr` to `\n`; trailing newlines remain significant.
- For flow, the runner normalizes line endings for `stdout`/`stderr` to `\n`; trailing newlines remain significant.
- For cli, the runner normalizes line endings for `stdout`/`stderr` to `\n` and strips trailing newlines before comparison.
- For error, the runner normalizes line endings for `stdout`/`stderr` to `\n`; trailing newlines remain significant.
- Internal whitespace is not trimmed or collapsed. Stderr is not otherwise normalized.
- For eval, cli, flow, and error, the compared surface remains only `stdout`, `stderr`, and `exit_code`
- For IR, the runner compares normalized host-neutral portable Core IR output
- For IR, execution flow is `source -> parse -> lower -> normalize -> compare`
- For parse, the runner compares the normalized parse result: exact AST match for `kind: ok`; type exact + message substring for `kind: error`
- It does not trim meaningful whitespace

**GENIA_STATE.md is the final authority for implemented behavior. All other docs/specs must align with this contract.**
