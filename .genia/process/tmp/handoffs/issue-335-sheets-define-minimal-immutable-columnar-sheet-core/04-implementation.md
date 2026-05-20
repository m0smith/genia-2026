# === GENIA IMPLEMENTATION ===

CHANGE NAME:
issue #335 sheets-define-minimal-immutable-columnar-sheet-core

CHANGE SLUG:
issue-335-sheets-define-minimal-immutable-columnar-sheet-core

BRANCH:
feature/issue-335-sheets-define-minimal-immutable-columnar-sheet-core

HANDOFF DIRECTORY:
.genia/process/tmp/handoffs/issue-335-sheets-define-minimal-immutable-columnar-sheet-core/

OUTPUT FILE:
.genia/process/tmp/handoffs/issue-335-sheets-define-minimal-immutable-columnar-sheet-core/04-implementation.md

FAILING TEST COMMIT:
d86bf6a

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

1. CHANGE PLAN

---

Files to add:

* `src/genia/sheet.py`
  * Add minimal immutable `GeniaSheet` runtime value.
  * Add list-of-pairs construction validation.
  * Add helper operations for `shape`, `columns`, `select`, `where`, `derive`, and `rows`.

Files to modify:

* `src/genia/builtins.py`
  * Register the public Sheet API in the Python reference host.
  * Use arity-specific function groups for Sheet helpers so existing user-defined helpers such as `rows()` can coexist with `rows(sheet)`.

* `src/genia/utf8.py`
  * Add deterministic Sheet formatting to avoid leaking Python dataclass reprs when a Sheet is printed directly.

Files to remove:

* None.

---

2. SUMMARY OF CHANGES

---

Implemented the minimal immutable Sheet core defined by the approved contract/design:

* `sheet(columns)`
  * Accepts ordered list-of-pairs input: `[[quote(name), values], ...]`.
  * Requires column values to be lists.
  * Requires unique column names.
  * Requires equal column lengths.
  * Stores canonical columns as tuples.

* `shape(sheet)`
  * Returns `[[rows, n], [columns, n]]`.

* `columns(sheet)`
  * Returns column names in deterministic order.

* `rows(sheet)`
  * Returns deterministic pair-list rows.

* `select(names, sheet)`
  * Returns a new Sheet with requested columns in requested order.
  * Rejects duplicate or missing names.

* `where(predicate, sheet)`
  * Calls the predicate once per row.
  * Requires boolean predicate results.
  * Returns a new filtered Sheet.

* `derive(name, function, sheet)`
  * Calls the function once per row.
  * Appends the derived column.
  * Rejects an existing column name.
  * Stores returned values, including Outcome values, as ordinary cells.

Immutability:

* The canonical representation is tuple-backed.
* Transformations create new `GeniaSheet` values.
* Existing Sheet values are not mutated.

Error behavior:

* Sheet validation errors use stable `TypeError` diagnostics.
* Sheet operation diagnostics opt out of generic pipeline wrapping so shared error specs see the contract-level message.

Rendering:

* Direct Sheet debug/display rendering is deterministic and compact:
  * `sheet([[name, ["Ann"]], [age, [30]]])`

---

3. FILES CHANGED

---

Added:

* `src/genia/sheet.py`

Modified:

* `src/genia/builtins.py`
* `src/genia/utf8.py`

No docs were updated in this implementation phase.

No tests were modified in this implementation phase.

---

4. TESTS RUN AND RESULTS

---

Targeted Sheet tests:

```bash
uv run pytest -q tests/unit/test_sheet.py tests/spec/test_sheet_shared_specs_335.py
```

Result:

```text
18 passed
```

Nearby eval/error shared-spec sweep:

```bash
uv run pytest -q tests/spec/test_spec_ir_runner_blackbox.py::test_discover_specs_includes_eval_cases tests/spec/test_spec_ir_runner_blackbox.py::test_discover_specs_includes_error_pattern_cases tests/spec/test_spec_ir_runner_blackbox.py::test_eval_spec_fixture tests/spec/test_spec_ir_runner_blackbox.py::test_error_spec_fixture
```

Result:

```text
117 passed
```

Regression run for the `rows()` name collision found by full suite:

```bash
uv run pytest -q tests/unit/test_sheet.py tests/spec/test_sheet_shared_specs_335.py tests/unit/test_flow_phase1.py::test_keep_some_else_emits_unwrapped_successes_and_routes_original_failures tests/unit/test_fn_stdlib.py::test_autoloaded_rule_helper_composes_directly_with_option_aware_pipelines_in_rules tests/unit/test_cases.py::test_cases
```

Result:

```text
115 passed
```

Lint:

```bash
uv tool run ruff check src/genia/sheet.py src/genia/builtins.py src/genia/utf8.py tests/unit/test_sheet.py tests/spec/test_sheet_shared_specs_335.py
```

Result:

```text
All checks passed!
```

Full suite:

```bash
uv run pytest -q
```

Result:

```text
2343 passed in 1020.27s (0:17:00)
```

Note:

* `uv run ruff ...` was attempted first but this environment did not have a `ruff` command available through `uv run`.
* The equivalent approved command `uv tool run ruff check ...` passed.

---

5. COMPLEXITY CHECK

---

[x] Minimal and direct

The implementation is limited to:

* one small Sheet runtime module
* public builtin registration
* deterministic formatting support

No parser, lexer, Core IR, docs, flow semantics, or host adapter behavior was changed.

---

6. BLOCKERS OR AMBIGUITIES

---

None.

One implementation integration issue was found and resolved:

* Registering `rows` as a plain runtime value prevented existing user-defined `rows()` helpers from being defined.
* The fix registers Sheet helpers as arity-specific `GeniaFunctionGroup` values, allowing `rows(sheet)` to coexist with user-defined `rows/0`.

---

7. TEST STEP NOTES

---

The next Test Verification phase should verify:

* The committed failing tests from `d86bf6a` now pass.
* Existing user-defined `rows()` functions remain allowed.
* Sheet helpers remain limited to the approved minimal core.
* Docs are still not claiming Sheet behavior until the docs phase updates the source-of-truth files.
