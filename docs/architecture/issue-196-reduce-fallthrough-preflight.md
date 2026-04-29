# Pre-flight: `_reduce` Fallthrough Behavior Analysis

**Issue:** #196
**Phase:** preflight
**Branch:** issue-reduce-fallthrough-analysis
**Date:** 2026-04-29

---

## 1. Scope Lock

**In scope:**
- All `_reduce` call sites in prelude, interpreter, and host/runtime code
- When and how the `_reduce` fallthrough arm in `reduce` is triggered
- Whether `_reduce` handles Flow values, non-list values, or other special shapes
- Recommendation: KEEP / REMOVE / REPLACE
- Minimal set of phases needed to resolve

**Out of scope:**
- Do not change reduce semantics for lists
- Do not modify pairs, map, or filter
- Do not introduce new APIs
- Do not implement changes in this phase

---

## 2. Current Known Behavior

### The three-arm `reduce` in `src/genia/std/prelude/list.genia:113-116`

```genia
reduce(f, acc, xs) =
  (f, acc, []) -> acc |
  (f, acc, [x, ..rest]) -> reduce(f, apply_raw(f, [acc, x]), rest) |
  (f, acc, xs) -> _reduce(f, acc, xs)
```

- **Arm 1** `(f, acc, [])`: xs is the empty list — returns `acc` immediately.
- **Arm 2** `(f, acc, [x, ..rest])`: xs is a non-empty list — recurses via `apply_raw`.
- **Arm 3** `(f, acc, xs)` (catch-all): xs is anything that did NOT match `[]` or `[head, ..tail]`, i.e., a **non-list value**. Delegates to the Python-backed `_reduce`.

Arms 1 and 2 together exhaust all list shapes. **Arm 3 is reached exclusively for non-list inputs.**

### The Python `reduce_fn` registered as `_reduce` (`interpreter.py:7051-7060`)

```python
def reduce_fn(f: Any, acc: Any, xs: Any) -> Any:
    if not isinstance(xs, list):
        raise TypeError(
            f"reduce expected a list as third argument, received {_runtime_type_name(xs)}"
        )
    result = acc
    for x in xs:
        result = _invoke_raw_from_builtin(f, [result, x])
    return result
```

- When called from arm 3, `xs` is NEVER a list (arms 1 and 2 consumed all list cases).
- `isinstance(xs, list)` is always `False` from the prelude call path.
- `_reduce` **always raises `TypeError`** when invoked from the prelude catch-all.
- The list-iterating body (`for x in xs`) is **dead code** in the prelude call path.

### Error message

`_reduce` calls `_runtime_type_name(xs)` to produce the type name string, yielding:
```
TypeError: reduce expected a list as third argument, received <type-name>
```
where `<type-name>` is e.g. `flow`, `string`, `int`, `bool`, `map`, `some(...)`, `none(...)`.

---

## 3. Files Inspected

| File | Purpose |
|------|---------|
| `src/genia/std/prelude/list.genia:113-116` | Genia `reduce` — the three-arm definition containing the fallthrough |
| `src/genia/interpreter.py:7051-7060` | Python `reduce_fn` — registered as `_reduce` |
| `src/genia/interpreter.py:7760` | `env.set("_reduce", reduce_fn)` — env registration |
| `src/genia/interpreter.py:6897-6906` | `_invoke_raw_from_builtin` — used by `reduce_fn` for callback invocation |
| `src/genia/interpreter.py:5156ff` | `_runtime_type_name` — produces the type-name string in the error message |
| `spec/eval/reduce-on-flow-type-error.yaml` | Shared spec asserting exact error message for flow input |
| `spec/flow/count-as-pipe-stage-type-error.yaml` | Flow spec embedding the reduce error message |
| `tests/unit/test_dead_code_removal_182.py:135-156` | `TestReduceRegression` — guards `_reduce` path (non-list error, none-delivery) |
| `tests/unit/test_list_hofs_190.py` | HOF regression tests |
| `docs/architecture/issue-182-contract.md` | Documented blocker: `_reduce` cannot be removed without Genia-native error primitive |
| `docs/architecture/issue-182-preflight.md` | Item B analysis: blocker for replacing `_reduce` catch-all |
| `docs/architecture/issue-190-list-hofs-design.md` | Design choice: retain `_reduce` in arm 3 for error-message preservation |
| `docs/architecture/issue-190-list-hofs-audit.md` | Audit confirms `_reduce` retained; removal deferred to issue related to #181 |
| `docs/architecture/issue-195-preflight.md` | Confirms `_reduce` is NOT in scope for `_map`/`_filter` dead-code cleanup |
| `docs/host-interop/capabilities.md:371` | `apply_raw` notes (references prelude HOFs; no longer mentions `_reduce` motivation) |

---

## 4. All `_reduce` References Found

### Active call site

| Location | Kind | Notes |
|----------|------|-------|
| `src/genia/std/prelude/list.genia:116` | Genia call `_reduce(f, acc, xs)` | The only active call; arm 3 catch-all |
| `src/genia/interpreter.py:7760` | `env.set("_reduce", reduce_fn)` | Only registration |

### Test references

| Location | Kind |
|----------|------|
| `tests/unit/test_dead_code_removal_182.py:149-152` | Guards exact `TypeError` message via `_reduce` catch-all |
| `tests/unit/test_dead_code_removal_182.py:154-156` | Guards `none(...)` element delivery (applies to normal list path, not arm 3) |
| `tests/unit/test_list_hofs_190.py:3` | Module docstring — historical description only, not a live call |

### Spec assertions that depend on the error message produced by `_reduce`

| File | Assertion |
|------|-----------|
| `spec/eval/reduce-on-flow-type-error.yaml` | `stderr: Error: reduce expected a list as third argument, received flow` |
| `spec/flow/count-as-pipe-stage-type-error.yaml` | Embeds the same message in a pipeline-stage error |

### Documentation references (historical/explanatory)

`docs/architecture/issue-182-contract.md`, `issue-182-preflight.md`, `issue-182-design.md`,
`issue-182-audit.md`, `issue-190-list-hofs-preflight.md`, `issue-190-list-hofs-design.md`,
`issue-190-list-hofs-audit.md`, `issue-190-list-hofs-spec.md`, `issue-188-callbacks-design.md`,
`issue-188-callbacks-preflight.md`, `issue-162-value-flow-classification-impl.md`,
`issue-195-preflight.md`, `issue-195-audit.md`.

---

## 5. Suspected Trigger Paths

### When arm 3 fires

Arm 3 fires whenever `reduce` is called with `xs` matching neither `[]` nor `[head, ..tail]`:

| Input type | Example | Arm 3 fires? | `_reduce` raises |
|------------|---------|--------------|-----------------|
| Flow | `tick(3)` | YES | `TypeError: ... received flow` |
| String | `"hello"` | YES | `TypeError: ... received string` |
| Integer | `42` | YES | `TypeError: ... received int` |
| Map | `{a: 1}` | YES | `TypeError: ... received map` |
| Boolean | `true` | YES | `TypeError: ... received bool` |
| `none(...)` | `none("x")` | YES | `TypeError: ... received none(string)` |
| `some(...)` | `some([1,2])` | YES | `TypeError: ... received some(list)` |
| `[]` | empty list | NO (arm 1) | — |
| `[x, ..rest]` | non-empty list | NO (arm 2) | — |

### Does `_reduce` handle Flow specially?

**No.** `reduce_fn` checks `isinstance(xs, list)`. A Flow value is not a Python `list`. The check fails immediately and `TypeError` is raised. There is no special-casing for Flow, no unwrapping, no traversal attempt.

### Does the list-body of `reduce_fn` ever execute from the prelude call?

**No.** When arm 3 calls `_reduce(f, acc, xs)`, `xs` is a non-list by definition. `reduce_fn` raises `TypeError` before reaching the `for` loop. The iteration body is unreachable from the arm-3 call path.

---

## 6. Risks and Ambiguity

### R1 — Exact error message is a pinned contract

The message `"reduce expected a list as third argument, received <type>"` is asserted verbatim by:
- `spec/eval/reduce-on-flow-type-error.yaml`
- `spec/flow/count-as-pipe-stage-type-error.yaml`
- `tests/unit/test_dead_code_removal_182.py:151`

Any replacement mechanism **must reproduce the exact type-name strings** produced by `_runtime_type_name`.

### R2 — No Genia-native type-name or error-raise primitive currently exists

As documented in `issue-182-contract.md §Item B`, Genia currently has no:
- `type_name(value)` primitive returning the runtime type name as a string
- General `raise_type_error(message)` primitive callable from Genia

`_cli_type_error(message)` raises `TypeError(message)` but is CLI-specific, takes only a pre-formatted string, and cannot produce the type name.

This is the only blocker preventing removal of `_reduce`.

### R3 — `reduce_fn`'s list-iteration body creates false impression

`reduce_fn` contains a working list-iteration loop. This may mislead a reader into thinking `_reduce` is called for lists. It is not — in the current prelude, arm 3 only fires for non-lists. The list body is dead code in the arm-3 path. It was present before #190 (when `reduce` fully delegated to `_reduce`) and was never removed.

### R4 — Scope boundary with issue #183 (`pairs`)

Issue #183 is next in line after #195. Issue #196 (this pre-flight) was explicitly raised to resolve the `_reduce` question before #183 continues. #183 (`pairs(xs, ys)`) does not depend on `_reduce` behavior. These are orthogonal concerns. No blocking dependency.

### R5 — `_reduce` registration name is not `reduce`

`env.set("_reduce", reduce_fn)` uses the underscore-prefixed internal name. No Genia user code calls `_reduce` directly. The only consumer is `list.genia:116`.

---

## 7. Recommended Next Phase

### Recommendation: REPLACE — introduce a minimal host primitive to remove the `_reduce` dependency

**Rationale:** `_reduce` serves a single purpose in the current codebase: raising a `TypeError` with a formatted type-name string. The list-body of `reduce_fn` is dead code in the arm-3 call path. The only real need is:
1. A way to get `_runtime_type_name(xs)` as a Genia string value, OR
2. A way to call a host function that raises `TypeError` with a formatted message.

Option A — Add `type_name(value)` host primitive returning a string:
- Genia arm 3 becomes: `(f, acc, xs) -> _reduce_type_error(type_name(xs))`
- Or, with a general raise: `(f, acc, xs) -> raise_type_error("reduce expected a list as third argument, received " ++ type_name(xs))`
- Requires one new primitive: `type_name(value)` (or `_type_name`)
- Impact: single new host-backed primitive; no new language feature

Option B — Add a `_reduce_type_error(type_name_string)` host primitive:
- Calls `_runtime_type_name` Python-side and raises `TypeError`
- `_reduce` becomes: `_reduce_type_error` (single-purpose, named correctly)
- Genia arm 3: `(f, acc, xs) -> _reduce_type_error(xs)` or `_reduce_type_error(type_name(xs))`

**Minimum viable path:** contract and design a new host primitive (`type_name` or `_reduce_type_error`), then replace arm 3 in prelude and remove `_reduce` registration. Test against pinned spec assertions.

**Required phases for resolution:**
1. `contract` — define the primitive name, input/output shape, and behavior guarantee
2. `design` — minimal implementation in `interpreter.py`; spec for error assertion
3. `test` — failing test confirming the new primitive works and existing specs still pass
4. `implementation` — add primitive; update `list.genia` arm 3; remove `env.set("_reduce", ...)`
5. `docs` — update `capabilities.md`; update `GENIA_STATE.md`
6. `audit` — verify all specs pass and `_reduce` is gone

---

## 8. Go / No-Go

**GO** to proceed to contract phase.

Conditions:
- The fallthrough arm behavior is fully understood: arm 3 fires for all non-list inputs and always raises `TypeError`.
- `_reduce` does NOT handle Flow specially.
- `_reduce` does NOT handle lists when invoked from the arm-3 call path.
- The only blocker (no Genia-native type-name primitive) is addressable in a single targeted contract/design/test/implementation cycle.
- No ambiguity remains.

---

## 9. Exact Next Claude Prompt

```
Read AGENTS.md, GENIA_STATE.md, GENIA_RULES.md, GENIA_REPL_README.md, README.md.
GENIA_STATE.md is final authority.

Issue: #196 — Pre-flight and resolve _reduce fallthrough behavior
Branch: issue-reduce-fallthrough-analysis
Phase: CONTRACT

Context: Pre-flight `docs/architecture/issue-196-reduce-fallthrough-preflight.md` is complete and
confirmed GO. The _reduce fallthrough arm in `src/genia/std/prelude/list.genia:116` is a non-list
error-path delegate. Its only role is raising TypeError with the exact message:
  "reduce expected a list as third argument, received <type>"
Removal requires a Genia-accessible type-name primitive.

Scope:
- Contract a single new host primitive: `type_name(value)` returning the runtime type name as a
  string, OR an equivalent minimal mechanism to replace the arm-3 `_reduce(f, acc, xs)` call.
- Define: primitive name, arity, input/output contract, error behavior, portability status.
- Define: exact new form of reduce arm 3 using the new primitive.
- Define: what changes in interpreter.py (registration), list.genia (arm 3), and capabilities.md.
- Confirm: the exact error message "reduce expected a list as third argument, received <type>"
  remains unchanged in spec/eval/reduce-on-flow-type-error.yaml and
  spec/flow/count-as-pipe-stage-type-error.yaml.

Scope excludes:
- Do not implement — write contract only.
- Do not change list, map, filter, pairs, or any other prelude behavior.
- Do not add new language features beyond the minimal primitive needed.

Output: contract document at docs/architecture/issue-196-reduce-fallthrough-contract.md.
Commit: contract(reduce): define type_name primitive to replace _reduce catch-all issue #196
```
