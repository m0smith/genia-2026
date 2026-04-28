# Design: Prelude-safe callback invocation — `apply_raw`

Issue: #188
Phase: design
Branch: issue-188-raw-callback-invocation-design
Date: 2026-04-28

Preflight: `docs/architecture/issue-188-callbacks-preflight.md`
Spec: `docs/architecture/issue-188-callbacks-spec.md`

---

## 1. Purpose

Translate the spec for `apply_raw(f, args)` into a concrete structure for implementation. No code is written here.

---

## 2. Scope Lock

Follows the spec exactly. Does not add behavior, does not expand scope.

### Included

- `apply_raw_fn` Python function definition in `src/genia/interpreter.py`
- `env.set("apply_raw", apply_raw_fn)` registration in `setup_env()`
- Error messages for invalid `args` type

### Excluded

- Parser changes (none needed; `apply_raw` is an ordinary named call)
- New Core IR nodes (none needed; lowers as `IrCall(IrVar("apply_raw"), ...)`)
- Changes to `_NONE_AWARE_PUBLIC_FUNCTIONS`
- Changes to `_invoke_raw_from_builtin` (unchanged, still used by `_reduce`/`_map`/`_filter`)
- Prelude migration of `reduce`, `map`, `filter` (blocked on #188 landing; separate issue)
- Any change to normal function call semantics
- Any change to `invoke_callable` signature

---

## 3. Architecture Overview

### Where it fits

`apply_raw` lives at the same layer as the existing metacircular `apply`:

```
Genia source
    ↓  parse + lower
IrCall(IrVar("apply_raw"), [f_node, args_node])
    ↓  eval
apply_raw_fn(proc, args)          ← NEW: defined in setup_env()
    ↓
invoke_callable(proc, args, skip_none_propagation=True)
    ↓
function body executes with none args intact
```

Contrast with the existing metacircular `apply`:

```
apply(proc, args)
    ↓  fn.genia prelude → apply_dispatch → _meta_host_apply
meta_host_apply_fn(proc, args)    ← existing, unchanged
    ↓
invoke_callable(proc, args, skip_none_propagation=False)  ← none propagation still active
```

`apply_raw` is a distinct named primitive — it is not a variant of `apply`.

### Components involved

| Component | Role | Change |
|---|---|---|
| `src/genia/interpreter.py` — `setup_env()` | Defines and registers all host-backed callables | Two additions: function def + `env.set` |
| `invoke_callable` | Performs the actual call dispatch | Unchanged; already has `skip_none_propagation` param |
| `_invoke_raw_from_builtin` | Internal closure used by `_map`/`_filter`/`_reduce` | Unchanged |
| Prelude files (`list.genia`) | Thin wrappers over `_map`/`_filter`/`_reduce` | Unchanged in this phase |
| Parser / Core IR lowering | Handles `IrCall` nodes | Unchanged |

---

## 4. File / Module Changes

### Modified files

**`src/genia/interpreter.py`** — two additions, zero deletions:

1. **`apply_raw_fn` definition** — new nested function inside `setup_env()`, placed immediately after `_invoke_raw_from_builtin` (currently ending around line 6906).

2. **`env.set("apply_raw", apply_raw_fn)`** — registration line, placed in the same `setup_env()` block near the `_reduce`/`_map`/`_filter` registrations (currently around line 7763–7765).

### New files

None.

### Removed files

None.

---

## 5. Data Shapes

### `apply_raw_fn` signature (Python)

```
apply_raw_fn(proc: Any, args: Any) -> Any
```

- `proc` — any value; if non-callable, `invoke_callable` raises its own dispatch error
- `args` — must be a Python list; if not, `apply_raw_fn` raises `TypeError`
- return — whatever `invoke_callable` returns (no wrapping)

### Genia surface

```
apply_raw(f, args)
```

- `f` — any Genia callable
- `args` — a Genia list whose elements are the positional arguments
- fixed arity: 2

---

## 6. Function / Interface Design

### `apply_raw_fn(proc, args)` — new function inside `setup_env()`

**Parameters:**
- `proc: Any` — the callable to invoke
- `args: Any` — expected to be a Python list of Genia runtime values

**Returns:** the result of calling `proc` with `args` elements as positional arguments

**Behavior:**
1. If `args` is not a Python `list`, raise `TypeError` with message:
   `"apply_raw expected a list as second argument, received <runtime_type_name(args)>"`
2. Call `Evaluator(env, env.debug_hooks, env.debug_mode).invoke_callable(proc, args, tail_position=False, callee_node=None, skip_none_propagation=True)`
3. Return the result unchanged

**Does NOT:**
- Pre-validate `proc` as callable (delegated to `invoke_callable`)
- Unwrap or transform any argument values
- Catch exceptions from `invoke_callable`

### Pattern: consistent with existing `_invoke_raw_from_builtin`

`apply_raw_fn` is the Genia-visible equivalent of the private `_invoke_raw_from_builtin`. The only structural difference is that `apply_raw_fn` validates that `args` is a list (since it's a user-facing primitive) and is registered in the public env by a clean name.

---

## 7. Control Flow

```
eval(IrCall(IrVar("apply_raw"), [f_node, args_node]))
  │
  ├─ evaluate f_node  →  proc (any value)
  ├─ evaluate args_node  →  args_val (any value)
  │
  └─ call apply_raw_fn(proc, args_val)
        │
        ├─ if not isinstance(args_val, list):
        │     raise TypeError("apply_raw expected a list ...")
        │
        └─ Evaluator.invoke_callable(proc, args_val,
                                     tail_position=False,
                                     callee_node=None,
                                     skip_none_propagation=True)
                │
                ├─ [none-propagation check SKIPPED]
                │
                ├─ dispatch on proc type (GeniaFunctionGroup / GeniaFunction / lambda / builtin / ...)
                │
                └─ body executes with args_val elements as positional bindings
                        │
                        └─ return result unchanged
```

Key decision point: the `skip_none_propagation=True` flag suppresses the early-return guard at the top of `invoke_callable`. All other dispatch logic (arity, patterns, tail-call trampoline) is unchanged.

---

## 8. Error Handling Design

| Error condition | Detected at | Message format | Python exception type |
|---|---|---|---|
| `args` is not a list | `apply_raw_fn`, before `invoke_callable` | `"apply_raw expected a list as second argument, received <type>"` | `TypeError` |
| `proc` is not callable | `invoke_callable`, during dispatch | Existing dispatch error (unchanged) | `TypeError` |
| Arity mismatch | `invoke_callable`, arity resolution | Existing dispatch error (unchanged) | `TypeError` |
| Runtime error inside `proc` | Propagates from `invoke_callable` | Unchanged (re-raised) | whatever the body raises |

The `_runtime_type_name` helper (already defined in the file) provides the `<type>` string used in the `args` error message.

---

## 9. Integration Points

### `invoke_callable` — unchanged

`invoke_callable` already has `skip_none_propagation: bool = False`. `apply_raw_fn` passes `True`. No changes to `invoke_callable` itself.

### `_invoke_raw_from_builtin` — unchanged

The private `_invoke_raw_from_builtin` closure continues to serve `_map`/`_filter`/`_reduce`. It is not replaced or removed. `apply_raw_fn` and `_invoke_raw_from_builtin` are parallel implementations of the same mechanism for different audiences (public vs. private).

### `_NONE_AWARE_PUBLIC_FUNCTIONS` — unchanged

`apply_raw` does NOT need to be added to this set. The none-propagation check fires on the arguments passed to `apply_raw` itself, which are `(callable, list)`. The list value `[none("x")]` is not a `GeniaOptionNone` — it is a Python `list` — so the short-circuit guard never fires on `apply_raw`'s own invocation.

### Autoload system — not used

`apply_raw` is registered with `env.set(...)` (direct binding), not `env.register_autoload(...)`. It is a host-backed primitive available immediately, same as `force`, `print`, `cons`, etc.

### help system

`apply_raw` will appear as a raw host-backed name. `help("apply_raw")` will produce the generic bridge note (same as other direct-set names). A docstring can be added via the prelude in a later docs phase if desired.

---

## 10. Test Design Input (for test phase)

The test phase must cover these invariants from the spec:

| Invariant | Test approach |
|---|---|
| Raw invocation | Call with none arg where body unwraps it; assert result ≠ none |
| Ordinary-value equivalence | Call with plain args; assert same result as direct call |
| Exception propagation | Call with body that raises; assert exception propagates |
| Normal call unchanged | Direct call with none arg still short-circuits (regression) |
| No implicit coercion | Identity lambda returns none unchanged |
| `args` not a list → TypeError | Pass a non-list second arg; assert TypeError with correct message |
| `proc` not callable → dispatch error | Pass non-callable first arg; assert TypeError |
| Zero-arg via empty list | `apply_raw(() -> 42, [])` → `42` |
| Named function as proc | Named function works the same as lambda |
| Lambda as proc | Lambda works as first argument |

Existing `reduce_none_propagation.genia` case must continue to pass without any change (regression guard).

Shared YAML spec cases from the spec phase (`spec/eval/apply-raw-*.yaml`) serve as the conformance contract.

---

## 11. Doc Impact

Docs to update in the doc phase (not now):

- `GENIA_STATE.md`: add `apply_raw` to the builtin surface table; document the none-bypass contract; mark as language-contract primitive
- `GENIA_RULES.md` §9.6.4: add sub-clause on `apply_raw` as the explicit raw-call mechanism
- `GENIA_REPL_README.md`: add `apply_raw` to builtins list
- `README.md`: update builtins section; add `apply_raw` alongside `apply` / `compose`
- `docs/host-interop/capabilities.md`: add `apply_raw` as a required host capability
- `spec/eval/README.md`: already updated in spec phase

---

## 12. Constraints

**Follows existing patterns:**
- Parallel structure to `meta_host_apply_fn` / `_meta_host_apply` (same `invoke_callable` call, different `skip_none_propagation`)
- Registered with `env.set(...)` like all other host-backed primitives
- Error messages use `_runtime_type_name(...)` like all other type guards in `setup_env()`

**Preserves minimalism:**
- Two lines of change: one function definition, one `env.set` call
- No new IR nodes, no new parser rules, no new prelude files

**Avoids unnecessary abstraction:**
- `apply_raw_fn` is a thin function; all real logic is already inside `invoke_callable`

---

## 13. Complexity Check

[x] Minimal — two additions to one file; all logic already exists via `invoke_callable`'s `skip_none_propagation` parameter

**Explanation:** The mechanism already exists (`_invoke_raw_from_builtin` uses it internally). This design makes that mechanism publicly accessible under a clean name. The only new code is a validation guard on the `args` argument and the `env.set` registration.

---

## 14. Final Check

- [x] Matches spec exactly — `apply_raw(f, args)` with list args, no coercion, exceptions propagate
- [x] No new behavior introduced — normal calls and `_reduce`/`_map`/`_filter` are unchanged
- [x] Structure is clear and implementable — one function, one registration
- [x] Ready for implementation without ambiguity
