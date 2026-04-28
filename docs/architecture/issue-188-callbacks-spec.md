# Spec: Prelude-safe callback invocation — `apply_raw`

Issue: #188
Phase: spec
Branch: issue-188-raw-callback-invocation-spec
Date: 2026-04-28

---

## 1. Change Name

Prelude-safe callback invocation without automatic none propagation.

---

## 2. Observable Behavior Contract

### 2.1 Signature

```genia
apply_raw(f, args)
```

- `f` — any Genia callable (named function, lambda, or prelude wrapper)
- `args` — a list of runtime values; each element becomes a positional argument to `f`

### 2.2 Core Semantics

`apply_raw(f, args)` invokes `f` with the elements of `args` as positional arguments.

**Bypassed**: automatic `none(...)` propagation that normally short-circuits an ordinary function call when any argument is `none(...)` and the callee does not explicitly handle absence.

**Not bypassed**: everything else — arity dispatch, pattern matching, runtime exceptions, type errors.

### 2.3 Invariants

| Invariant | Description |
|---|---|
| Raw invocation | `apply_raw(f, args)` always reaches the function body regardless of whether any element of `args` is `none(...)` |
| Ordinary-value equivalence | When no element of `args` is `none(...)`, the result is identical to a direct call `f(args[0], args[1], ...)` |
| Exception propagation | Runtime errors raised inside `f`'s body propagate normally through `apply_raw` |
| Normal call unchanged | Existing ordinary calls (`f(x)`, `f(x, y)`, etc.) are unaffected by this primitive |
| No implicit coercion | `apply_raw` does not unwrap `some(...)` or transform absence values before passing them to `f` |
| Return value as-is | The return value of `f` is returned unchanged (no re-wrapping into `some(...)`) |

### 2.4 Relation to Normal Function Calls

Normal call behavior (unchanged):
```genia
f = (x) -> x + 1
f(none("q"))           # → none("q")  (short-circuited; body not called)
```

`apply_raw` behavior:
```genia
f = (x) -> x + 1
apply_raw(f, [none("q")])  # → none("q")  (body called; x + 1 where x = none("q");
                           #                + propagates none since + is not none-aware)
```

The difference is observable only when `f`'s body handles `none(...)` explicitly and produces a non-none result:

```genia
step = (acc, x) -> acc + unwrap_or(0, x)
step(5, none("q"))              # → none("q")  (short-circuited)
apply_raw(step, [5, none("q")]) # → 5          (body executes; unwrap_or handles none)
```

### 2.5 Error Cases

| Condition | Behavior |
|---|---|
| `f` is not callable | `TypeError` raised; `apply_raw` does not suppress it |
| `args` is not a list | `TypeError` raised |
| Arity mismatch | Unmatched dispatch error raised (same as ordinary call) |
| Runtime error inside `f` | Propagates unchanged |

### 2.6 Portability Requirement

`apply_raw` is a **host-backed primitive**. Every host must provide it as a named callable in the root environment with the semantics above.

Python host: implemented as a thin wrapper over `invoke_callable(..., skip_none_propagation=True)`.

Future hosts: must implement equivalent bypass of their none-propagation short-circuit.

### 2.7 Host Capability Classification

- **Language contract**: yes — `apply_raw` is part of the portable language surface
- **Core IR**: `apply_raw(f, args)` lowers as `IrCall(IrVar("apply_raw"), [f, args])`; no new IR node needed
- **Host substrate**: yes — each host provides the backing implementation
- **Prelude helper**: no — `apply_raw` is a primitive, not a prelude-composed helper

### 2.8 Motivation: Enabling Prelude Extraction

After `apply_raw` exists as a language primitive, `reduce`, `map`, and `filter` can be rewritten as pure Genia prelude functions:

```genia
reduce_impl(f, acc, []) = acc
reduce_impl(f, acc, [x, ..rest]) = reduce_impl(f, apply_raw(f, [acc, x]), rest)
```

```genia
map_impl(f, []) = []
map_impl(f, [x, ..rest]) = [apply_raw(f, [x])] + map_impl(f, rest)
```

```genia
filter_impl(pred, []) = []
filter_impl(pred, [x, ..rest]) =
  apply_raw(pred, [x]) == true -> [x] + filter_impl(pred, rest) |
  _ -> filter_impl(pred, rest)
```

The Python builtins `_reduce`, `_map`, `_filter` can then be retired.

---

## 3. Shared Spec Cases

### 3.1 Positive Cases (eval category)

| File | Description | Expected stdout |
|---|---|---|
| `apply-raw-basic-ordinary-value.yaml` | apply_raw with clean args = normal call | `42\n` |
| `apply-raw-none-arg-body-executes.yaml` | lambda with unwrap_or receives none; body runs | `0\n` |
| `apply-raw-none-multi-arg.yaml` | two-arg step fn; none in second position; body handles it | `5\n` |
| `apply-raw-lambda-identity-none.yaml` | identity lambda with none arg returns none | `none("y")\n` |
| `apply-raw-empty-args.yaml` | zero-arg function via apply_raw | `42\n` |
| `apply-raw-contrast-normal-call.yaml` | same step fn called normally with none short-circuits | `none("q")\n` |

### 3.2 Error Cases (error category)

Error YAML cases require exact `stderr` matching. The exact messages are defined during the implementation phase. Error behavior is covered by the invariants in §2.5 and will produce test cases in the test phase.

---

## 4. Scope Locks

### What this spec covers

- Observable behavior of `apply_raw(f, args)`
- Shared YAML cases proving the core invariants
- Host portability classification
- Path to enabling prelude extraction of `reduce`/`map`/`filter`

### What this spec does NOT cover

- Implementation of `apply_raw` in the Python host (design/implementation phases)
- Migration of `reduce`, `map`, `filter` to prelude (separate extraction issue under #117)
- Changes to normal function call behavior
- Any new parser syntax
- Any new Core IR node (not needed; `apply_raw` lowers as `IrCall`)

---

## 5. Phase Sign-off

- GO for design phase
- Recommended next branch: `issue-188-raw-callback-invocation-design`
- Recommended commit message: `design(callbacks): plan apply_raw implementation for issue #188`
