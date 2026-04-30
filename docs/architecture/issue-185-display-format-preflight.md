# === GENIA PRE-FLIGHT ===

CHANGE NAME: Extract display and formatting helpers to prelude
ISSUE: #185 (subtask of #117)
BRANCH: issue-117-extract-display-format

---

## 0. BRANCH

Starting branch: `main`
Working branch: `issue-117-extract-display-format` (newly created; did not previously exist)
Status: branch was created fresh from `main`

---

## 1. SCOPE LOCK

### Change includes:

- Expose `format_display` (display form: strings rendered without quotes) as a new
  host primitive `_display` in `interpreter.py`
- Generalize the existing `_flow_debug` primitive to `_debug_repr` (or confirm
  `_flow_debug` is renamed) so it is not scoped only to the flow subsystem
- Create `src/genia/std/prelude/display.genia` with thin prelude wrappers:
  - `display(value)` — Genia-callable display form for any runtime value
  - `debug_repr(value)` — Genia-callable debug/quoted form for any runtime value
- Register the new prelude file in `src/genia/std/prelude/__init__.py` if needed
- Update `flow.genia` to use `debug_repr` instead of the internal `_flow_debug`
  where the general helper is now canonical
- Tests for `display(value)` and `debug_repr(value)` on all major value types
- Preserving exact current behavior: no semantic change

### Change does NOT include:

- IO behavior: `write`, `writeln`, `print`, `log`, `flush` — these stay in `io.genia`
- Representation System work issue #166+ — do not overlap or pre-empt
- New language syntax or runtime value types
- Moving the format logic out of Python into Genia — the Python dispatch over
  `GeniaSymbol`, `GeniaPair`, `GeniaMap`, `GeniaOptionNone`, `GeniaOptionSome`
  is host-internal and must remain host-backed
- `json_stringify` / `json_parse` — already in `json.genia`
- Broad refactor of `utf8.py` (unrelated UTF-8 utilities stay where they are)
- Semantic changes of any kind
- Pre-emptive doc changes — the docs phase must explicitly verify which truth-hierarchy
  docs require updating, and the audit phase must justify any omissions

---

## 2. SOURCE OF TRUTH

Authoritative files:

- `GENIA_STATE.md` (final authority)
- `GENIA_RULES.md`
- `README.md`
- `AGENTS.md`

### Additional relevant:

- `src/genia/utf8.py` — contains `format_display` and `format_debug`; the authoritative
  Python implementations of display and debug rendering logic
- `src/genia/interpreter.py` — contains `flow_debug_fn` (wraps `format_debug`) registered
  as `_flow_debug`; also uses `format_display` directly for `_sink_write_display`, REPL
  output, shell command output, and print/log builtins
- `src/genia/std/prelude/flow.genia` — currently calls `_flow_debug` directly in error
  message construction (lines 193, 206, 227, 249)
- `src/genia/std/prelude/io.genia` — output sinks using display form (IO side, out of scope)
- `src/genia/std/prelude/json.genia` — `json_stringify` is a separate value serializer
  with different semantics; not in scope here

### Notes:

- `format_display` is NOT currently accessible to Genia code at all — it is only used
  internally in the Python host for sink writes, REPL output, and built-in output functions.
- `format_debug` IS accessible as `_flow_debug` but is scoped to the flow subsystem only.
- No prelude file for display/format exists today.
- The existing `json_stringify` is JSON-only and returns `none(...)` on failure; `display`
  is always successful and produces any Genia value's surface representation.
- Issue #166+ (Representation System) may eventually provide a richer, user-configurable
  representation layer. This extraction is a precursor and must not conflict with that work.
  Risk: if #166+ intends to replace `format_display` / `format_debug`, this extraction
  could introduce naming that later requires renaming. The contract phase must assess
  this overlap explicitly before proceeding.

---

## 3. FEATURE MATURITY

Stage: [x] Stable

The formatting logic in `format_display` and `format_debug` is stable — it has been in
production use for all REPL output, `write`/`writeln` sinks, and error messages. This
extraction only names and exposes the existing logic as prelude functions; it introduces
no new logic.

### How this must be described in docs:

The docs phase must explicitly verify whether any newly exposed helpers are public API
(i.e., intended for user-facing code, appearing in `help()`, or referenced in cheatsheets).
If public, `GENIA_STATE.md`, `GENIA_REPL_README.md`, and relevant cheatsheets must be updated.
If internal-only, the audit must justify the omission — a silent omission is not acceptable.

The decision of public vs. internal must be made in the contract phase.

---

## 3a. PORTABILITY ANALYSIS

### Portability zone:

`prelude` AND `Python reference host`

The prelude wrappers (`display.genia`) are in the prelude zone.
The host primitives (`_display`, renaming/generalizing `_flow_debug`) are in the Python
reference host zone.

Two zones are affected. This is justified because:
- The prelude file is a thin wrapper layer — no logic
- The host change is minimal: add one new primitive, rename/generalize one existing one
- Both changes are required together for the prelude wrapper to work

Per AGENTS.md multi-zone rule: document the zones explicitly and justify the coupling.

### Core IR impact:

`none` — this change does not introduce or modify any `Ir*` node families.

### Capability categories affected:

`eval` — `display(value)` and `debug_repr(value)` produce Genia-observable string values;
they could be tested via eval cases.

However, since the new prelude helpers are thin wrappers over already-tested behavior,
and the underlying rendering is unchanged, no new shared spec YAML cases are strictly
required. The contract phase must decide.

### Shared spec impact:

`none — no new shared spec cases required` (preliminary; contract phase must confirm).

Observable eval output is unchanged. The new `display` and `debug_repr` helpers are thin
wrappers. Existing shared eval cases that check `stdout` output from `write`/`writeln`
or REPL rendering already cover the behavior indirectly.

If the contract phase decides to add shared eval cases for `display(value)` → string,
they belong in `spec/eval/`.

### Python reference host impact:

`yes` — two changes in `src/genia/interpreter.py`:

1. Add `_display` as a new host primitive wrapping `format_display`. Registers as
   `env.set("_display", display_fn)`.
2. Rename or alias `_flow_debug` → `_debug_repr` (or add `_debug_repr` as a general alias
   and deprecate `_flow_debug` for flow-internal use). Registers as `env.set("_debug_repr", ...)`.

Both changes expose existing behavior at a new name — no behavioral changes.

### Host adapter impact:

`none — host adapter interface is unchanged`.

`hosts/python/adapter.py::run_case` is not affected.

### Future host impact:

`prelude` layer — future hosts will get `display.genia` automatically if they implement
the two host primitives `_display` and `_debug_repr`.

Each future host must implement:
- `_display(value)` — produces the display form string for any runtime value (strings
  rendered without quotes, numbers/booleans as expected, none/some rendered structurally)
- `_debug_repr(value)` — produces the debug/quoted form string (strings rendered with
  escape sequences and double quotes, all other rendering same as display)

The exact rendering contract will be specified in the contract phase and validated by
tests in the test phase.

---

## 4. CONTRACT vs IMPLEMENTATION

### Contract (portable semantics):

The Genia prelude will provide:

- `display(value)` — returns the display form of `value` as a string.
  - strings render as their content (no surrounding quotes)
  - booleans render as `"true"` or `"false"`
  - numbers render as their decimal representation
  - `none("nil")` renders as `none("nil")`
  - `none(reason)` renders as `none("reason")`
  - `none(reason, ctx)` renders as `none("reason", {...})`
  - `some(v)` renders as `some(display(v))`
  - lists render as `[item1, item2, ...]`
  - maps render as `{key: value, ...}` with identifier keys unquoted
  - pairs render as `(head . tail)` or `(a b c)` for nil-terminated chains
  - symbols render as their name
  - always succeeds; never returns `none(...)`

- `debug_repr(value)` — returns the debug/quoted form of `value` as a string.
  - same as `display(value)` for all types except strings
  - strings render with double-quote delimiters and escape sequences:
    `"\n"`, `"\t"`, `"\r"`, `"\\"`, `"\""` — all other ASCII/Unicode chars raw
  - always succeeds; never returns `none(...)`

### Implementation (Python today):

Both helpers are implemented as thin Genia wrappers over host primitives that call
the existing `format_display` and `format_debug` Python functions in `utf8.py`.
No new Python formatting logic; only primitive registration.

### Not implemented:

- User-customizable value rendering / type-dispatch hooks — not in scope
- Truncation or pretty-printing with configurable width — not in scope
- Any interaction with the Representation System (#166+) — not in scope
- `inspect` or `tap`-style debugging helpers — these already exist in `fn.genia`
  and use `log`/`format_debug` internally; they are not changed here

---

## 5. TEST STRATEGY

### Core invariants:

`display(value)` invariants:
1. `display("hello")` → `"hello"` (no quotes)
2. `display(42)` → `"42"`
3. `display(true)` → `"true"`
4. `display(false)` → `"false"`
5. `display(none)` → `none("nil")` as string → `'none("nil")'`
6. `display(some(3))` → `'some(3)'`
7. `display([1, 2, 3])` → `'[1, 2, 3]'`
8. `display({a: 1})` → `'{a: 1}'`

`debug_repr(value)` invariants:
9. `debug_repr("hello")` → `'"hello"'` (with quotes)
10. `debug_repr("line\nnewline")` → `'"line\\nnewline"'`
11. `debug_repr(42)` → `"42"` (same as display for numbers)
12. `debug_repr(true)` → `"true"` (same as display for booleans)
13. `debug_repr(none)` → same none string form as display
14. `debug_repr([1, "a"])` → `'[1, "a"]'` (strings in lists are quoted)

### Expected behaviors:

- Both helpers always return a string — never `none(...)`
- `display` is a lossy format: the string `"42"` and the number `42` produce the same output
- `debug_repr` is the unambiguous format: strings are always distinguishable from numbers
- No IO side effects — these are pure value-to-string conversions

### Failure cases:

None — both helpers are total functions that succeed for any Genia value.

### Negative guardrails (no IO/printing side effects):

- Calling `display(v)` or `debug_repr(v)` must not produce any stdout/stderr output
- The test must confirm no output is produced as a side effect

### How this will be tested:

- New pytest test file: `tests/unit/test_display_format_185.py`
  - Each test runs a Genia expression through `run_source()` and asserts the return value
  - Cover all major value types for both `display` and `debug_repr`
  - Regression: existing `flow.genia` error messages still render correctly after
    any `_flow_debug` → `_debug_repr` rename
  - Regression: existing `write`/`writeln` behavior (IO sinks) is unchanged

---

## 6. EXAMPLES

### Minimal example:

```genia
display("hello")            # => "hello"  (no quotes around the string)
display(42)                 # => "42"
display([1, 2])             # => "[1, 2]"
debug_repr("hello")         # => "\"hello\""  (with quotes)
debug_repr(42)              # => "42"
```

### Real example (internal delegation in flow.genia):

After extraction, `flow.genia` error message construction changes from:

```genia
concat("returned ", concat(_flow_debug(result), "; expected none(...) or some(result)"))
```

to:

```genia
concat("returned ", concat(debug_repr(result), "; expected none(...) or some(result)"))
```

The behavior is identical; `debug_repr` is the canonical name.

---

## 7. COMPLEXITY CHECK

Is this: [x] Revealing structure

### Justification:

`format_display` and `format_debug` already exist and are used throughout the runtime.
This extraction makes them first-class Genia-callable functions under documented names,
following the established prelude pattern. The total logic count is unchanged.
The number of files increases by one (`display.genia`), but the formatting logic does not
grow or change. No new complexity is introduced.

---

## 8. COMPLEXITY CHECK — ADDITIONAL

### Is this adding complexity or revealing structure?

Revealing structure: the display/format behavior was always present but only accessible
internally to the Python host. Naming it explicitly in the prelude reveals the existing
structure.

### Is extraction worth doing as one cycle?

Yes. The scope is tight: one new prelude file, two new host primitives, one prelude update
(flow.genia). All changes are mechanically coupled. Splitting further would create an
incomplete state where a host primitive exists without a prelude wrapper.

### Any reason to split further?

Only if issue #166+ (Representation System) is imminent and would rename these.
If so, the contract phase should block this extraction until naming is settled with #166+.
This is the primary blocking risk.

---

## 9. PHILOSOPHY CHECK

Does this:

- preserve minimalism? YES — one small prelude file; no new logic; follows existing pattern
- avoid hidden behavior? YES — display/debug rendering is now explicitly named and documented
  instead of being an internal Python-only detail
- keep semantics out of host where feasible? YES — the prelude wrappers bring formatting
  behavior closer to the Genia layer; the host keeps only the type dispatch that requires
  Python isinstance checks
- align with pattern-first / value-first design? YES — helpers are pure value → string
  transforms; no side effects; consistent with the existing prelude helper pattern
- avoid representation-system creep? YES (with caveats) — this extraction does NOT introduce
  user-customizable rendering, type registration, or dispatch hooks. It only exposes
  the existing flat-switch formatting as named Genia functions. However: the contract phase
  MUST explicitly verify that the chosen names (`display`, `debug_repr`) do not conflict
  with planned Representation System (#166+) naming.

---

## 10. PROMPT PLAN

Recommended separate prompts:

1. **Contract** — Define the exact public API surface: `display(value)`, `debug_repr(value)`.
   Confirm chosen names do not conflict with #166+. Decide whether helpers are public
   (in `GENIA_STATE.md`) or internal. Write the implementation-ready contract.

2. **Design** — Specify: which file houses the prelude wrappers, how `_flow_debug` is
   renamed or aliased, whether the interpreter change is a rename or an addition.
   Output: file list, function signatures, migration plan for `flow.genia`.

3. **Failing tests** — Write `tests/unit/test_display_format_185.py` with tests for
   all invariants listed in section 5. All tests must fail before implementation.
   Commit and record the SHA.

4. **Implementation** — Add `_display` primitive in interpreter.py, rename/alias `_flow_debug`
   to `_debug_repr`, create `display.genia`, update `flow.genia`, register prelude.
   Reference failing-test commit SHA. All tests must now pass.

5. **Docs** — Verify explicitly whether `display` and `debug_repr` appear in `GENIA_STATE.md`,
   `GENIA_REPL_README.md`, `README.md`, and cheatsheets. Update if public. Justify if not.

6. **Audit** — Run full test suite, confirm no regressions, verify doc alignment, confirm
   no overlap with #166+, verify AGENTS.md process-artifact rule for this file.

7. **Distillation** — Remove or archive this preflight document from `docs/architecture/`
   per AGENTS.md rule: "No process artifact may live in docs/ after merge."

---

## FINAL VERDICT

### GO / NO-GO

**GO** — with one blocking condition to verify at contract phase.

### Blocking questions:

1. **#166+ overlap**: Does the Representation System work (#166+) have reserved names
   or plans that conflict with `display` and `debug_repr`? The contract phase must
   explicitly resolve this before proceeding with implementation.

If the answer is "yes, naming will conflict", this extraction should either:
- be deferred until #166+ is scoped, or
- use clearly internal names (`_display_value`, `_debug_value`) with a plan to rename
  when #166+ lands.

If the answer is "no conflict", proceed normally.

### Recommended commit message:

```
preflight(display): assess extraction of display/format helpers to prelude — issue #185

Starting branch: main
Working branch: issue-117-extract-display-format (created)

Scope: expose format_display as _display builtin, generalize _flow_debug to _debug_repr,
create display.genia prelude with display(value) and debug_repr(value) wrappers.
No behavior change. Portability zones: prelude + Python reference host.
Blocking question: naming conflict with Representation System #166+ must be resolved
at contract phase.

Go/No-Go: GO (pending #166+ naming confirmation at contract phase)
```

---

## DOC DISTILLATION CHECK

Will this change create process artifacts?
[x] YES → must run Doc Distillation

Will docs/architecture or docs/design gain new files?
[x] YES — this preflight document (`docs/architecture/issue-185-display-format-preflight.md`)

Risk of doc drift:
[x] Low

AGENTS.md rule: "No process artifact may live in docs/ after merge."

This preflight document is a process artifact. Distillation (the final phase) must
either DELETE it from `docs/architecture/` or EXTRACT any permanent architectural
facts into an appropriate permanent location before the branch is merged.
Leaving this file in `docs/architecture/` after merge is not allowed.

---

## CROSS-FILE IMPACT

### Candidate files to inspect/change later:

- `src/genia/interpreter.py` — add `_display` builtin; rename/alias `_flow_debug` → `_debug_repr`
- `src/genia/utf8.py` — no change required (format_display/format_debug stay)
- `src/genia/std/prelude/display.genia` — NEW FILE: `display(value)` and `debug_repr(value)`
- `src/genia/std/prelude/flow.genia` — update 4 call sites from `_flow_debug` to `debug_repr`
- `src/genia/std/prelude/__init__.py` — register `display.genia` if required by autoload mechanism

### Candidate tests/specs to add/update later:

- `tests/unit/test_display_format_185.py` — NEW: all invariants from section 5
- `tests/unit/test_flow_phase1.py` — verify flow error messages are unchanged (regression)
- `tests/unit/test_io_sinks.py` — verify `write`/`writeln` output is unchanged (regression)

### Docs likely needing sync later (to be confirmed in docs phase):

- `GENIA_STATE.md` — does it need to document `display` and `debug_repr` as public helpers?
- `GENIA_REPL_README.md` — does it need to list these in the prelude surface?
- `README.md` — does it reference the autoloaded stdlib surface for formatting?
- `docs/cheatsheet/*` — do any cheatsheets reference formatting behavior?

Risk of drift:
[x] Low

The scope is contained to prelude files and a small interpreter change. The only external
risk is if `_flow_debug` is referenced in spec YAML files — a quick grep confirms it is not.
All current call sites of `_flow_debug` are inside `flow.genia` itself.
