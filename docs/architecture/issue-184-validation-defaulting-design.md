# === GENIA DESIGN ===

CHANGE NAME: Extract validation and defaulting helpers to prelude
ISSUE: #184
BRANCH: issue-184-validation-defaulting
CONTRACT: docs/architecture/issue-184-validation-defaulting-contract.md

---

## 0. BRANCH DISCIPLINE

Current branch: `issue-184-validation-defaulting` ✓ (not `main`)

---

## 1. PURPOSE

Translate the contract into an implementable file and function structure.

The contract calls for three pure-Genia helpers (`map?`, `list?`, `get_or`) and
three one-line delegation updates in `flow.genia`. This design resolves the exact
file placement and load-order constraint the contract did not address.

---

## 2. SCOPE LOCK

Follows contract exactly. No additions, no reinterpretations.

One correction of contract §3 file placement: see §4 below for the reasoning.

---

## 3. ARCHITECTURE OVERVIEW

The Genia prelude uses a lazy autoload registry. When a user calls a named function
the interpreter looks it up in `env.autoloads`. If found, it loads the corresponding
`.genia` file and retries. If not found, `NameError` is raised.

Consequence for this change: a function defined in file A can call a function
in file B only if file B's function is registered in `env.autoloads`. Unregistered
names in a separate file are unreachable at runtime.

The contract prohibits registering `map?`, `list?`, `get_or` with `register_autoload`
(they are internal; no public API addition). Therefore they cannot live in a separate
`validate.genia` file that `flow.genia` would need to load.

Resolution: the three helpers are added directly to `flow.genia`. This is not a
scope change — the contract's intent (helpers in the prelude, used by the delegation
wrappers) is fully satisfied. Only the in-file location changes from the contract's
suggested `validate.genia` to `flow.genia`. The helpers remain unreachable from the
autoload registry and invisible in `help()`.

This matches the existing pattern for all other internal helpers in `flow.genia`
(e.g., `rules_apply`, `rules_dispatch`, `rules_last_arg`) — they are defined in the
same file as the registered public names, reachable only because that file was loaded.

---

## 4. FILE / MODULE CHANGES

### New files:

None. The contract's `validate.genia` suggestion is not viable without autoload
registration. All changes are contained in existing files.

### Modified files:

**`src/genia/std/prelude/flow.genia`**

- Add three new internal helper definitions (see §6):
  - `map?(v)`
  - `list?(v)`
  - `get_or(key, target, default)`
- Update three existing delegation definitions:
  - `rules_map?(value)` — body replaced with `map?(value)`
  - `rules_list?(value)` — body replaced with `list?(value)`
  - `rules_optional_value(result_map, key, default)` — body replaced with
    `get_or(key, result_map, default)`

**`tests/test_validate_defaulting_helpers_184.py`**

- New pytest file. See §10.

### Removed files:

None.

### Files explicitly NOT changed:

- `src/genia/interpreter.py` — no new `register_autoload` calls, no Python changes
- `src/genia/std/prelude/option.genia` — unchanged
- `src/genia/std/prelude/cli.genia` — unchanged (its inline patterns are correct as-is)
- All truth-hierarchy docs — docs phase must verify; no changes expected

---

## 5. DATA SHAPES

No new data structures. All helpers operate on existing Genia value types:

- Map values — matched by the `{}` partial map pattern
- List values — matched by `[]` and `[_, .._]` patterns
- Any Genia value — passed through to `get` and `unwrap_or`

---

## 6. FUNCTION / INTERFACE DESIGN

### `map?(v)` — new internal helper

```
Parameters: v — any Genia value
Returns:    true | false (boolean, never none)
Raises:     never
```

Placement: near the bottom of `flow.genia`, grouped with the other `rules_*`
internal helpers it generalises (`rules_map?`).

### `list?(v)` — new internal helper

```
Parameters: v — any Genia value
Returns:    true | false (boolean, never none)
Raises:     never
```

Placement: immediately after `map?` in `flow.genia`.

### `get_or(key, target, default)` — new internal helper

```
Parameters:
  key     — any Genia value usable as a map key (typically string)
  target  — any Genia value (map, option, or other — handled by get)
  default — any Genia value, returned as-is when key is absent
Returns: value at key, or default
Raises:  propagates any error raised by get(key, target) for invalid key types
```

Placement: immediately after `list?` in `flow.genia`.

### Updated delegation definitions

`rules_map?(value)` — unchanged signature, body replaced:

```
Old body: ({}) -> true | (_) -> false
New body: map?(value)
```

`rules_list?(value)` — unchanged signature, body replaced:

```
Old body: ([]) -> true | ([_, .._]) -> true | (_) -> false
New body: list?(value)
```

`rules_optional_value(result_map, key, default)` — unchanged signature, body replaced:

```
Old body: unwrap_or(default, get(key, result_map))
New body: get_or(key, result_map, default)
```

---

## 7. CONTROL FLOW

No new control flow. All three new helpers are single-expression functions:

`map?` — single case expression (two arms), returns immediately.

`list?` — single case expression (three arms), returns immediately.

`get_or` — single expression, delegates to `unwrap_or` and `get`, both of which
are already in the environment when `flow.genia` is loaded (they are registered
autoloads from `option.genia`).

The delegation wrappers (`rules_map?`, `rules_list?`, `rules_optional_value`) are
also single-expression forwarding calls. No branching is added.

---

## 8. ERROR HANDLING DESIGN

`map?` and `list?`: no error paths — total functions over all Genia values.

`get_or`: errors propagate from `get(key, target)` unchanged. This matches the
contract (§5) and the prior behavior of `rules_optional_value`, which called
`get` and `unwrap_or` directly with the same propagation behavior.

No new error messages, no new error types, no new error-handling logic.

---

## 9. INTEGRATION POINTS

### With `option.genia`

`get_or` calls `get` and `unwrap_or`, both registered autoloads from `option.genia`.
When `get_or` is first called, `get` and `unwrap_or` must already be in the
environment. This is guaranteed because:
- `rules_optional_value` is only called from within `flow.genia`'s own rule processing
- By that point, `flow.genia` has already been loaded (it's what triggered the call)
- `get` and `unwrap_or` are either already loaded (if any option helper was called
  first) or will be autoloaded on first use within `get_or`'s evaluation

This is the same load-order dependency that already exists: the current
`rules_optional_value = unwrap_or(default, get(key, result_map))` already calls
`get` and `unwrap_or`. No new dependency is introduced.

### With the test suite

Tests call helpers through `run_source()`. The test file exercises:
- `map?`, `list?`, `get_or` directly (by name, triggering autoload of `flow.genia`
  via any registered `flow.genia` function that causes the module to load)

Wait — `map?`, `list?`, `get_or` are NOT registered. To call them in tests, the
test must first trigger a `flow.genia` load. The cleanest approach: tests call
`rules(map?)` or otherwise reference a registered `flow.genia` name first,
OR the test loads `flow.genia` via `run_source` with a complete Genia snippet
that defines a shim and calls the target function.

**Resolved approach:** tests use complete Genia snippets that define the call
chain inline. For example:

```python
# In test, to test map?:
result = run_source("rules_map?({a: 1})")
# rules_map? is internal to flow.genia but callable after flow.genia loads.
# Autoloading rules (arity 0) loads flow.genia, making rules_map? available.
# Then rules_map? calls map?, which is defined in flow.genia.
```

Alternatively, tests exercise `rules_map?` and `rules_list?` directly (which also
validates the delegation chain) since those names are internal-but-callable after
flow.genia loads. The test plan in §10 specifies which names to use.

### With `interpreter.py`

No interaction. No `register_autoload` lines are added. No Python code changes.

---

## 10. TEST DESIGN INPUT

Test file: `tests/test_validate_defaulting_helpers_184.py`

### Strategy

Tests call `rules_map?`, `rules_list?`, and `rules_optional_value` by name
(which are internal-but-callable after any registered `flow.genia` function
loads the module). This validates both the new general helpers and the delegation
chain in a single stroke.

To trigger `flow.genia` load in test snippets, the test source uses `rules` (a
registered name, arity 0) or any other registered `flow.genia` name first, OR
uses `rules_map?` directly (the autoload system will try to load it; since it's
not registered, it requires `flow.genia` to have been loaded via another name).

**Simplest approach:** each test snippet uses `rules_map?({})` etc., and the
test runner registers `flow.genia` as the location for `rules` which causes the
whole file to be loaded including `map?`, `list?`, `get_or`.

OR: use `run_source` with snippets that call `rules(map?)` — triggering load —
then call `map?` directly. The simplest is to use `rules_map?` / `rules_list?`
as the test entry points and test `get_or` via `rules_optional_value`.

### Invariants to cover (from contract §6)

All 10 contract invariants become test cases:

| Test | Source | Expected |
|------|--------|----------|
| map?-empty-map | `rules_map?({})` | `true` |
| map?-nonempty-map | `rules_map?({a: 1})` | `true` |
| map?-list | `rules_map?([])` | `false` |
| map?-string | `rules_map?("x")` | `false` |
| map?-number | `rules_map?(1)` | `false` |
| list?-empty-list | `rules_list?([])` | `true` |
| list?-nonempty-list | `rules_list?([1, 2])` | `true` |
| list?-map | `rules_list?({})` | `false` |
| list?-string | `rules_list?("x")` | `false` |
| get_or-key-present | `rules_optional_value({k: "v"}, "k", "d")` | `"v"` |
| get_or-key-absent | `rules_optional_value({}, "k", "d")` | `"d"` |
| get_or-other-key | `rules_optional_value({x: 1}, "k", "d")` | `"d"` |

Plus regression: existing `flow.genia` rules tests must continue to pass.

---

## 11. DOC IMPACT

No new truth-hierarchy doc entries are expected (all three helpers are internal).

The docs phase must explicitly check and record the result for each of:

1. `GENIA_STATE.md` — does it reference `map?`, `list?`, `get_or`? If not after
   this change, state that no update is needed and why.
2. `GENIA_REPL_README.md` — same check for autoloaded stdlib function list.
3. `README.md` (Autoloaded stdlib highlights section) — same check.
4. `docs/cheatsheet/*` — no cheatsheet currently references `rules_map?`,
   `rules_list?`, or `rules_optional_value`. Same check for new names.

If any helper ends up callable-but-undocumented, the audit must confirm this is
intentional and acceptable under the "internal" classification.

---

## 12. CONSTRAINTS

Must:
- Define `map?`, `list?`, `get_or` in `flow.genia` (only viable co-location)
- Preserve identical behavior of `rules_map?`, `rules_list?`, `rules_optional_value`
- Make no changes to `interpreter.py`
- Match contract invariants exactly

Must NOT:
- Add `register_autoload` for `map?`, `list?`, or `get_or`
- Add docstrings to internal helpers (they would appear in `help()`)
- Change any signatures of existing functions
- Touch `cli.genia`, `option.genia`, or any other prelude file

---

## 13. COMPLEXITY CHECK

[x] Minimal
[x] Necessary

Three new single-expression function definitions. Three one-line body replacements.
One new test file with ~12 test cases. No new abstractions, no new files, no host
changes. This is the smallest possible implementation of the contract.

---

## 14. FINAL CHECK

- Matches contract exactly: ✓ (placement correction is a resolution, not expansion)
- No new behavior introduced: ✓
- Structure is clear and implementable: ✓
- Ready for implementation without ambiguity: ✓

Implementation can begin: add three definitions to `flow.genia`, replace three
function bodies in `flow.genia`, add test file.
