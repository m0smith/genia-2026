
# Shared Spec Runner

The shared spec runner loads shared spec cases, executes them against the Python reference host, and compares normalized observable outputs.

**Python is the only implemented host today.**
Implemented runner scope in this phase:
- eval cases only
- YAML spec files under `spec/eval/`
- comparison fields: `stdout`, `stderr`, `exit_code`

Browser execution is planned to use the Python reference host on a backend service in the current playground direction; this does not add a second implemented host today.

**How to run the spec suite:**

```bash
python -m tools.spec_runner
```

**How it works:**
- cases are loaded from `spec/eval/*.yaml`
- each case is executed independently against the Python reference host
- stdout/stderr line endings are normalized before comparison
- failures are reported per spec with expected vs actual fields

**Example failure output:**

```
FAIL eval arithmetic-basic (/path/to/spec/eval/arithmetic-basic.yaml)
  field: stdout
    expected: '42\n'
    actual:   '41\n'
```

**Normalization:**
- current Phase 1 runner normalizes line endings for stdout/stderr
- it does not trim meaningful whitespace
- it compares only `stdout`, `stderr`, and `exit_code`

**GENIA_STATE.md is the final authority for implemented behavior. All other docs/specs must align with this contract.**
