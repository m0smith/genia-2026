# Issue #126 Spec — Minimal Host Adapter Contract (`run_case`)

**Phase:** spec
**Branch:** `issue-126-run-case-contract`
**Issue:** #126 — Define minimal host adapter contract (`run_case` interface)

This phase defines expected behavior only.
It does not add failing tests, implementation, or documentation sync edits.

---

## 1. Source Of Truth

Final authority: `GENIA_STATE.md`

Supporting:
- `GENIA_RULES.md`
- `docs/host-interop/HOST_INTEROP.md`
- `tools/spec_runner/executor.py` (active execution behavior)
- `tools/spec_runner/loader.py` (canonical input shape — `LoadedSpec`)
- `tools/spec_runner/comparator.py` (canonical comparison contract — `ActualResult` fields consumed)
- `hosts/python/adapter.py` (existing scaffold, NOT currently wired to the runner)

Relevant existing truths:
- Python is the only implemented host and is the reference host.
- The active shared spec runner routes execution through
  `tools/spec_runner/executor.py::execute_spec(spec: LoadedSpec) -> ActualResult`.
- `hosts/python/adapter.py::run_case(case: SpecCase) -> SpecResult` exists as a scaffold but is
  not called by the current runner.
- `GENIA_STATE.md` and `HOST_INTEROP.md` both describe `run_case` as the host adapter entrypoint,
  but today the runner bypasses it.
- `GENIA_STATE.md` states no generic multi-host runner exists.

---

## 2. Scope Decision

### Included in this spec

- Define the canonical `run_case(case) -> result` interface that the shared spec harness will
  eventually route through.
- Define the input type: what fields `run_case` must accept, derived from what `LoadedSpec`
  carries today.
- Define the output type per category: exact fields the comparator consumes from `ActualResult`.
- Define normalization rules per category, including the CLI trailing-newline rule.
- Identify and resolve the divergence between the scaffold (`adapter.py`) and the active runner
  (`executor.py`).

### Explicitly excluded from this spec

- New host implementations (Node, Go, Rust, C++, browser-native).
- Generic multi-host orchestration.
- Changes to `LoadedSpec`, `comparator.py`, `loader.py`, or `runner.py` beyond the execution-boundary
  change.
- Structured error model expansion (phase/category/source-location assertions).
- Renaming existing `exec_*` functions.
- Changing spec YAML behavior or spec file format.
- Implementation, failing tests, or docs sync.

---

## 3. Divergence Resolution

Two execution paths exist today:

**Active path** (`tools/spec_runner/executor.py::execute_spec`):
- Input: `LoadedSpec` (flat dataclass from the loader).
- Output: `ActualResult` (frozen dataclass with `stdout`, `stderr`, `exit_code`, `ir`, `parse`).
- CLI normalization: strips trailing newlines from both `stdout` and `stderr` after line-ending
  normalization. No other category strips trailing newlines.
- Flow/eval/error normalization: normalizes line endings (`\r\n` → `\n`, `\r` → `\n`) only.
- IR: returns normalized portable Core IR directly from `exec_ir`.
- Parse: returns normalized parse dict (`{kind: ok, ast: ...}` or `{kind: error, type: ..., message: ...}`).

**Scaffold path** (`hosts/python/adapter.py::run_case`):
- Input: `SpecCase` (adapter-specific dataclass).
- Output: `SpecResult` (dataclass with `success`, `stdout`, `stderr`, `exit_code`, `result`, `error`, `ir`).
- Normalization: `hosts/python/normalize.py::normalize_result` — normalizes line endings but does NOT
  strip trailing newlines for CLI. This diverges from the active runner.
- `SpecResult.success`, `SpecResult.result`, and `SpecResult.error` are not consumed by the comparator
  and have no place in the portable contract.
- `SpecResult` does not have a `parse` field; `parse` category results cannot be returned.

**Resolution:**

The canonical adapter output for later phases is the `ActualResult` shape, not the `SpecResult` shape.
`SpecResult` must not be used as the portable result type. The adapter must return an `ActualResult`-
compatible value so that `comparator.py` can consume it without changes.

The scaffold in `adapter.py` must be aligned to accept a `LoadedSpec`-compatible input and return an
`ActualResult`-compatible output. Whether this is done by replacing the scaffold entirely or by
retaining `SpecCase`/`SpecResult` as internal adapter types and converting at the boundary is a design
decision; this spec only mandates the external interface.

---

## 4. Input Contract

### 4.1 What `run_case` must accept

The host adapter entrypoint must accept all fields that `LoadedSpec` carries which are needed for
execution. The following fields are the mandatory execution surface:

| Field         | Type                   | Present for                         |
|---------------|------------------------|--------------------------------------|
| `name`        | `str`                  | all categories (identity/reporting)  |
| `category`    | `str`                  | all categories                       |
| `source`      | `str`                  | all categories                       |
| `stdin`       | `str`                  | eval, flow, error, cli               |
| `file`        | `str \| None`          | cli (file mode)                      |
| `command`     | `str \| None`          | cli (command and pipe modes)         |
| `argv`        | `list[str]`            | cli                                  |
| `debug_stdio` | `bool`                 | cli                                  |

`spec_id`, `path`, `description`, and `expected_*` fields are metadata only; the host adapter must
not require them for execution and must not use `expected_*` values to influence the execution result.

### 4.2 Category values

Accepted category values: `"parse"`, `"ir"`, `"eval"`, `"cli"`, `"flow"`, `"error"`.

An unsupported category must raise an error immediately. The adapter must not silently return a
result for an unknown category.

---

## 5. Output Contract

### 5.1 Fields per category

The host adapter result must provide exactly the fields consumed by `comparator.py::compare_spec`.
No extra fields (`success`, `result`, `error`) are part of the portable contract.

**eval / flow / error:**

| Field       | Type  | Rule                                   |
|-------------|-------|----------------------------------------|
| `stdout`    | `str` | line-ending normalized, no trailing-newline strip |
| `stderr`    | `str` | line-ending normalized, no trailing-newline strip |
| `exit_code` | `int` | as returned by the subprocess          |

**cli:**

| Field       | Type  | Rule                                                      |
|-------------|-------|-----------------------------------------------------------|
| `stdout`    | `str` | line-ending normalized, then trailing newlines stripped   |
| `stderr`    | `str` | line-ending normalized, then trailing newlines stripped   |
| `exit_code` | `int` | as returned by the subprocess                             |

**ir:**

| Field | Type     | Rule                                              |
|-------|----------|---------------------------------------------------|
| `ir`  | `object` | normalized portable Core IR (list of IR node dicts) |

**parse:**

| Field   | Type   | Rule                                                          |
|---------|--------|---------------------------------------------------------------|
| `parse` | `dict` | `{kind: "ok", ast: <normalized AST>}` or `{kind: "error", type: <str>, message: <str>}` |

### 5.2 Normalization rules

**Line-ending normalization** (all text fields):
- `\r\n` → `\n`
- `\r` → `\n`

**Trailing-newline stripping (CLI only)**:
- After line-ending normalization, strip all trailing `\n` characters from `stdout` and `stderr`.
- This rule applies only to `cli` category. It must not apply to `eval`, `flow`, `error`, `ir`, or
  `parse`.

**IR normalization**:
- The result of `exec_ir` is the normalized portable Core IR. No additional normalization is applied
  at the adapter boundary; `exec_ir` owns IR normalization.

**Parse normalization**:
- The result of the parse execution path is the normalized parse dict. The adapter returns it as-is.
- For `kind: error` parse results, `message` must be a string; comparison is substring-based (this
  is the comparator's responsibility, not the adapter's).

### 5.3 `error` category

`error` cases use the `eval` execution path. The error normalization (stdout/stderr/exit_code) is
identical to `eval`. No structured phase/category/source-location fields are added at the adapter
boundary. The adapter returns `stdout`, `stderr`, `exit_code` exactly as the subprocess provides
them after line-ending normalization.

---

## 6. Invariants

1. The adapter must not inspect `expected_*` fields from the input.
2. The adapter must not mutate the input.
3. Unsupported categories must raise an error, never silently return a result.
4. CLI trailing-newline stripping must occur after line-ending normalization, not before.
5. IR and parse result shapes must remain compatible with `comparator.py` without changes to
   the comparator.
6. The adapter result for `eval`, `flow`, and `error` must not strip trailing newlines.
7. Host-specific subprocess strategy, internal runtime objects, and file layout remain
   host-specific and must not appear in the portable result.

---

## 7. Observable Cases (to become tests in the test phase)

These are not test code. They describe the contract. Tests are written in the test phase.

### Case: adapter-eval-basic

```
category: eval
source: print("hello")
expected:
  stdout: "hello\n"
  stderr: ""
  exit_code: 0
```

Adapter result must provide `stdout="hello\n"`, `stderr=""`, `exit_code=0`.
No trailing-newline stripping for eval.

### Case: adapter-cli-trailing-newline

```
category: cli
command: print("hello")
stdin: ""
argv: []
expected:
  stdout: "hello"
  stderr: ""
  exit_code: 0
```

Adapter result must strip trailing newlines from `stdout`. Raw subprocess output `"hello\n"` normalizes
to `"hello"`.

### Case: adapter-eval-no-strip

```
category: eval
source: print("hello")
```

Adapter result `stdout` is `"hello\n"`. It must NOT be `"hello"`. Trailing-newline stripping is
CLI-only.

### Case: adapter-ir-basic

```
category: ir
source: 1 + 2
```

Adapter result provides `ir` field with normalized portable Core IR list. No `stdout`/`stderr`/`exit_code`
fields are required.

### Case: adapter-parse-ok

```
category: parse
source: 1 + 2
```

Adapter result provides `parse` field with `{kind: "ok", ast: <normalized AST>}`.

### Case: adapter-parse-error

```
category: parse
source: (
```

Adapter result provides `parse` field with `{kind: "error", type: <str>, message: <str>}`.

### Case: adapter-unsupported-category

```
category: unknown_category
```

Adapter raises an error immediately. No result is returned.

### Case: adapter-cli-crlf

```
category: cli
command: <source that produces CRLF output>
```

Adapter normalizes `\r\n` to `\n` before stripping trailing newlines.

### Case: adapter-error-stdout-stderr

```
category: error
source: <source that triggers a runtime error>
expected:
  stdout: ""
  stderr: <error message>
  exit_code: 1
```

Adapter uses eval path. Returns `stdout`, `stderr`, `exit_code` with line-ending normalization only.

---

## 8. Cases NOT in scope

- Structured error assertions (phase, category, source-location fields) — not in active spec contracts.
- Multi-host dispatch — no generic runner exists; Python is the only host.
- `SpecResult.success`, `SpecResult.result`, `SpecResult.error` — not consumed by the comparator,
  not part of the portable contract.
- Nested CLI argv edge cases — already covered by existing CLI spec cases.
- Changes to how `exec_ir` or `exec_parse` normalize their results internally.

---

## 9. Cross-phase notes

### For the design phase

- The design must choose one of two alignment strategies for `adapter.py`:
  a. Replace the scaffold entirely: `run_case` accepts a `LoadedSpec` and returns `ActualResult`
     directly, removing `SpecCase` and `SpecResult`.
  b. Retain `SpecCase`/`SpecResult` as internal types but add a thin public entry that accepts
     `LoadedSpec` and converts before delegating to the existing `run_case` body.
- Either way, the design must confirm that `normalize.py::normalize_result` is updated or replaced
  so that CLI results strip trailing newlines (matching `executor.py`) and that `parse` results
  are returned in the `parse` field (not `ir`/`result`).
- The design must confirm `executor.py::execute_spec` will be thin-wired to call the adapter after
  this issue, or describe the integration boundary explicitly.
- No changes to `loader.py`, `comparator.py`, or `runner.py` are expected.

### For the test phase

Write the following failing tests before implementation:

- `tests/test_adapter_contract.py` — unit tests for the adapter contract:
  - `run_case` with eval input returns `stdout`, `stderr`, `exit_code` (no trailing-newline strip).
  - `run_case` with cli input strips trailing newlines from stdout and stderr.
  - `run_case` with ir input returns `ir` field.
  - `run_case` with parse input returns `parse` field with `kind: ok` or `kind: error`.
  - `run_case` with error input uses eval path; returns `stdout`, `stderr`, `exit_code`.
  - `run_case` with flow input returns `stdout`, `stderr`, `exit_code` (no trailing-newline strip).
  - `run_case` with unsupported category raises an error.
  - `run_case` with cli input applies line-ending normalization before stripping trailing newlines.

Run them and confirm they fail before any implementation change.

Confirm all existing shared spec cases still pass after implementation:
- `spec/eval/*.yaml`
- `spec/ir/*.yaml`
- `spec/cli/*.yaml`
- `spec/flow/*.yaml`
- `spec/error/*.yaml`
- `spec/parse/*.yaml`

### For the docs phase

In order:
1. `docs/host-interop/HOST_INTEROP.md` — update the `run_case` description to reflect the
   canonical input/output contract as defined here. Remove any claim that `run_case` returns
   `SpecResult`; document the `ActualResult`-compatible surface instead.
2. `GENIA_STATE.md` — update the Python host adapter description to reflect that the adapter
   entrypoint is wired to the spec runner. Do not imply multi-host support.
3. `tools/spec_runner/README.md` (if it exists) — note the execution boundary change if the
   integration path changes.
4. `README.md` and `GENIA_REPL_README.md` — no update expected unless user-visible behavior changes.

---

## 10. Recommended next prompt (DESIGN phase)

```
You are working in the Genia repo on issue #126:
Define minimal host adapter contract (run_case interface)

Spec is complete. Branch: issue-126-run-case-contract.
Spec doc: docs/architecture/issue-126-run-case-contract-spec.md

Design phase task:
1. Confirm current branch is issue-126-run-case-contract.
   Refuse to modify files on main.
2. Read the spec doc and the following files before writing anything:
   - hosts/python/adapter.py
   - tools/spec_runner/executor.py
   - tools/spec_runner/comparator.py
   - hosts/python/normalize.py
3. Write a design document at docs/architecture/issue-126-run-case-contract-design.md
   describing exactly:
   - Which alignment strategy is chosen for adapter.py (replace scaffold vs. thin wrapper)
   - Exact changes to adapter.py: new input type, new return type, CLI trailing-newline rule
   - Exact changes to normalize.py: what is added/changed/removed
   - How executor.py routes through the adapter (or what the integration boundary is)
   - What docs change in the docs phase and exactly what is updated
   - Confirmation that loader.py, comparator.py, and runner.py are not changed
4. Do NOT implement. Do NOT write tests. Do NOT update behavior docs.
5. Commit with prefix: design(host): run_case contract alignment plan issue #126
```
