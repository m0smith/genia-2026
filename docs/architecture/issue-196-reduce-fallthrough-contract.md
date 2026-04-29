# Contract: Replace `_reduce` Catch-All with `_reduce_error`

**Issue:** #196
**Phase:** contract
**Branch:** issue-reduce-fallthrough-analysis
**Pre-flight:** `docs/architecture/issue-196-reduce-fallthrough-preflight.md` — GO
**Date:** 2026-04-29

---

## 1. Problem Statement

`reduce` in `src/genia/std/prelude/list.genia` contains a three-arm case body:

```genia
reduce(f, acc, xs) =
  (f, acc, []) -> acc |
  (f, acc, [x, ..rest]) -> reduce(f, apply_raw(f, [acc, x]), rest) |
  (f, acc, xs) -> _reduce(f, acc, xs)
```

Arm 3 is a catch-all that fires when `xs` is not a list. Its only role is raising:
```
TypeError: reduce expected a list as third argument, received <type-name>
```

It delegates to `_reduce` — a Python-backed 3-argument function (`reduce_fn`) that immediately raises `TypeError` for any non-list input. The list-iteration body of `reduce_fn` is dead code in this call path.

**Problem:** `_reduce` is a 3-argument host function whose argument signature is wider than its actual use (only the third argument matters for the error). It carries dead iteration logic and an opaque name. The goal of this issue is to replace it with a purpose-named, 1-argument primitive.

---

## 2. Contracted Solution

### 2.1 New Primitive: `_reduce_error`

**Name:** `_reduce_error`  
**Arity:** 1  
**Argument:** `xs` — any Genia value (the non-list third argument passed to `reduce`)  
**Return:** never returns — always raises  
**Behavior:** raises `TypeError` with the exact message:
```
reduce expected a list as third argument, received <type-name>
```
where `<type-name>` is the string produced by `_runtime_type_name(xs)`.

**Portability:** `language contract`  
Any host that implements `reduce` must provide this primitive. The exact error message and type-name vocabulary are part of the shared spec contract (asserted by `spec/eval/reduce-on-flow-type-error.yaml` and `spec/flow/count-as-pipe-stage-type-error.yaml`).

**Type-name vocabulary** — the complete set of strings `_runtime_type_name` produces (from `interpreter.py:5156-5201`):

| Value type | Type-name string |
|---|---|
| Python `None` | `"none"` |
| `GeniaOptionNone` | `"none"` |
| `GeniaOptionSome(v)` | `"some(<type-name of v>)"` |
| `bool` | `"bool"` |
| `int` | `"int"` |
| `float` | `"float"` |
| `str` | `"string"` |
| `list` | `"list"` |
| `GeniaMap` | `"map"` |
| `GeniaFlow` | `"flow"` |
| `GeniaRng` | `"rng"` |
| `GeniaRef` | `"ref"` |
| `GeniaProcess` | `"process"` |
| `GeniaOutputSink` | `"sink"` |
| `GeniaBytes` | `"bytes"` |
| `GeniaZipEntry` | `"zip_entry"` |
| `GeniaPythonHandle` | `"python_handle"` |
| `GeniaPair` | `"pair"` |
| `GeniaMetaEnv` | `"meta_env"` |
| `GeniaPromise` | `"promise"` |
| `GeniaFunctionGroup` or callable | `"function"` |
| anything else | `type(value).__name__` |

This vocabulary is identical to the one currently used by `_reduce`. No type-name behavior changes.

---

### 2.2 New Arm 3 in `reduce`

**File:** `src/genia/std/prelude/list.genia`

**Before:**
```genia
reduce(f, acc, xs) =
  (f, acc, []) -> acc |
  (f, acc, [x, ..rest]) -> reduce(f, apply_raw(f, [acc, x]), rest) |
  (f, acc, xs) -> _reduce(f, acc, xs)
```

**After:**
```genia
reduce(f, acc, xs) =
  (f, acc, []) -> acc |
  (f, acc, [x, ..rest]) -> reduce(f, apply_raw(f, [acc, x]), rest) |
  (f, acc, xs) -> _reduce_error(xs)
```

Arms 1 and 2 are unchanged. Only arm 3 changes: the call target changes from
`_reduce(f, acc, xs)` (3 args) to `_reduce_error(xs)` (1 arg). The caller
passes only the non-list `xs` — `f` and `acc` are not needed to produce the error.

---

### 2.3 Changes to `src/genia/interpreter.py`

#### Add `reduce_error_fn`

A new Python function, to be defined in the same locality as `reduce_fn` (around line 7051):

```python
def reduce_error_fn(xs: Any) -> Any:
    raise TypeError(
        f"reduce expected a list as third argument, received {_runtime_type_name(xs)}"
    )
```

**Invariant:** `reduce_error_fn` must produce the identical error message string as
`reduce_fn` currently produces for non-list inputs. The message template and
`_runtime_type_name` call are unchanged.

#### Register `_reduce_error`, deregister `_reduce`

**Before (around line 7760):**
```python
env.set("_reduce", reduce_fn)
```

**After:**
```python
env.set("_reduce_error", reduce_error_fn)
```

`env.set("_reduce", reduce_fn)` is removed. `_reduce_error` is the only new registration.

#### Remove `reduce_fn`

`reduce_fn` (lines 7051–7060) is removed. Its list-iteration body was already dead code
from the arm-3 call path after issue #190. No behavior is lost.

---

### 2.4 Changes to `docs/host-interop/capabilities.md`

Add a new entry under the **Callable Invocation** group:

```markdown
#### `fn.reduce-error`

- **name:** `fn.reduce-error`
- **genia_surface:** `_reduce_error(xs)` (internal — called from `reduce` arm 3 only)
- **input:** `xs` — any non-list Genia value (the erroneous third argument to `reduce`)
- **output:** never returns — always raises
- **errors:**
  - `TypeError` with message `"reduce expected a list as third argument, received <type-name>"` — always, for all inputs; `<type-name>` is the string produced by `_runtime_type_name(xs)`
- **portability:** `language contract`
- **notes:** Single-purpose error delegate called when `reduce`'s catch-all arm fires. Any host implementing `reduce` must raise this exact `TypeError`. The type-name vocabulary is shared across all `_runtime_type_name` usages. Not intended for direct user-code use.
```

No other entry in `capabilities.md` requires change. `fn.apply-raw` notes reference the
prelude HOFs using `apply_raw`; those notes remain accurate.

---

### 2.5 No Change to `GENIA_STATE.md`

`_reduce` and `_reduce_error` are both internal implementation names, not user-visible
language surface. `GENIA_STATE.md` describes `reduce` as a prelude function using
`apply_raw` — that description remains accurate and complete. No update is needed.

`GENIA_STATE.md` does not document `_reduce` by name and will not document `_reduce_error`
by name. The user-visible contract (the error message) is captured in the shared spec.

---

### 2.6 No Change to Spec Files

| File | Action |
|------|--------|
| `spec/eval/reduce-on-flow-type-error.yaml` | Unchanged — same error message |
| `spec/flow/count-as-pipe-stage-type-error.yaml` | Unchanged — same embedded message |

Both specs assert the error message produced by `_runtime_type_name`. Since `_reduce_error`
uses the same `_runtime_type_name` call and the same message template, both specs must
continue to pass without modification.

---

## 3. Invariants That Must Be Preserved

| ID | Invariant |
|----|-----------|
| I1 | `reduce(f, acc, flow)` raises `TypeError: "reduce expected a list as third argument, received flow"` |
| I2 | `reduce(f, acc, "string")` raises `TypeError: "reduce expected a list as third argument, received string"` |
| I3 | `reduce(f, acc, [])` returns `acc` unchanged |
| I4 | `reduce(f, acc, [1, 2, 3])` accumulates left-to-right using `apply_raw` |
| I5 | `none(...)` list elements are delivered to the callback (skip_none_propagation via `apply_raw`) |
| I6 | `_reduce` is no longer registered in the env after this change |
| I7 | No user-visible API changes — `reduce` surface is identical |

---

## 4. Explicitly Out of Scope

- **`type_name(value)` general primitive** — a general `type_name` primitive would
  be more broadly useful, but introducing it is not required to resolve this issue.
  It is deferred to a future issue.
- **General `_raise_type_error(message)` primitive** — not required; `_reduce_error`
  handles the error-formatting internally.
- **Changes to `map`, `filter`, `pairs`, or any other prelude functions** — none.
- **Changes to `apply_raw`** — none.
- **Changes to `_invoke_raw_from_builtin`** — none.
- **Changes to `spec/` YAML files** — spec assertions are preserved, not changed.

---

## 5. Risk Register

| Risk | Severity | Mitigation |
|------|----------|-----------|
| Error message string diverges from current | High | `reduce_error_fn` must use the identical message template and `_runtime_type_name` call as `reduce_fn` |
| `reduce-on-flow-type-error.yaml` fails | High | Run spec suite immediately after implementation; no spec change is needed or allowed |
| `_reduce` removed before arm-3 updated | Medium | Update list.genia and interpreter.py in the same implementation commit |
| `reduce_fn` removed but still referenced | Low | Search for all `reduce_fn` references before removal |

---

## 6. Files Changed in Implementation Phase

| File | Change |
|------|--------|
| `src/genia/std/prelude/list.genia` | Arm 3: `_reduce(f, acc, xs)` → `_reduce_error(xs)` |
| `src/genia/interpreter.py` | Add `reduce_error_fn`; add `env.set("_reduce_error", ...)`; remove `env.set("_reduce", ...)`; remove `reduce_fn` |
| `docs/host-interop/capabilities.md` | Add `fn.reduce-error` entry under Callable Invocation group |

---

## 7. Exact Next Claude Prompt (Design Phase)

```
Read AGENTS.md, GENIA_STATE.md, GENIA_RULES.md, GENIA_REPL_README.md, README.md.
GENIA_STATE.md is final authority.

Issue: #196 — Pre-flight and resolve _reduce fallthrough behavior
Branch: issue-reduce-fallthrough-analysis
Phase: DESIGN

Context: Contract is at docs/architecture/issue-196-reduce-fallthrough-contract.md.
The contracted solution is to add a 1-arg host primitive _reduce_error(xs) that raises
TypeError with the exact message "reduce expected a list as third argument, received <type>",
replace _reduce(f, acc, xs) in list.genia arm 3 with _reduce_error(xs), remove the _reduce
env registration, and remove reduce_fn.

Scope:
- Produce the design document at docs/architecture/issue-196-reduce-fallthrough-design.md.
- Specify exact line numbers and diffs for each change in interpreter.py and list.genia.
- Specify the exact new capabilities.md entry for fn.reduce-error.
- Confirm the exact test that must pass without change: spec/eval/reduce-on-flow-type-error.yaml.

Scope excludes:
- Do not implement — write design only.
- Do not change any spec YAML files.
- Do not add type_name or any other general primitive beyond _reduce_error.

Output: design document at docs/architecture/issue-196-reduce-fallthrough-design.md.
Commit: design(reduce): _reduce_error primitive design for catch-all replacement issue #196
```
