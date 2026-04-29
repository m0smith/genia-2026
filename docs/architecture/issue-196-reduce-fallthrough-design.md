# Design: Replace `_reduce` Catch-All with `_reduce_error`

**Issue:** #196
**Phase:** design
**Branch:** issue-reduce-fallthrough-analysis
**Contract:** `docs/architecture/issue-196-reduce-fallthrough-contract.md`
**Date:** 2026-04-29

---

## 1. Overview

Three targeted changes, applied together in one implementation commit:

| # | File | Change |
|---|------|--------|
| A | `src/genia/std/prelude/list.genia` | Arm 3: `_reduce(f, acc, xs)` → `_reduce_error(xs)` |
| B | `src/genia/interpreter.py` | Replace `reduce_fn` with `reduce_error_fn`; swap env registration |
| C | `docs/host-interop/capabilities.md` | Insert `fn.reduce-error` entry after `fn.apply-raw` |

No spec YAML files change. No test files change in this phase (tests are the next phase).

---

## 2. Change A — `src/genia/std/prelude/list.genia`

### Location

Line 116 (the only line that changes in this file).

### Diff

```diff
 reduce(f, acc, xs) =
   (f, acc, []) -> acc |
   (f, acc, [x, ..rest]) -> reduce(f, apply_raw(f, [acc, x]), rest) |
-  (f, acc, xs) -> _reduce(f, acc, xs)
+  (f, acc, xs) -> _reduce_error(xs)
```

### Result (lines 112–116 after change)

```
@doc "Fold a list from left to right."
reduce(f, acc, xs) =
  (f, acc, []) -> acc |
  (f, acc, [x, ..rest]) -> reduce(f, apply_raw(f, [acc, x]), rest) |
  (f, acc, xs) -> _reduce_error(xs)
```

Arms 1 and 2 are unchanged. Arm 3 now calls `_reduce_error(xs)` with one argument
instead of `_reduce(f, acc, xs)` with three.

---

## 3. Change B — `src/genia/interpreter.py`

### B1 — Replace `reduce_fn` with `reduce_error_fn` (lines 7051–7060)

#### Before (lines 7051–7060)

```python
    def reduce_fn(f: Any, acc: Any, xs: Any) -> Any:
        """Host-backed reduce that calls the callback via invoke_callable with
        skip_none_propagation, so that list elements which are none(...)
        are passed to the callback rather than short-circuiting it."""
        if not isinstance(xs, list):
            raise TypeError(f"reduce expected a list as third argument, received {_runtime_type_name(xs)}")
        result = acc
        for x in xs:
            result = _invoke_raw_from_builtin(f, [result, x])
        return result
```

#### After (replaces lines 7051–7060 with 3 lines)

```python
    def reduce_error_fn(xs: Any) -> Any:
        raise TypeError(f"reduce expected a list as third argument, received {_runtime_type_name(xs)}")

```

The message template is identical to the `if not isinstance(xs, list)` branch of the old
`reduce_fn`. The list-iteration body (`result = acc` / `for x in xs` / `_invoke_raw_from_builtin`)
is removed — it was dead code in the arm-3 call path after issue #190.

The blank line after the function body is preserved to maintain the gap before `sum_fn` which
now starts at the line formerly occupied by line 7062.

### B2 — Swap env registration (line 7760)

#### Before (line 7760)

```python
    env.set("_reduce", reduce_fn)
```

#### After (line 7760, same position)

```python
    env.set("_reduce_error", reduce_error_fn)
```

The surrounding context (unchanged):

```python
    env.set("_sum", sum_fn)
    env.set("_reduce_error", reduce_error_fn)   # was: env.set("_reduce", reduce_fn)
    env.set("apply_raw", apply_raw_fn)
```

No other registrations change.

---

## 4. Change C — `docs/host-interop/capabilities.md`

### Location

Insert after line 372 (blank line closing the `fn.apply-raw` entry), before line 373
(`#### zip.write`).

### Inserted block (12 lines)

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

### Resulting section (lines 356–385 after insertion)

```markdown
### Group: Callable Invocation

Capabilities for invoking Genia callables with explicit control over none-propagation behavior.

#### `fn.apply-raw`

- **name:** `fn.apply-raw`
- **genia_surface:** `apply_raw(f, args)`
- **input:** `f` — any Genia callable; `args` — a Genia list of positional argument values
- **output:** whatever `f` returns when called with the elements of `args`
- **errors:**
  - `TypeError` with message `"apply_raw expected a list as second argument, received <type>"` — when `args` is not a Python list (covers: string, int, bool, map, and any other non-list value)
  - dispatch error from `invoke_callable` — when `f` is not callable or arity does not match
  - any exception raised inside `f` body — propagates unchanged through `apply_raw`
- **portability:** `language contract`
- **notes:** Calls `f` with `args` elements as positional arguments while skipping the automatic `none(...)` short-circuit. `none(...)` values inside `args` are delivered to `f` unchanged — the function body executes. The return value of `f` is returned as-is without coercion or wrapping. `apply_raw` itself is subject to ordinary none-propagation: if `args` is `none(...)` the call short-circuits before `apply_raw` runs. The prelude list HOFs `reduce`, `map`, and `filter` use `apply_raw` directly for callback invocation.

#### `fn.reduce-error`

- **name:** `fn.reduce-error`
- **genia_surface:** `_reduce_error(xs)` (internal — called from `reduce` arm 3 only)
- **input:** `xs` — any non-list Genia value (the erroneous third argument to `reduce`)
- **output:** never returns — always raises
- **errors:**
  - `TypeError` with message `"reduce expected a list as third argument, received <type-name>"` — always, for all inputs; `<type-name>` is the string produced by `_runtime_type_name(xs)`
- **portability:** `language contract`
- **notes:** Single-purpose error delegate called when `reduce`'s catch-all arm fires. Any host implementing `reduce` must raise this exact `TypeError`. The type-name vocabulary is shared across all `_runtime_type_name` usages. Not intended for direct user-code use.

#### `zip.write`
...
```

---

## 5. Files NOT Changed

| File | Reason |
|------|--------|
| `spec/eval/reduce-on-flow-type-error.yaml` | Error message unchanged — same template, same `_runtime_type_name` |
| `spec/flow/count-as-pipe-stage-type-error.yaml` | Same embedded message — unchanged |
| `tests/unit/test_dead_code_removal_182.py` | Existing tests guard the same TypeError message — must still pass |
| `tests/unit/test_list_hofs_190.py` | HOF regression suite unchanged |
| `GENIA_STATE.md` | `_reduce_error` is internal — no user-visible surface change |
| `docs/contract/semantic_facts.json` | No semantic facts reference `_reduce` or `_reduce_error` |

---

## 6. Spec Confirmation

### `spec/eval/reduce-on-flow-type-error.yaml`

```yaml
name: reduce-on-flow-type-error
category: eval
input:
  source: |
    acc(a, b) = a
    reduce(acc, 0, tick(3))
expected:
  stdout: ""
  stderr: |
    Error: reduce expected a list as third argument, received flow
  exit_code: 1
```

**Trace after change:**
1. `reduce(acc, 0, tick(3))` is called; `xs = tick(3)` (a `GeniaFlow`)
2. Arm 1: `tick(3)` does not match `[]` — skip
3. Arm 2: `tick(3)` does not match `[x, ..rest]` — skip
4. Arm 3: catch-all fires; calls `_reduce_error(tick(3))`
5. `reduce_error_fn(tick(3))` executes: `_runtime_type_name(tick(3))` → `"flow"`
6. Raises `TypeError("reduce expected a list as third argument, received flow")`
7. Interpreter normalizes to `stderr: "Error: reduce expected a list as third argument, received flow"`, `exit_code: 1`

Result: **spec passes unchanged** ✓

### `spec/flow/count-as-pipe-stage-type-error.yaml`

The embedded error fragment `"reduce expected a list as third argument, received flow"` is
produced by the same path (arm 3 → `_reduce_error`). **Spec passes unchanged** ✓

---

## 7. Implementation Order

Within a single commit:

1. Edit `src/genia/std/prelude/list.genia` line 116
2. Edit `src/genia/interpreter.py` — replace `reduce_fn` with `reduce_error_fn` (lines 7051–7060)
3. Edit `src/genia/interpreter.py` — swap env registration (line 7760)
4. Edit `docs/host-interop/capabilities.md` — insert `fn.reduce-error` entry

Steps 1–3 must be in the same commit to avoid a window where the prelude calls
`_reduce_error` before it is registered (or `_reduce` is unregistered before the
prelude no longer calls it).

---

## 8. Exact Next Claude Prompt (Test Phase)

```
Read AGENTS.md, GENIA_STATE.md, GENIA_RULES.md, GENIA_REPL_README.md, README.md.
GENIA_STATE.md is final authority.

Issue: #196 — Pre-flight and resolve _reduce fallthrough behavior
Branch: issue-reduce-fallthrough-analysis
Phase: TEST

Context: Design is at docs/architecture/issue-196-reduce-fallthrough-design.md.
The design adds _reduce_error(xs) as a 1-arg host primitive, replaces the reduce arm-3 call,
removes reduce_fn and its _reduce env registration.

Scope:
- Write failing tests for the new _reduce_error primitive BEFORE implementation.
- Tests must verify:
  (a) _reduce_error(flow_value) raises TypeError with message
      "reduce expected a list as third argument, received flow"
  (b) _reduce_error("string") raises TypeError with "... received string"
  (c) _reduce_error(42) raises TypeError with "... received int"
  (d) reduce(f, acc, non_list) routes through _reduce_error and produces the same error
  (e) _reduce is no longer registered in the env after the change (negative test)
- Tests must be in a new test file or clearly marked section, consistent with the
  existing test style in tests/unit/test_dead_code_removal_182.py.
- Tests must FAIL before implementation (confirm this is achievable given _reduce_error
  does not yet exist).

Scope excludes:
- Do not implement changes yet.
- Do not edit list.genia, interpreter.py, or capabilities.md in this phase.
- Do not change existing spec YAML files.

Output: new test file (or additions) committed with a failing-test note.
Commit: test(reduce): failing tests for _reduce_error primitive issue #196
```
