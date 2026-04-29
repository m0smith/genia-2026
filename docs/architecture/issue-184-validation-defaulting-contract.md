# === GENIA CONTRACT ===

CHANGE NAME: Extract validation and defaulting helpers to prelude
ISSUE: #184
BRANCH: issue-184-validation-defaulting
PREFLIGHT: docs/architecture/issue-184-validation-defaulting-preflight.md

---

## 1. PURPOSE

Extract three general-purpose, pure-Genia helpers into the prelude and have the
existing domain-specific helpers in `flow.genia` delegate to them. No behavior
changes at any observable boundary.

This contract defines:
- what the three new internal helpers are
- their exact semantics
- how `flow.genia` delegation changes
- what is explicitly not changed

---

## 2. SCOPE (FROM PRE-FLIGHT)

### Included:

- New internal helper `map?(v)` in the prelude
- New internal helper `list?(v)` in the prelude
- New internal helper `get_or(key, target, default)` in the prelude
- `rules_map?` in `flow.genia` updated to delegate to `map?`
- `rules_list?` in `flow.genia` updated to delegate to `list?`
- `rules_optional_value` in `flow.genia` updated to delegate to `get_or`
- `bool?(v)` is NOT included — see §8 Non-goals

### Excluded:

- No new public API (no autoload registration, no `help()` entry, no `_`-prefix stripping)
- No changes to `interpreter.py`
- No changes to `cli.genia` (its inline `unwrap_or(default, get(key, spec))` calls
  are already correct; updating them to use `get_or` is left for a future cleanup)
- No changes to `GENIA_STATE.md`, `README.md`, `GENIA_REPL_README.md`, or cheatsheets
  in this phase — the docs phase must confirm this is correct
- No `bool?(v)` — see §8

---

## 3. BEHAVIOR DEFINITION

### `map?(v)`

**Location:** New file `src/genia/std/prelude/validate.genia`

**Signature:** `map?(v)`

**What it does:** Returns `true` when `v` is a Genia map value (any map, including
the empty map `{}`). Returns `false` for every other Genia value.

**Inputs:** Any single Genia value.

**Outputs:** `true` or `false`. Never `none(...)`, never raises.

**Implementation shape (Genia pattern matching):**
```genia
map?(v) =
  ({}) -> true |
  (_) -> false
```

The empty-map arm `{}` matches any map value (it is a partial map pattern that
matches any map regardless of content), so this correctly returns `true` for
`{}`, `{a: 1}`, `{x: 1, y: 2}`, etc.

---

### `list?(v)`

**Location:** `src/genia/std/prelude/validate.genia`

**Signature:** `list?(v)`

**What it does:** Returns `true` when `v` is a Genia list value (any list,
including the empty list `[]`). Returns `false` for every other Genia value.

**Inputs:** Any single Genia value.

**Outputs:** `true` or `false`. Never `none(...)`, never raises.

**Implementation shape:**
```genia
list?(v) =
  ([]) -> true |
  ([_, .._]) -> true |
  (_) -> false
```

---

### `get_or(key, target, default)`

**Location:** `src/genia/std/prelude/validate.genia`

**Signature:** `get_or(key, target, default)`

**What it does:** Looks up `key` in map `target`. Returns the associated value
when the key is present. Returns `default` when the key is absent or when
`target` is a `none(...)` value.

**Exact semantics:** Equivalent to `unwrap_or(default, get(key, target))`.
This is a named convenience that reduces repetition in delegation sites.

**Inputs:**
- `key` — any value usable as a map key (typically a string)
- `target` — any Genia value (map, option, or other — `get` handles all cases)
- `default` — any Genia value, returned as-is when key is absent

**Outputs:** The value associated with `key`, or `default`. Never raises on
ordinary absent-key cases (those return `default`). Type errors from invalid
key types are propagated from the underlying `get` call unchanged.

**Implementation shape:**
```genia
get_or(key, target, default) =
  unwrap_or(default, get(key, target))
```

---

### Updated delegation in `flow.genia`

The three existing domain-specific helpers in `flow.genia` are updated to
delegate to the general helpers:

```genia
rules_map?(value) = map?(value)

rules_list?(value) = list?(value)

rules_optional_value(result_map, key, default) =
  get_or(key, result_map, default)
```

**Observable behavior of `rules_map?`, `rules_list?`, `rules_optional_value` is
unchanged.** All callers within `flow.genia` continue to work identically.

---

## 4. SEMANTICS

### `map?(v)` semantics

| Input | Result |
|-------|--------|
| `{}` | `true` |
| `{a: 1}` | `true` |
| `{x: 1, y: 2}` | `true` |
| `[]` | `false` |
| `[1, 2]` | `false` |
| `"hello"` | `false` |
| `42` | `false` |
| `true` | `false` |
| `none` | `false` |
| `some(v)` | `false` |

### `list?(v)` semantics

| Input | Result |
|-------|--------|
| `[]` | `true` |
| `[1]` | `true` |
| `[1, 2, 3]` | `true` |
| `{}` | `false` |
| `{a: 1}` | `false` |
| `"hello"` | `false` |
| `42` | `false` |
| `true` | `false` |
| `none` | `false` |
| `some(v)` | `false` |

### `get_or(key, target, default)` semantics

| `key` | `target` | `default` | Result |
|-------|----------|-----------|--------|
| `"k"` | `{k: "v"}` | `"d"` | `"v"` |
| `"k"` | `{}` | `"d"` | `"d"` |
| `"k"` | `{x: 1}` | `"d"` | `"d"` |
| `"k"` | `none` | `"d"` | `"d"` |
| `"k"` | `none("reason")` | `"d"` | `"d"` |
| `"k"` | `some({k: "v"})` | `"d"` | `"v"` (via `get`'s option-lifting) |

The last row is inherited from `get`'s maybe-aware behavior. `get_or` does not
introduce any new option-handling semantics.

---

## 5. FAILURE BEHAVIOR

### `map?(v)` and `list?(v)`

These helpers are total functions — they accept any Genia value and return `true`
or `false`. They do not raise and do not return `none(...)`.

### `get_or(key, target, default)`

- Absent key returns `default` — no error.
- `none(...)` target returns `default` — no error.
- If `get(key, target)` raises (e.g., invalid key type), that error propagates
  unchanged through `get_or`. This preserves the behavior of the underlying
  `get` call and is not a new failure mode introduced by `get_or`.

---

## 6. INVARIANTS

1. `map?({})` is `true`.
2. `map?(v)` is `true` if and only if `v` is a Genia map value.
3. `list?([])` is `true`.
4. `list?(v)` is `true` if and only if `v` is a Genia list value.
5. `map?` and `list?` never return `none(...)` and never raise on any input.
6. `get_or(key, target, default)` equals `unwrap_or(default, get(key, target))`
   for all inputs where `get` does not raise.
7. `rules_map?(v)` equals `map?(v)` for all inputs.
8. `rules_list?(v)` equals `list?(v)` for all inputs.
9. `rules_optional_value(m, k, d)` equals `get_or(k, m, d)` for all inputs.
10. All existing callers of `rules_map?`, `rules_list?`, `rules_optional_value`
    within `flow.genia` produce identical results before and after this change.

---

## 7. EXAMPLES

### Minimal:

```genia
map?({a: 1})          # true
map?([])              # false
list?([1, 2, 3])      # true
list?({})             # false
get_or("x", {x: 10}, 0)   # 10
get_or("x", {}, 0)         # 0
get_or("x", none, 0)       # 0
```

### Delegation (internal — not user-facing):

```genia
rules_map?({emit: [1], halt: false})    # true  (delegates to map?)
rules_list?([1, 2])                     # true  (delegates to list?)
rules_optional_value({ctx: "a"}, "ctx", {})  # "a"  (delegates to get_or)
rules_optional_value({}, "ctx", {})          # {}   (delegates to get_or)
```

---

## 8. NON-GOALS

- `bool?(v)` is NOT included. The `rules_result_halt_value` function in `flow.genia`
  already handles boolean validation inline via pattern matching arms `(some(true), _)`
  and `(some(false), _)`. Extracting `bool?` is additional scope not required by
  the existing delegation pattern and is deferred.

- No public API addition. These helpers will NOT be registered with `register_autoload`,
  will NOT appear in `help()`, and will NOT be referenced in any truth-hierarchy docs.
  They are internal to the prelude. The docs phase must confirm this remains correct.

- No changes to the host (`interpreter.py`). The Python-backed `_rules_prepare`,
  `_cli_spec`, etc. stay unchanged.

- No changes to `cli.genia`. The inline `unwrap_or(default, get(key, spec))` calls
  in `cli_spec_flags`, `cli_spec_options`, `cli_spec_aliases` are functionally
  equivalent to `get_or` but are not updated in this change to keep scope minimal.

---

## 9. IMPLEMENTATION BOUNDARY

This contract is host-independent. `map?`, `list?`, and `get_or` are expressible
in pure Genia pattern matching using only:
- Genia map pattern `{}`
- Genia list patterns `[]` and `[_, .._]`
- The existing prelude helpers `get` and `unwrap_or`

No new host primitives are introduced. No Python code is added or changed.
Future hosts that load this prelude file automatically gain these helpers.

---

## 10. DOC REQUIREMENTS

### In this change:

No truth-hierarchy doc updates are expected, because the new helpers are internal
to the prelude and not part of the public API.

### Docs phase must explicitly verify:

- `GENIA_STATE.md`: Does it list or reference any prelude function that this change
  adds or modifies? If no, state that explicitly. If yes, update accordingly.
- `GENIA_REPL_README.md`: Same check for the autoloaded stdlib function list.
- `README.md` (Autoloaded stdlib highlights section): Same check.
- `docs/cheatsheet/*`: Do any cheatsheets document these helpers or reference
  `rules_map?`/`rules_list?`/`rules_optional_value`? If yes, update.

The audit phase must confirm the docs phase answered all four checks and did not
silently skip any.

---

## 11. COMPLEXITY CHECK

[x] Minimal
[x] Necessary

Three functions, one new file, three one-line delegation updates.
No new abstractions beyond what is required.

---

## 12. FINAL CHECK

- No implementation details: ✓ (shapes shown are illustrative, not implementation)
- No scope expansion: ✓
- Consistent with `GENIA_STATE.md`: ✓ (pure prelude, no contract boundary change)
- Behavior is precise and testable: ✓ (invariants §6 drive tests directly)
- Distillation is final phase: ✓ (see preflight §10 prompt plan)
