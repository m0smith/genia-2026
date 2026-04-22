
# Shared Spec Runner

The shared spec runner loads shared spec cases, executes them against the Python reference host, and compares normalized observable outputs.

**Python is the only implemented host today.**

## Runner Scope (Current Phase)

- **Active categories:** `eval`, `ir` (executable shared spec files)
- **Scaffold-only:** `parse`, `cli`, `flow`, `error` (no executable shared spec files yet)
- YAML spec files are loaded from `spec/eval/` and `spec/ir/`
- Comparison fields:
  - eval: `stdout`, `stderr`, `exit_code`
  - ir: normalized portable Core IR

Browser execution is planned to use the Python reference host on a backend service in the current playground direction; this does not add a second implemented host today.

## How to run the spec suite

```bash
python -m tools.spec_runner
```

## How it works

- Cases are loaded from `spec/eval/*.yaml` and `spec/ir/*.yaml`
- Each case is executed independently against the Python reference host
- Eval cases normalize `stdout`/`stderr` line endings before comparison
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
- For eval, the runner normalizes line endings for `stdout`/`stderr`
- For IR, the runner compares normalized host-neutral portable Core IR output
- For IR, execution flow is `source -> parse -> lower -> normalize -> compare`
- It does not trim meaningful whitespace

**GENIA_STATE.md is the final authority for implemented behavior. All other docs/specs must align with this contract.**
