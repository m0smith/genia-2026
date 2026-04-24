
# Shared Spec Runner

The shared spec runner loads shared spec cases, executes them against the Python reference host, and compares normalized observable outputs.

**Python is the only implemented host today.**

## Runner Scope (Current Phase)

- **Active categories:** `eval`, `ir`, `cli`, `flow` (executable shared spec files)
- **Scaffold-only:** `parse`, `error` (no executable shared spec files yet)
- YAML spec files are loaded from `spec/eval/`, `spec/ir/`, `spec/cli/`, and `spec/flow/`
- The loader uses one shared top-level envelope for active executable categories: `name`, `id`, `category`, `description`, `input`, `expected`, and `notes`
- Comparison fields:
  - eval: `stdout`, `stderr`, `exit_code`
  - cli: `stdout`, `stderr`, `exit_code`
  - flow: `stdout`, `stderr`, `exit_code`
  - ir: normalized portable Core IR

Browser execution is planned to use the Python reference host on a backend service in the current playground direction; this does not add a second implemented host today.

## How to run the spec suite

```bash
python -m tools.spec_runner
```

## How it works

- Cases are loaded from `spec/eval/*.yaml`, `spec/cli/*.yaml`, `spec/ir/*.yaml`, and `spec/flow/*.yaml`
- Each case is executed independently against the Python reference host
- CLI cases are executed through the Python host adapter
- Flow cases are executed through command-source execution in the Python host adapter; the runner does not route Flow cases through CLI pipe mode
- CLI file mode uses `input.file`; command mode uses `input.command` with empty `input.stdin`; pipe mode uses `input.command` as `-p <command>` when `input.stdin` is non-empty, with that stdin passed directly as subprocess input
- The runner does not construct shell pipelines for CLI specs
- Eval, CLI, and Flow cases normalize `stdout`/`stderr` line endings before comparison
- The current CLI suite covers deterministic non-interactive file, command, and pipe cases. REPL is not covered by shared executable specs
- The current Flow suite covers first-wave observable contract cases only: lazy pull-based observable behavior through early termination, single-use enforcement, deterministic outputs, `refine(..steps)`, `rules(..fns)`, `step_*` / `rule_*` equivalence, `rules()` identity, and error propagation via invalid-reducer-on-flow diagnostic
- IR cases normalize portable Core IR before comparison and fail if host-local optimized IR appears in the shared IR path
- Failures are reported per spec with expected vs actual fields

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
- Internal whitespace is not trimmed or collapsed. Stderr is not otherwise normalized.
- For eval, cli, and flow, the compared surface remains only `stdout`, `stderr`, and `exit_code`
- For IR, the runner compares normalized host-neutral portable Core IR output
- For IR, execution flow is `source -> parse -> lower -> normalize -> compare`
- It does not trim meaningful whitespace

**GENIA_STATE.md is the final authority for implemented behavior. All other docs/specs must align with this contract.**
