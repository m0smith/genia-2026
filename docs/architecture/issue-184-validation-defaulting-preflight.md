# === GENIA PRE-FLIGHT ===

CHANGE NAME: Extract validation and defaulting helpers to prelude
ISSUE: #184
BRANCH: issue-184-validation-defaulting

---

## 0. BRANCH

Starting branch: `main`
Working branch: `issue-184-validation-defaulting` (created; previously named `issue-117-extract-validation-defaulting` and renamed)
Status: branch was created (did not previously exist)

---

## 1. SCOPE LOCK

### Change includes:

- General-purpose Genia type predicate helpers: `map?(v)`, `list?(v)`, `bool?(v)`
- General-purpose defaulting helper: `get_or(key, target, default)` (or equivalent)
- Extracting the inline predicate logic from `rules_map?` and `rules_list?` in `flow.genia`
  so that domain-specific helpers delegate to or are superseded by general-purpose ones
- Adding pure-Genia validation/defaulting helpers to an appropriate prelude file
- Tests for every extracted helper
- Preserving current behavior exactly

### Change does NOT include:

- New language behavior (no new Genia syntax or semantics)
- Host-environment dependencies (no Python-level type checks moved to prelude)
- Moving host-backed helpers (`_cli_spec`, `_rules_prepare`, `_rules_kernel`) to prelude —
  these have Python `isinstance()` / `callable()` dependencies that cannot be expressed in pure Genia
- Semantic redesign of the rules system or CLI parser
- Broad refactor of any files outside helper extraction
- Pre-emptive doc changes — the docs phase must explicitly verify whether any new
  public helpers require updates to `GENIA_STATE.md`, `README.md`, `GENIA_REPL_README.md`,
  or cheatsheets. If no permanent doc change is needed, the audit phase must justify that.

---

## 2. SOURCE OF TRUTH

Authoritative files:

- `GENIA_STATE.md` (final authority)
- `GENIA_RULES.md`
- `README.md`
- `AGENTS.md`

Additional relevant:

- `src/genia/std/prelude/flow.genia` — contains existing `rules_map?`, `rules_list?`, `rules_optional_value`
- `src/genia/std/prelude/cli.genia` — contains `cli_spec_flags`, `cli_spec_options`, `cli_spec_aliases` (inline defaulting)
- `src/genia/std/prelude/option.genia` — contains `get`, `unwrap_or`, `or_else`
- `src/genia/std/prelude/list.genia` — contains `empty?`, `nil?`
- `src/genia/interpreter.py` — host-backed `_cli_spec`, `_rules_prepare`, `_rules_kernel`

Notes:

- `rules_map?` and `rules_list?` in `flow.genia` are the ONLY existing Genia-level type predicates
  for map and list values. No general-purpose `map?`, `list?`, or `bool?` predicates exist yet.
- `rules_optional_value(map, key, default)` = `unwrap_or(default, get(key, map))` is the only
  named general-defaulting helper, but it is internal to the rules subsystem.
- The host-backed `_cli_spec`, `_rules_prepare`, and `_rules_kernel` have Python dependencies
  (`isinstance()`, `callable()`) that cannot be expressed in pure Genia pattern matching.
  These stay in the host.

---

## 3. FEATURE MATURITY

Stage: [x] Stable

This is a pure prelude refactoring of already-implemented behavior. The underlying
validation and defaulting logic is stable; we are only extracting and naming it.

### How this must be described in docs:

The docs phase must explicitly verify whether any newly added or renamed helpers are
public API (i.e., intended for user-facing code, appearing in `help()`, referenced in
cheatsheets). If public, updates are required to `GENIA_STATE.md`, `GENIA_REPL_README.md`,
and relevant cheatsheets. If internal-only, the audit must justify why no doc update is
needed — a silent omission is not acceptable.

The decision of public vs. internal must be made in the contract phase and confirmed during docs.

---

## 3a. PORTABILITY ANALYSIS

### Portability zone:

`prelude` — behavior lives in `.genia` stdlib; portable if no host calls are made.

All extracted helpers will be pure Genia (pattern matching, `get`, `unwrap_or`).
No host calls. No `_`-prefixed host primitives.

This change affects ONE zone only. No cross-zone split is needed.

### Core IR impact:

`none` — this change does not introduce or modify any `Ir*` node families.
Pure prelude extraction at the Genia-source level.

### Capability categories affected:

`none` — this is a pure prelude refactoring. No new observable behavior at the
eval/ir/cli/flow/error/parse contract boundary.

### Shared spec impact:

`none — no new shared spec cases required`.

The extracted helpers are pure Genia code with no new observable eval or CLI behavior.
No new shared spec YAML files are needed.

New pytest cases in `tests/` will cover the internal prelude helpers.

### Python reference host impact:

`none — Python host behavior is unchanged`.

The interpreter.py file is not modified. The host-backed `_cli_spec`, `_rules_prepare`,
`_rules_kernel`, `_flow?`, and `_rules_error` remain as-is.

### Host adapter impact:

`none — host adapter interface is unchanged`.

The `hosts/python/adapter.py::run_case` boundary is not touched.

### Future host impact:

`prelude` — future hosts that implement the Genia prelude layer will automatically
get these helpers, since they are expressed in pure Genia code.
No new host-primitive backing is needed for a future host to support these helpers.

---

## 4. CONTRACT vs IMPLEMENTATION

### Contract (portable semantics):

The Genia prelude will provide:

- `map?(v)` — returns `true` when `v` is a map value (including empty map `{}`),
  `false` otherwise. Pure pattern matching over Genia map values.

- `list?(v)` — returns `true` when `v` is a list value (including empty list `[]`),
  `false` otherwise. Pure pattern matching over Genia list values.

- `bool?(v)` — returns `true` when `v` is a boolean (`true` or `false`),
  `false` otherwise. Pure pattern matching over Genia boolean values.

- `get_or(key, target, default)` — returns the value for `key` in map `target` when
  present, or `default` when absent. Equivalent to `unwrap_or(default, get(key, target))`.
  This is a named convenience wrapper for the most common defaulting pattern.

Additionally:

- `rules_map?` in `flow.genia` is updated to delegate to `map?`.
- `rules_list?` in `flow.genia` is updated to delegate to `list?`.
- `rules_optional_value` in `flow.genia` is updated to delegate to `get_or`.

### Implementation (Python today):

These helpers will be implemented as pure Genia pattern-matching functions in the prelude.
No new Python code. No new host primitives.

### Not implemented:

- General `string?(v)`, `number?(v)`, `option?(v)`, `pair?(v)` predicates — not in scope.
  (`pair?` already exists as a host builtin; `option?` behavior is covered by `some?`/`none?`.)
- Moving any host-backed validation out of `interpreter.py` — not in scope.

---

## 5. TEST STRATEGY

### Core invariants:

1. `map?({})` → `true`
2. `map?({a: 1})` → `true`
3. `map?([])` → `false`
4. `map?("x")` → `false`
5. `map?(1)` → `false`
6. `list?([])` → `true`
7. `list?([1, 2])` → `true`
8. `list?({})` → `false`
9. `list?("x")` → `false`
10. `bool?(true)` → `true`
11. `bool?(false)` → `true`
12. `bool?(1)` → `false`
13. `bool?("true")` → `false`
14. `get_or("k", {k: "v"}, "def")` → `"v"`
15. `get_or("k", {}, "def")` → `"def"`
16. `get_or("k", {other: 1}, "def")` → `"def"`

### Expected behaviors:

- All predicates return `true` or `false` (boolean), never `none(...)`
- `get_or` preserves the default type exactly — no coercion
- `rules_map?`, `rules_list?`, `rules_optional_value` behavior unchanged
- `cli_spec_flags`, `cli_spec_options`, `cli_spec_aliases` behavior unchanged

### Failure cases:

- There are no failure cases for these helpers — they are total functions
  (they pattern-match on any Genia value and always return a result)

### How this will be tested:

- New pytest test file: `tests/test_validate_defaulting_helpers_184.py`
  covering all invariants above
- Each test runs a Genia expression through `run_source()` and asserts the output
- Tests for `rules_*` delegation: verify `rules_map?(v)` and `rules_list?(v)` still
  return the same results as before extraction
- Tests for `get_or` delegation: verify `rules_optional_value` still works correctly
- Regression: existing flow / cli tests must continue to pass

---

## 6. EXAMPLES

### Minimal example:

```genia
map?({a: 1})          # => true
map?([])              # => false
list?([1, 2, 3])      # => true
list?({})             # => false
bool?(true)           # => true
bool?("yes")          # => false
get_or("x", {x: 10}, 0)   # => 10
get_or("x", {}, 0)         # => 0
```

### Real example (internal delegation):

After extraction, `flow.genia` will contain:

```genia
rules_map?(value) = map?(value)
rules_list?(value) = list?(value)
rules_optional_value(result_map, key, default) = get_or(key, result_map, default)
```

And these delegate to the general helpers in the new or extended prelude file.

---

## 7. COMPLEXITY CHECK

Is this: [x] Revealing structure

### Justification:

The validation and defaulting logic already exists — it is inline in `rules_map?` and
`rules_list?`. This extraction reveals the shared structure already present, making
the general pattern explicit and reusable. No new complexity is introduced.
The number of total lines of code may slightly increase (due to delegation wrappers),
but the logic count stays the same.

---

## 8. CROSS-FILE IMPACT

### Files that must change:

- `src/genia/std/prelude/flow.genia` — update `rules_map?`, `rules_list?`, `rules_optional_value`
  to delegate to general helpers (or add comment noting relationship)
- One of: new `src/genia/std/prelude/validate.genia` OR extended `src/genia/std/prelude/option.genia`
  OR extended `src/genia/std/prelude/fn.genia` — to house the new general helpers
  (contract phase must decide which)
- `tests/test_validate_defaulting_helpers_184.py` — new test file
- `src/genia/std/prelude/__init__.py` — if a new prelude file is created, register it

### Files requiring docs-phase verification:

The docs phase must check each of these and explicitly state whether they need updating:

- `GENIA_STATE.md` — does it need to document new public helpers?
- `GENIA_REPL_README.md` — does it need to list new public helper names?
- `README.md` — does it reference the autoloaded stdlib surface?
- `docs/cheatsheet/*` — do any cheatsheets reference the relevant prelude?

Risk of drift:
[x] Low

The scope is contained to prelude files. The only risk is if `rules_map?` or `rules_list?`
are referenced in tests or spec files directly — those references remain valid since
the functions still exist with the same names.

---

## DOC DISTILLATION CHECK

Will this change create process artifacts?
[x] YES → must run Doc Distillation

Will docs/architecture or docs/design gain new files?
[x] YES — this preflight document (`docs/architecture/issue-184-validation-defaulting-preflight.md`)

Risk of doc drift:
[x] Low

AGENTS.md rule: "No process artifact may live in docs/ after merge."

This preflight document is a process artifact. Distillation (the final phase) must
either DELETE it from `docs/architecture/` or EXTRACT any permanent architectural
facts into an appropriate permanent location before the branch is merged.
Leaving this file in `docs/architecture/` after merge is not allowed.

---

## 9. PHILOSOPHY CHECK

Does this:

- preserve minimalism? YES — extracting shared patterns reduces inline duplication
- avoid hidden behavior? YES — named helpers make the validation/defaulting logic explicit
- keep semantics out of host? YES — this change moves semantics INTO prelude (away from host)
- align with pattern-matching-first? YES — all extracted helpers use pattern matching

### Notes:

The Genia prelude already has this pattern (GENIA_RULES.md §10 Ref/concurrency wrapping,
GENIA_RULES.md §11 Map builtins): thin prelude wrappers over host primitives.
This change applies the same discipline to validation/defaulting: extract general helpers,
have domain-specific ones delegate.

---

## 10. PROMPT PLAN

Will use full pipeline? YES

Steps:

- [x] Preflight — this document
- [ ] Contract
- [ ] Design
- [ ] Test (failing tests first, commit SHA referenced in implementation)
- [ ] Implementation (references failing-test commit SHA)
- [ ] Docs
- [ ] Audit
- [ ] Distillation

---

## FINAL GO / NO-GO

Ready to proceed? YES

Rationale:
- Scope is tight and well-defined
- No behavior change
- Pure prelude extraction — one architectural zone
- No host-environment dependencies in the extracted code
- Clear test strategy
- Low drift risk

## Next prompt to run:

Contract phase: "Write the implementation-ready contract for validation and defaulting
helpers extraction — issue #184. Reference the preflight at
`docs/architecture/issue-184-validation-defaulting-preflight.md`."
