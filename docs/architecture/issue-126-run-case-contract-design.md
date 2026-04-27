# Issue #126 Design — `run_case` Contract Alignment Plan

**Phase:** design
**Branch:** `issue-126-run-case-contract`
**Issue:** #126 — Define minimal host adapter contract (`run_case` interface)
**Spec:** `docs/architecture/issue-126-run-case-contract-spec.md`

---

## 1. Branch Check

Branch: `issue-126-run-case-contract` — not `main`. Proceeding.

---

## 2. Alignment Strategy: Replace Scaffold Entirely

**Chosen: Option (a) — replace the scaffold entirely.**

`SpecCase` and `SpecResult` are removed. `run_case` is rewritten to accept `LoadedSpec` and return
`ActualResult`.

**Why not option (b) — thin wrapper:**
- `SpecCase` wraps all CLI fields inside an `input: dict`, requiring a disassembly step that adds
  noise with no benefit.
- `SpecResult` lacks the `parse` field entirely, so it cannot carry parse results through the
  contract without structural changes anyway.
- `SpecResult.success`, `SpecResult.result`, and `SpecResult.error` are not consumed by the
  comparator and must not appear in the portable result.
- A thin wrapper would keep two sets of types in scope and require a conversion layer that solves
  no problem. `executor.py` already has the right dispatch and normalization shape; moving it into
  `adapter.py` directly is simpler.

---

## 3. Changes to `hosts/python/adapter.py`

### 3.1 Removed

- `SpecCase` dataclass — replaced by `LoadedSpec` (from `tools.spec_runner.loader`)
- `SpecResult` dataclass — replaced by `ActualResult` (from `tools.spec_runner.executor`)
- `from .normalize import normalize_result` — the old normalize function is removed

### 3.2 New signature

```python
from tools.spec_runner.loader import LoadedSpec
from tools.spec_runner.executor import ActualResult
from .normalize import normalize_text, strip_trailing_newlines

def run_case(spec: LoadedSpec) -> ActualResult:
```

### 3.3 New dispatch body

Dispatch logic is identical to the current `executor.py::execute_spec` body, moved here as the
canonical implementation:

```
parse   → parse_and_normalize(spec.source) → ActualResult(parse=result)
ir      → exec_ir(...)                     → ActualResult(ir=result["ir"])
cli     → exec_cli(spec)                   → ActualResult(stdout=stripped, stderr=stripped, exit_code=...)
flow    → exec_flow(spec)                  → ActualResult(stdout=normalized, stderr=normalized, exit_code=...)
eval    → run_eval_subprocess(...)         → ActualResult(stdout=normalized, stderr=normalized, exit_code=...)
error   → run_eval_subprocess(...)         → ActualResult(stdout=normalized, stderr=normalized, exit_code=...)
other   → raise ValueError(f"Unknown spec case category: {spec.category}")
```

CLI path applies `strip_trailing_newlines(normalize_text(...))` to both `stdout` and `stderr`.
eval, flow, error paths apply `normalize_text(...)` only — no trailing-newline stripping.
ir and parse paths return their result objects without text normalization at this boundary.

### 3.4 exec_ir call site

The current `executor.py` passes a `SimpleNamespace` to `exec_ir`. That adapter-internal wrapping
stays in `adapter.py`. The call becomes:

```python
result = exec_ir(SimpleNamespace(input={"source": spec.source}, stdin=None))
```

This is an internal adapter detail — `exec_ir`'s calling convention is host-specific and not part
of the portable contract.

---

## 4. Changes to `hosts/python/normalize.py`

### 4.1 Removed

- `normalize_result(raw, case)` — this function returns a `SpecResult`-shaped dict which is not
  the portable result type. It is removed along with `SpecResult`.
- `_normalize_value(value)` — not consumed at the adapter boundary for any portable contract field.
  Removed.
- `_normalize_text(value)` — renamed and made the canonical helper (see below).

### 4.2 Added / renamed

```python
def normalize_text(text: str) -> str:
    """Line-ending normalization: \\r\\n → \\n, \\r → \\n."""
    return text.replace("\r\n", "\n").replace("\r", "\n")

def strip_trailing_newlines(text: str) -> str:
    """Strip trailing newlines. CLI category only."""
    return text.rstrip("\n")
```

These replace the private `_normalize_text` and `_strip_trailing_newlines` that are currently
duplicated in `executor.py`. Both `adapter.py` and `executor.py` import from `normalize.py`.

---

## 5. Changes to `tools/spec_runner/executor.py`

`execute_spec` becomes a thin delegation wrapper:

```python
from hosts.python.adapter import run_case

def execute_spec(spec: LoadedSpec) -> ActualResult:
    return run_case(spec)
```

The local helpers `_normalize_text` and `_strip_trailing_newlines` are removed from `executor.py`
(they move to `normalize.py`). `ActualResult` remains defined in `executor.py` — it is the
canonical result type and `comparator.py` imports it from here.

`runner.py` calls `execute_spec`; that call site does not change.

---

## 6. No Changes

- `tools/spec_runner/loader.py` — `LoadedSpec` is the canonical input type. No changes.
- `tools/spec_runner/comparator.py` — `compare_spec(spec, actual: ActualResult)` is unchanged.
  The result shape `adapter.py` returns is already `ActualResult`-compatible.
- `tools/spec_runner/runner.py` — calls `execute_spec`. Not changed.

---

## 7. Integration Boundary

```
runner.py
  └─ execute_spec(spec: LoadedSpec) -> ActualResult   [executor.py — thin wrapper]
       └─ run_case(spec: LoadedSpec) -> ActualResult  [adapter.py — canonical dispatch + normalization]
            ├─ exec_parse / parse_and_normalize
            ├─ exec_ir
            ├─ exec_cli
            ├─ exec_flow
            └─ run_eval_subprocess
```

The execution boundary is `adapter.py::run_case`. `executor.py` exists only to preserve the
`runner.py` call site without changes.

---

## 8. Docs Phase Changes

In order:

1. **`docs/host-interop/HOST_INTEROP.md`** — update the `run_case` description to document the
   canonical input/output contract: accepts `LoadedSpec`-compatible fields, returns
   `ActualResult`-compatible fields. Remove any statement that `run_case` returns `SpecResult`.
   Document CLI trailing-newline stripping explicitly.

2. **`GENIA_STATE.md`** — update the Python host adapter description to reflect that the adapter
   entrypoint is wired to the spec runner (no longer bypassed). Do not imply multi-host support.

3. **`tools/spec_runner/README.md`** (if it exists) — note that `execute_spec` now delegates to
   `hosts/python/adapter.py::run_case`.

4. **`README.md`** and **`GENIA_REPL_README.md`** — no update. This change does not affect
   user-visible behavior.

---

## 9. Summary of File Touches

| File | Change |
|------|--------|
| `hosts/python/adapter.py` | Replace scaffold: remove `SpecCase`/`SpecResult`, rewrite `run_case` to accept `LoadedSpec`, return `ActualResult` |
| `hosts/python/normalize.py` | Remove `normalize_result`, `_normalize_value`; add public `normalize_text` and `strip_trailing_newlines` |
| `tools/spec_runner/executor.py` | Replace body of `execute_spec` with `return run_case(spec)`; remove local normalization helpers |
| `docs/host-interop/HOST_INTEROP.md` | Update `run_case` contract description (docs phase) |
| `GENIA_STATE.md` | Update Python adapter wiring description (docs phase) |
| `tools/spec_runner/README.md` | Note delegation change (docs phase, if file exists) |
| `tools/spec_runner/loader.py` | No change |
| `tools/spec_runner/comparator.py` | No change |
| `tools/spec_runner/runner.py` | No change |
