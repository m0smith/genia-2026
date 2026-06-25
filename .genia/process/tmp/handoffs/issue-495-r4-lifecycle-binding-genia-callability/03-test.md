# Test — issue #495 r4-lifecycle-binding-genia-callability

CHANGE NAME: issue #495 r4-lifecycle-binding-genia-callability
CHANGE SLUG: issue-495-r4-lifecycle-binding-genia-callability

Handoff directory:

```text
.genia/process/tmp/handoffs/issue-495-r4-lifecycle-binding-genia-callability/
```

Output file:

```text
.genia/process/tmp/handoffs/issue-495-r4-lifecycle-binding-genia-callability/03-test.md
```

---

## 0. BRANCH

Starting branch:

```text
feature/issue-495-r4-lifecycle-binding-genia-callability
```

Working branch:

```text
feature/issue-495-r4-lifecycle-binding-genia-callability
```

Branch check passed before edits. Work was not done on `main`.

---

## 1. FILES CHANGED

```text
tests/unit/test_lifecycle_binding.py
.genia/process/tmp/handoffs/issue-495-r4-lifecycle-binding-genia-callability/03-test.md
```

No production implementation files were changed.

---

## 2. TESTS ADDED

Updated `tests/unit/test_lifecycle_binding.py` with focused callable participant coverage:

* `test_callable_participant_kind_accepts_genia_function_group_semantics`
  * Uses a `NonCallableMock` with `spec=GeniaFunctionGroup` so it is recognized as a Genia function-group representation while failing raw Python `callable(...)`.
  * Proves `participant_kind="callable"` must use Genia callable-participant semantics rather than only Python host callability.
* `test_callable_participant_kind_accepts_genia_function_values`
  * Constructs a minimal `GeniaFunction` with `IrVar("none")` and an empty `Env`.
  * Proves direct Genia function values remain accepted as lifecycle callable participants.

Existing tests continue to cover:

* plain Python callable candidates accepted for internal compatibility
* ordinary non-callable candidates rejected with the existing diagnostic shape
* callable participant validation does not execute candidate values
* ordering, metadata filters, duplicate diagnostics, required binding diagnostics, and invalid ordering behavior

---

## 3. EXPECTED FAILING TEST COMMAND

```bash
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run pytest -q tests/unit/test_lifecycle_binding.py -v
```

Observed result:

```text
17 collected
1 failed, 16 passed
```

Observed failing test:

```text
tests/unit/test_lifecycle_binding.py::test_callable_participant_kind_accepts_genia_function_group_semantics
```

Observed failing output summary:

```text
assert _participant_names(result) == ["setup"]
E AssertionError: assert [] == ['setup']
```

Interpretation:

* The candidate is `isinstance(function_group, GeniaFunctionGroup)`.
* The candidate is not accepted because current lifecycle binding checks only raw Python `callable(candidate.value)`.
* This is the intended red signal for the implementation phase.

---

## 4. NEARBY VALIDATION

Command:

```bash
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run pytest -q tests/unit/test_native_test_cli.py tests/unit/test_native_test_kernel.py -v
```

Observed result:

```text
29 passed
```

Native-test behavior was not disturbed by the test-phase edit.

---

## 5. IMPLEMENTATION HANDOFF

No production implementation was changed in this TEST phase.

The implementation phase must reference the failing-test commit SHA from this TEST-phase commit before changing `src/genia/lifecycle_binding.py`.
