# E18-4 Reconcile Patterns, Assertions, and Equality-like Surfaces — Design

ISSUE: #794
STATUS: design

Translates the E18-4 contract into implementation structure. Adds no behavior.

---

## 1. PURPOSE

Delete four independent equality implementations and one independent key
relation, replacing each with a call to the existing boundary. Nothing new is
built; the work is subtraction.

---

## 2. CHANGES, ONE PER SURFACE

### 2.1 `assert_eq` — `src/genia/builtins.py`

`if actual != expected:` becomes `if not genia_equal(actual, expected):`.

The `NativeTestFailure` shape, message, and `expected`/`actual` fields are
untouched, so failure rendering and the native-test CLI are unaffected.

This site also stops being a protected-payload oracle — though #793 already
closed that at the type level, this makes it structural rather than incidental.

### 2.2 Literal patterns — `src/genia/pattern_match.py`

`return {} if pattern.value == arg else None` becomes a `genia_equal` call.

Mismatch stays `None`, so clause selection is unchanged: a kind difference makes
the clause not match rather than raising.

### 2.3 Duplicate bindings — `src/genia/pattern_match.py`

In `_merge_bindings`, `if key in target and target[key] != value` becomes a
`genia_equal` check.

Only the same-name case is affected. Merging bindings for different names does
not reach the comparison at all, so the hot path for ordinary multi-name patterns
is unchanged.

### 2.4 Meta-evaluator operators — `src/genia/builtins.py`

`_meta_operator_eq` and `_meta_operator_ne` delegate to `genia_equal` and its
negation.

Only these two operators change. The relational operators (`<`, `<=`, `>`, `>=`)
and the arithmetic operators are deliberately left alone: R18 defines no
ordering, so changing them would be scope expansion.

### 2.5 Sheet column-name identity — `src/genia/sheet.py`

`_freeze_column_name` is replaced by a delegation to `canonical_map_key`, the
same canonicalizer map keys use, wrapped so the existing Sheet-specific error
type and messages are preserved.

This is the right primitive rather than a coincidence: column-name identity and
map-key identity ask the same question — "do these two values denote the same
slot?" — and the contract requires both to be `==`.

Consequences, both intended:

- `true` and `1` become distinct column names, so a Sheet that was rejected as
  having duplicate columns is now accepted
- NaN, and structural names containing NaN, become illegal column names, because
  a non-reflexive name cannot denote a stable column

The second is a *new* rejection. It follows directly from the contract's
reflexivity requirement, and the alternative — a column whose name does not equal
itself — is incoherent.

Protected values remain rejected as column names with their existing message.
`canonical_map_key` rejects them too, so the guarantee is not weakened; the
Sheet-specific message is preserved by checking protection before delegating.

The `try: hash(name)` fallback at the end of the current function is removed:
under the canonical relation the legal set is closed and explicit, so an
"anything hashable" escape hatch would reintroduce a host-defined relation.

---

## 3. IMPORT DIRECTION

`pattern_match.py`, `builtins.py`, and `sheet.py` all import from
`equality.py`, which imports `values.py` and `sheet.py`. `sheet.py` importing
`equality.py` at module scope would therefore cycle, so it uses the same
function-local import with module-level cache that `values.py` already uses for
`_freeze_map_key`.

---

## 4. FILE PLAN

Modified: `src/genia/builtins.py`, `src/genia/pattern_match.py`,
`src/genia/sheet.py`, `GENIA_STATE.md`.

New: `spec/eval/r18-surface-*.yaml`, `spec/error/r18-sheet-column-*.yaml`,
`tests/unit/test_r18_equality_surface_reconciliation_794.py`, shared-spec wiring.

---

## 5. TEST PLAN INPUT

The decisive test is **cross-surface agreement**: run the same operand pairs
through `==`, a literal pattern, a duplicate binding, `assert_eq`, and the
meta-evaluator in one program and require identical answers. Per-surface tests
would not catch a future surface drifting away from the relation; this does.

Also: Sheet columns distinguishing `true` from `1`; NaN column-name rejection;
protected column-name rejection message unchanged; index handle `==` returning a
boolean; named pattern values compared without invocation; `assert_eq` on
protected carriers not being an oracle.

Regression risks: pattern dispatch order, native test CLI output, Sheet
construction and `collect_sheet`, `render_csv`, and any existing test asserting
the old Sheet duplicate-column rejection.

---

## 6. COMPLEXITY CHECK

- [x] Minimal
- [ ] Necessary
- [ ] Over-engineered

Five call sites, each becoming a delegation. Net removal of logic.

---

## 7. FINAL CHECK

- matches contract exactly: YES
- no behavior added by design: YES
- no new pattern syntax, open functions, or public surface: YES
- no ordering introduced: YES — only `==`/`!=` of the meta-evaluator change
- no Core IR or parser change: YES

**GO for the E18-4 failing-test phase.**
