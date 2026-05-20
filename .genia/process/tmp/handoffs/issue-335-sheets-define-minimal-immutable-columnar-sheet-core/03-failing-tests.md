# === GENIA FAILING TESTS ===

CHANGE NAME:
issue #335 sheets-define-minimal-immutable-columnar-sheet-core

CHANGE SLUG:
issue-335-sheets-define-minimal-immutable-columnar-sheet-core

BRANCH:
feature/issue-335-sheets-define-minimal-immutable-columnar-sheet-core

HANDOFF DIRECTORY:
.genia/process/tmp/handoffs/issue-335-sheets-define-minimal-immutable-columnar-sheet-core/

OUTPUT FILE:
.genia/process/tmp/handoffs/issue-335-sheets-define-minimal-immutable-columnar-sheet-core/03-failing-tests.md

---

0. BRANCH CHECK

---

Result: PASS

Current branch:

```text
feature/issue-335-sheets-define-minimal-immutable-columnar-sheet-core
```

Preflight branch:

```text
feature/issue-335-sheets-define-minimal-immutable-columnar-sheet-core
```

The branch is not `main` and matches the preflight handoff.

---

1. TEST PLAN

---

Files added:

* `spec/eval/sheet-shape-columns-rows.yaml`
* `spec/eval/sheet-empty-core.yaml`
* `spec/eval/sheet-select-immutable.yaml`
* `spec/eval/sheet-where-core.yaml`
* `spec/eval/sheet-derive-core.yaml`
* `spec/error/error-sheet-unequal-column-lengths.yaml`
* `spec/error/error-sheet-select-missing-column.yaml`
* `spec/error/error-sheet-derive-duplicate-column.yaml`
* `tests/unit/test_sheet.py`
* `tests/spec/test_sheet_shared_specs_335.py`

Behavior groups covered:

* Sheet construction from ordered list-of-pairs column input.
* Shape inspection through `shape(sheet)`.
* Column inspection through `columns(sheet)`.
* Row inspection through `rows(sheet)`.
* Empty Sheet behavior.
* Column selection and requested-order preservation.
* `where` true/false filtering with pair-list row values and current legal lambda syntax.
* `derive` of a constant column with Outcome values stored as ordinary cells.
* Immutability as observed by the original Sheet shape after `select`, `where`, and `derive`.
* Clear errors for unequal column lengths, duplicate construction names, missing selected columns, and duplicate derived names.
* Shared spec discovery for the new Sheet cases.

Contract invariants covered:

* Columns are named and ordered.
* Column lengths must be aligned.
* Row count and column count are deterministic.
* Rows are deterministic pair-list views.
* Sheet operations return new values and leave the original Sheet unchanged.
* Outcome cell values are not unwrapped or propagated automatically.
* Duplicate derived names and duplicate selected/constructed names are rejected in phase one.
* No new syntax is required; tests use `quote(name)` and `(row) -> ...`.

---

2. FILES CHANGED

---

Added shared eval specs:

* `spec/eval/sheet-shape-columns-rows.yaml`
* `spec/eval/sheet-empty-core.yaml`
* `spec/eval/sheet-select-immutable.yaml`
* `spec/eval/sheet-where-core.yaml`
* `spec/eval/sheet-derive-core.yaml`

Added shared error specs:

* `spec/error/error-sheet-unequal-column-lengths.yaml`
* `spec/error/error-sheet-select-missing-column.yaml`
* `spec/error/error-sheet-derive-duplicate-column.yaml`

Added pytest coverage:

* `tests/unit/test_sheet.py`
* `tests/spec/test_sheet_shared_specs_335.py`

No implementation files were modified.

No docs were updated in this phase.

---

3. COMMANDS RUN

---

Targeted new tests:

```bash
uv run pytest -q tests/unit/test_sheet.py tests/spec/test_sheet_shared_specs_335.py
```

Result:

```text
17 failed, 1 passed
```

Nearby shared-spec discovery sanity check:

```bash
uv run pytest -q tests/spec/test_spec_ir_runner_blackbox.py::test_discover_specs_includes_eval_cases tests/spec/test_spec_ir_runner_blackbox.py::test_discover_specs_includes_error_pattern_cases
```

Result:

```text
2 passed
```

---

4. FAILING EVIDENCE

---

Expected failures:

* `tests/unit/test_sheet.py::test_sheet_shape_columns_and_rows_are_deterministic`
  * Fails with `NameError: Undefined name: sheet`.
  * Expected because `sheet` is not implemented or registered yet.

* `tests/unit/test_sheet.py::test_empty_sheet_has_zero_shape_and_empty_rows`
  * Fails with `NameError: Undefined name: sheet`.
  * Expected because empty Sheet construction is not implemented yet.

* `tests/unit/test_sheet.py::test_select_reorders_columns_and_preserves_original_sheet`
  * Fails with `NameError: Undefined name: sheet`.
  * Expected because Sheet construction and `select` are not implemented yet.

* `tests/unit/test_sheet.py::test_where_filters_rows_and_preserves_original_sheet`
  * Fails with `NameError: Undefined name: sheet`.
  * Expected because Sheet construction and `where` are not implemented yet.

* `tests/unit/test_sheet.py::test_derive_appends_column_stores_outcomes_and_preserves_original_sheet`
  * Fails with `NameError: Undefined name: sheet`.
  * Expected because Sheet construction and `derive` are not implemented yet.

* `tests/unit/test_sheet.py::test_sheet_errors_are_clear[...]`
  * Four parameterized cases fail with `NameError: Undefined name: sheet`.
  * Expected before implementation because the tested validation paths are unreachable until `sheet` exists.

* `tests/spec/test_sheet_shared_specs_335.py::test_sheet_eval_shared_specs[...]`
  * Five shared eval specs fail with actual stderr `Error: Undefined name: sheet`.
  * Expected before implementation because the public Sheet API is absent.

* `tests/spec/test_sheet_shared_specs_335.py::test_sheet_error_shared_specs[...]`
  * Three shared error specs fail because actual stderr is `Error: Undefined name: sheet` instead of the Sheet-specific diagnostics.
  * Expected before implementation because validation errors are not implemented yet.

Passing evidence:

* `tests/spec/test_sheet_shared_specs_335.py::test_discover_specs_includes_sheet_cases`
  * Passes, proving the new YAML files load and are discoverable by the existing shared-spec runner.

* Existing eval/error discovery sanity tests pass:
  * `test_discover_specs_includes_eval_cases`
  * `test_discover_specs_includes_error_pattern_cases`

Failure count:

* 17 failures in the targeted new tests.
* This is below the 20-failure stop threshold.

---

5. AMBIGUITIES / BLOCKERS

---

No contract/design blockers found.

One initial test bug was corrected during this phase:

* The first draft used conceptual `row -> ...` lambda syntax from the contract examples.
* Current Genia syntax requires `(row) -> ...`.
* Specs and tests were corrected to use `(row) -> ...`, matching the design condition that tests use current legal syntax.

Implementation phase notes:

* Expected observable shape output is the design-selected pair-list representation:
  * `[[rows, <row_count>], [columns, <column_count>]]`
* Expected row output is deterministic pair-list rows:
  * `[[[name, "Ann"], [age, 30]], ...]`
* Tests avoid direct bare Sheet rendering.
* Tests do not require row dot-access or new parser syntax.
