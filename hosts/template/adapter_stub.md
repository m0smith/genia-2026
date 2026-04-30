# Spec Runner Integration Stub

**Authoritative contract:** `docs/host-interop/HOST_INTEROP.md` §Host Adapter and Spec Runner Model

**Wiring point:** `tools/spec_runner/executor.py::execute_spec`

This file documents the spec runner integration contract. Implement `run_case` in your host adapter to connect this host to the shared spec runner.

---

## Required Entrypoint

```
run_case(spec: LoadedSpec) -> ActualResult
```

The shared spec runner routes all category execution through this entrypoint via `tools/spec_runner/executor.py::execute_spec`. See `HOST_INTEROP.md` for the full contract.

---

## LoadedSpec Input Fields

| Field | Present for |
|---|---|
| `category` | all |
| `source` | all |
| `stdin` | eval, flow, error, cli |
| `file` | cli (file mode) |
| `command` | cli (command and pipe modes) |
| `argv` | cli |
| `debug_stdio` | cli (debug mode) |

---

## ActualResult Output Fields

| Field | Type |
|---|---|
| `stdout` | string |
| `stderr` | string |
| `exit_code` | int |

---

## Category Stubs

Implement one category at a time. Start with `eval` — it requires only source execution and stdout/stderr/exit_code capture.

### parse

TODO: implement parse execution — call the host parser, compare normalized AST output.

For `kind: ok` cases the normalized AST is compared exactly.
For `kind: error` cases the error type is compared exactly and the message is matched as a substring.

### ir

TODO: implement IR execution — call host AST→Core IR lowering, compare normalized portable Core IR output before host-local optimization.

Only the minimal portable Core IR node families defined in `docs/architecture/core-ir-portability.md` are part of the contract.

### eval

TODO: implement eval execution — run the source string through the host evaluator, capture stdout, stderr, and exit_code.

Comparison is exact after line-ending normalization (`\r\n` and `\r` → `\n`).

### cli

TODO: implement CLI execution — run the source as a CLI process (file mode, command mode, or pipe mode), capture stdout, stderr, and exit_code.

CLI input fields: `file`, `command`, `stdin`, `argv`.

### flow

TODO: implement flow execution — run a flow-source program through the host, capture stdout, stderr, and exit_code.

Flow shared coverage is first-wave only; see `spec/flow/` for current cases.

### error

TODO: implement error execution — run the source through the host evaluator, assert `stdout` is `""`, match `stderr` exactly, assert `exit_code` is `1`.

---

## Reference Implementation

See `hosts/python/adapter.py` for the current working reference implementation.
