# === GENIA PRE-FLIGHT ===

CHANGE NAME: Prelude-safe callback invocation without automatic none propagation

Issue: #188
Branch: issue-188-raw-callback-invocation-preflight
Date: 2026-04-28

---

## 1. SCOPE LOCK

### Includes

- Inspect current `none(...)` propagation semantics in `invoke_callable`
- Inspect current Python raw callback invocation via `_invoke_raw_from_builtin`
- Identify where `_invoke_raw_from_builtin(..., skip_none_propagation=True)` is used
- Explain why `reduce`, `map`, and `filter` cannot currently move to pure prelude
- Evaluate whether this needs new language syntax, Core IR support, or a minimal prelude-visible primitive
- Recommend smallest safe next step

### Does NOT include

- Implementation
- Tests
- Docs sync beyond this preflight artifact
- Changing function-call behavior
- Moving `reduce`/`map`/`filter` to prelude
- Changing Option semantics globally
- Redesigning absence semantics
- Adding new syntax (unless later spec explicitly approves it)

---

## 2. SOURCE OF TRUTH SUMMARY

### GENIA_STATE.md (final authority)

- `invoke_callable` has `skip_none_propagation: bool = False`; when `False`, any `none(...)` argument short-circuits the call unless the callee explicitly handles none.
- `_NONE_AWARE_PUBLIC_FUNCTIONS` is a frozen registry of names that are exempt from short-circuit.
- `_callable_explicitly_handles_none()` performs the detection: attribute flag, name registry, or pattern-body inspection.
- `_reduce`, `_map`, `_filter` are Python builtins registered directly into the env; they use `_invoke_raw_from_builtin` internally.
- `reduce`, `map`, `filter` in `list.genia` are thin prelude wrappers that immediately delegate to those Python builtins.
- There is no Genia-level primitive for raw invocation.
- Core IR portability boundary is `docs/architecture/core-ir-portability.md`; host-local nodes are not part of the shared contract.

### AGENTS.md

- Change must follow: preflight → spec → design → test → implementation → docs → audit
- Each phase is a separate commit; do not cross phase boundaries
- A change should affect only ONE zone; if it crosses zones, split into multiple steps
- The four zones are: Language Contract, Core IR, Host Adapters, Docs/Tests/Examples

### GENIA_RULES.md

- Section 9.6.4: ordinary functions short-circuit on `none(...)` arguments unless the callee explicitly handles absence
- Section 11.2: `map_some(f, opt)` applies `f` to the inner value; this is an Option-aware helper, not a raw-call mechanism
- The language contract and the host substrate must not redefine each other

### Issue #188

Goal: introduce a portable, language-level mechanism to invoke functions without automatic `none(...)` propagation, unblocking extraction of `reduce`, `map`, and `filter` from Python into Genia prelude.

### Issue #117

Goal: extract pure runtime helpers from Python into prelude. `reduce`, `map`, and `filter` are extraction candidates but are blocked pending #188.

### Issue #181

Inventory of pure Python helpers for prelude extraction; classified `reduce`/`map`/`filter` as "maybe later / blocked" due to the `skip_none_propagation` dependency.

### Issue #182

First extraction batch (collection and option helpers). Must NOT include `reduce`, `map`, or `filter` until #188 is resolved.

---

## 3. CURRENT BEHAVIOR INSPECTION

### 3.1 Normal function call with `none(...)` argument

```
invoke_callable(fn, args, ...)
  if not skip_none_propagation:
    first_none = next(arg for arg in args if is_none(arg))
    if first_none is not None and not _callable_explicitly_handles_none(fn, ...):
      return first_none   # short-circuit; body never runs
```

**Example**: `f(x) = x + 1`; calling `f(none("x"))` returns `none("x")` without calling the body.

### 3.2 None-aware detection (`_callable_explicitly_handles_none`)

A callee bypasses short-circuit if any of:
1. It has `__genia_handles_none__ = True` (Python attribute, host-only)
2. Its name is in `_NONE_AWARE_PUBLIC_FUNCTIONS` (hard-coded frozenset, host-only)
3. Its body pattern-matches on `none(...)` or `some(...)` patterns (inspectable at call time)
4. Its body delegates directly to a name in `_NONE_AWARE_PUBLIC_FUNCTIONS`

A lambda like `(o) -> unwrap_or(0, o)` escapes short-circuit because its body delegates to `unwrap_or`, which is in `_NONE_AWARE_PUBLIC_FUNCTIONS`. This is currently host-specific analysis.

### 3.3 `_invoke_raw_from_builtin`

Location: `src/genia/interpreter.py` (nested inside `setup_env()`)

```python
def _invoke_raw_from_builtin(proc: Any, args: list[Any]) -> Any:
    """Like _invoke_from_builtin but skips none-propagation."""
    return Evaluator(env, env.debug_hooks, env.debug_mode).invoke_callable(
        proc,
        args,
        tail_position=False,
        callee_node=None,
        skip_none_propagation=True,
    )
```

This is a Python closure. It is not exposed to Genia code in any form.

### 3.4 Current implementations of `_map`, `_filter`, `_reduce`

```python
def reduce_fn(f, acc, xs):
    for x in xs:
        result = _invoke_raw_from_builtin(f, [result, x])
    return result

def map_fn(f, xs):
    return [_invoke_raw_from_builtin(f, [x]) for x in xs]

def filter_fn(predicate, xs):
    return [x for x in xs if truthy(_invoke_raw_from_builtin(predicate, [x]))]
```

All three use `_invoke_raw_from_builtin` so callbacks receive `none(...)` elements directly.

Registered in env as `_reduce`, `_map`, `_filter` (underscore-prefixed, internal names).

### 3.5 Prelude wrappers

`src/genia/std/prelude/list.genia`:
```genia
reduce(f, acc, xs) = _reduce(f, acc, xs)
map(f, xs) = _map(f, xs)
filter(predicate, xs) = _filter(predicate, xs)
```

These are docstring-annotated thin wrappers. They have no recursive logic of their own; all semantics live in the Python builtins.

### 3.6 Regression case

File: `tests/cases/option/reduce_none_propagation.genia`
Expected output: `[0, [0, 2, 0], 4, [some(1), some(3)], 4]`

This test currently passes because `_invoke_raw_from_builtin` is used. A naive pure-Genia recursive implementation would fail: calling `f(acc, none("x"))` in the loop body would return `none("x")` before calling `f`, yielding `none("x")` as the reduction result.

---

## 4. PROBLEM STATEMENT

### What behavior is currently host-only

`_invoke_raw_from_builtin` is a Python-internal capability: it bypasses the Genia-level `none(...)` short-circuit when calling a Genia callable. There is no equivalent mechanism exposed to Genia code.

### Why that blocks prelude extraction

A pure-Genia recursive implementation of `reduce` such as:

```genia
reduce_impl(f, acc, []) = acc
reduce_impl(f, acc, [x, ..rest]) = reduce_impl(f, f(acc, x), rest)
```

fails when `x` is `none(...)` and `f` does not explicitly handle none, because `f(acc, x)` short-circuits to `x` before calling `f`.

### Classification of the gap

This is a **language contract gap**: the language currently has no way to say "call this function regardless of whether the arguments are `none(...)`". The host adapter exploits an internal Python flag to implement this, making `reduce`/`map`/`filter` non-portable by construction.

---

## 5. DESIGN OPTION INVENTORY

### Option A: `apply_raw(f, args)` / `invoke_raw(f, args)`

A new named prelude primitive (backed by a host builtin) that takes a function and a list of arguments and calls it bypassing none propagation.

```genia
reduce_impl(f, acc, []) = acc
reduce_impl(f, acc, [x, ..rest]) = reduce_impl(f, apply_raw(f, [acc, x]), rest)
```

**Benefits:**
- Explicit: the name makes the semantics obvious
- No new syntax
- Minimal Core IR impact (can be a call to a new named builtin, no new IR node needed)
- Portable: any future host must implement `apply_raw` as a primitive, which is a single well-defined capability

**Risks:**
- Introduces a second call model; programmers must know when to use it
- If misused, can suppress legitimate none propagation errors in normal code
- Name `apply_raw` might conflict with metacircular `apply`

**Parser impact:** None

**Core IR impact:** Minimal; `apply_raw` lowers as an ordinary `IrCall`; no new IR node needed

**Prelude impact:** `reduce`, `map`, `filter` can be rewritten in Genia using `apply_raw`; Python builtins `_reduce`, `_map`, `_filter` can be removed

**Host impact:** Each host must expose `apply_raw` as a host-backed primitive; it is a single function with clear semantics

**Shared spec impact:** New shared eval and error cases needed to validate behavior

---

### Option B: `raw(f)(x)` wrapper syntax

A wrapper expression that returns a version of `f` with none propagation disabled.

```genia
map_impl(f, []) = []
map_impl(f, [x, ..rest]) = [raw(f)(x)] + map_impl(f, rest)
```

**Benefits:**
- Composable: can pass `raw(f)` as a higher-order value

**Risks:**
- Requires new parser support for `raw(f)` as a wrapper form
- `raw(f)` returns a new callable value — creates a new runtime value category or requires wrapping
- Adds parser-level complexity
- Makes the distinction between `f` and `raw(f)` invisible to pattern matching and none-awareness detection
- May accidentally suppress errors in higher-order compositions

**Parser impact:** New syntax form or callable wrapper

**Core IR impact:** New `IrRaw` or wrapper node family needed

**Prelude impact:** Same as A

**Host impact:** Each host must implement the `raw()` wrapper factory

**Shared spec impact:** New parser + eval + IR cases

---

### Option C: call-mode argument `call(f, args, {mode: "raw"})`

A map-keyed options variant of apply:

```genia
call(f, [acc, x], {mode: "raw"})
```

**Benefits:**
- Follows existing map/options pattern
- No new syntax

**Risks:**
- `"raw"` is a stringly-typed mode; typos are silent errors
- More verbose than Option A
- Couples the runtime call model to a runtime map value check
- May be confused with ordinary callable-map invocation

**Parser impact:** None

**Core IR impact:** Minimal; lowers as `IrCall`

**Prelude impact:** Same as A

**Host impact:** Host must interpret the options map at call time; adds overhead

**Shared spec impact:** Moderate

---

### Option D: explicit Option-aware callback protocol

Functions could opt-in to receiving none values by registering as none-aware, similar to the current `__genia_handles_none__` mechanism, but exposed as a Genia annotation.

```genia
@raw
my_reduce_step(acc, x) = acc + unwrap_or(0, x)
```

**Benefits:**
- Aligns with existing annotation surface
- Does not require a new call primitive

**Risks:**
- The none propagation short-circuit happens at the call site, not at the definition site; changing this requires the caller to know the callee is none-aware, which reverts to the current `_NONE_AWARE_PUBLIC_FUNCTIONS` mechanism
- Does not solve the problem of a lambda passed as a callback to `reduce`; a lambda defined inline cannot be annotated with `@raw`
- Still host-specific unless the annotation protocol is part of Core IR

**Parser impact:** New annotation name (minor)

**Core IR impact:** Annotation must be reflected in IR so hosts can read it

**Prelude impact:** Still cannot write a generic `reduce` because the callback is caller-provided

**Host impact:** Host must read the annotation from the IR

**Shared spec impact:** Moderate

---

### Option E: leave behavior host-only and mark reduce/map/filter non-portable

Accept that `reduce`, `map`, `filter` are host substrate and will not be extracted to prelude.

**Benefits:**
- No change required
- No new language surface
- No portability risk

**Risks:**
- Every future host must re-implement these three HOFs in Python/Java/Rust/etc.
- They cannot be shared via the prelude layer
- Violates the goal of #117 and the spirit of Core IR portability
- Sets a precedent that any HOF touching options must stay in the host

**Parser impact:** None

**Core IR impact:** None

**Prelude impact:** None (status quo)

**Host impact:** Permanently required for each host

**Shared spec impact:** Existing tests still pass

---

## 6. RECOMMENDED DIRECTION

**Recommended: Option A — `apply_raw(f, args)`**

Reasoning:

1. **No new syntax**: `apply_raw` is a named call to a builtin; no parser changes needed.
2. **Minimal Core IR**: `apply_raw(f, args)` lowers as `IrCall(IrVar("apply_raw"), [f, args])`; no new IR node.
3. **Explicit name**: the name communicates intent — raw invocation of a callable.
4. **Portable contract**: future hosts (Node, Rust, Java) implement one builtin with a clear semantics.
5. **Testable**: shared spec cases can validate both raw and normal call behavior.
6. **Preserves normal calls unchanged**: `apply_raw` is the opt-in path; `f(x)` behavior is unaffected.

Recommended surface name: `apply_raw(f, args)` where `args` is a list. This avoids conflict with the metacircular `apply(proc, args)` which also takes a list — the names must be distinct. Alternative: `invoke_raw(f, args)`.

Name disambiguation note: metacircular `apply(proc, args)` takes a metacircular procedure and a list of quoted data; `apply_raw(f, args)` takes an ordinary Genia callable and a list of ordinary runtime values. These must not be overloaded.

Preference: `apply_raw` over `invoke_raw` because `apply` already exists in the fn-helpers prelude and the naming is consistent. But the spec phase must confirm the exact name.

---

## 7. TEST STRATEGY FOR LATER PHASES

Do not write tests now.

Recommended future tests:

1. Normal call still propagates `none(...)`: `f(none("x"))` returns `none("x")` unchanged.
2. `apply_raw(f, [none("x")])` calls `f` with `none("x")` directly; body executes.
3. Callback can unwrap `none(...)`: `apply_raw((o) -> unwrap_or(0, o), [none("x")])` returns `0`.
4. `reduce` implemented via `apply_raw` yields same result as current host-backed version.
5. `map` implemented via `apply_raw` yields same result as current host-backed version.
6. `filter` implemented via `apply_raw` yields same result as current host-backed version.
7. `apply_raw` does not hide ordinary runtime errors: `apply_raw((x) -> 1 / 0, [5])` raises as expected.
8. Nested callback behavior: `apply_raw(f, [apply_raw(g, [none("x")])])` behaves correctly.
9. Named function and lambda both work as first argument.
10. Shared spec cases validate the `apply_raw` surface.
11. `reduce_none_propagation.genia` regression case still passes after prelude migration.
12. Existing `_NONE_AWARE_PUBLIC_FUNCTIONS`-based detection is unchanged for normal calls.

---

## 8. DOC IMPACT

Docs likely needing updates in later phases:

- `GENIA_STATE.md`: add `apply_raw` to the builtin/host primitive surface; document the none-bypass contract
- `GENIA_RULES.md`: section 9.6.4 — add sub-clause about `apply_raw` as the explicit raw-call mechanism
- `GENIA_REPL_README.md`: add `apply_raw` to the builtins list
- `README.md`: update autoloaded stdlib highlights if `reduce`/`map`/`filter` are migrated to pure prelude
- `docs/host-interop/capabilities.md`: add `apply_raw` as a required host capability
- `src/genia/std/prelude/list.genia`: replace `_reduce`/`_map`/`_filter` delegation with pure Genia implementations
- `src/genia/std/prelude/fn.genia` (if it exists): document `apply_raw` alongside `apply`

Do not update these now.

---

## 9. PORTABILITY ANALYSIS

### Language contract

`apply_raw(f, args)` is a language-level primitive: its semantics are "call `f` with `args` without activating the automatic `none(...)` short-circuit". This belongs to the language contract and must be part of the shared host spec.

### Core IR

`apply_raw(f, args)` lowers as a normal `IrCall`. No new IR node is required. The host runtime interprets the `apply_raw` name specially (setting `skip_none_propagation=True`). Alternatively, a new `IrRawCall` node could make the semantics explicit in the IR. The spec phase should decide which is cleaner.

### Host substrate

Each host must provide `apply_raw` as a named callable that bypasses none propagation. Python host: thin wrapper around `invoke_callable(..., skip_none_propagation=True)`. Other hosts: equivalent mechanism.

### Prelude helper

After `apply_raw` exists as a host primitive, `reduce`, `map`, and `filter` can be rewritten as pure Genia prelude functions using `apply_raw`. The Python `_reduce`, `_map`, `_filter` builtins can be retired.

---

## 10. RISK ANALYSIS

| Risk | Severity | Mitigation |
|---|---|---|
| Changing default `none(...)` semantics accidentally | High | `apply_raw` is an explicit opt-in; normal calls are unaffected |
| Silent error swallowing | Medium | `apply_raw` only bypasses none propagation, not exceptions; runtime errors still raise |
| Making Option behavior confusing | Medium | Clear naming and docs separate the two call models |
| Two competing call models | Medium | `apply_raw` is narrowly for HOF callbacks; normal calls remain the default |
| Leaking Python internals | Low | `apply_raw` replaces Python-internal `_invoke_raw_from_builtin` with a named contract |
| Hard-to-reason-about callback behavior | Medium | `apply_raw` makes the bypass explicit in source code; no implicit detection needed |
| Name conflict with metacircular `apply` | Low | Use a distinct name; spec phase must confirm; `apply_raw` or `invoke_raw` both work |
| Over-use of `apply_raw` in user code | Low | Document clearly that `apply_raw` is for HOF implementors, not ordinary callers |

---

## 11. RELATIONSHIP TO #117 / #182

- **#188 directly blocks extraction** of `reduce`, `map`, and `filter` from the Python host into prelude.
- **#182** (first extraction batch) must NOT include `reduce`, `map`, or `filter` until #188 is resolved. The batch should proceed with helpers that do not depend on raw invocation.
- **#117** should classify `reduce`, `map`, and `filter` as **blocked on #188** until this lands. After #188, they become safe extraction candidates.

Dependency chain:
```
#188 (apply_raw primitive) → unblocks reduce/map/filter extraction → advances #117 goal
```

---

## 12. FINAL GO / NO-GO

**GO for moving to spec phase.**

### Blockers resolved

- Root cause is identified: `_invoke_raw_from_builtin` is Python-internal with no Genia equivalent.
- The problem is classified: language contract gap.
- A minimal safe direction exists: Option A (`apply_raw`).
- No new syntax required.
- No Core IR change required beyond name recognition.
- Portability path is clear.

### Remaining blockers before implementation

- Spec phase must confirm the exact name (`apply_raw` vs `invoke_raw`).
- Spec phase must decide whether `apply_raw` lowers as `IrCall` (host-recognized name) or a new `IrRawCall` node.
- Design phase must decide whether `_reduce`/`_map`/`_filter` are retired immediately or kept as compatibility shims during transition.

### Recommended next issue/prompt

Spec phase for issue #188: define the observable behavior of `apply_raw(f, args)` and produce shared spec YAML cases covering:
- raw call with `none(...)` argument calls body
- raw call with ordinary value behaves identically to normal call
- raw call does not suppress exceptions
- `reduce`, `map`, `filter` rewritten in prelude via `apply_raw` produce identical outputs to current host-backed versions

### Recommended branch name

`issue-188-raw-callback-invocation-spec`

### Recommended commit message

```
spec(callbacks): define apply_raw observable behavior for issue #188
```

---

*Preflight complete. No implementation, no tests, no docs sync. Branch: issue-188-raw-callback-invocation-preflight.*
