# TEST handoff: issue #453 r4-lifecycle-deterministic-ordering-rules

CHANGE NAME: issue #453 r4-lifecycle-deterministic-ordering-rules
CHANGE SLUG: issue-453-r4-lifecycle-deterministic-ordering-rules
ISSUE: #453
BRANCH: feature/issue-453-r4-lifecycle-deterministic-ordering-rules
PHASE: TEST / failing tests only

---

## Branch

- Starting branch: `feature/issue-453-r4-lifecycle-deterministic-ordering-rules`
- Working branch: `feature/issue-453-r4-lifecycle-deterministic-ordering-rules`
- Branch already existed: yes
- Worked directly on `main`: no

---

## Files changed

- `tests/unit/test_lifecycle_binding.py`
- `.genia/process/tmp/handoffs/issue-453-r4-lifecycle-deterministic-ordering-rules/03-test.md`

No production implementation files were modified.

No project docs outside this handoff were modified.

---

## Tests added

Added focused lifecycle annotation binding coverage for:

- omitted binding ordering metadata defaulting to deterministic `source_order`
- normalized binding result data preserving explicit `reverse_source_order`
- non-string/callable ordering values failing validation with a deterministic `binding.ordering` diagnostic that names the runtime type and does not call the value

Existing nearby coverage already covers:

- explicit `source_order`
- explicit `reverse_source_order`
- annotation name matching
- metadata filters
- callable participant kind validation
- required/optional behavior
- duplicate participant diagnostics
- unsupported string ordering diagnostics

---

## Commands run

```bash
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run pytest -q tests/unit/test_lifecycle_binding.py
```

Observed result:

```text
2 failed, 13 passed in 0.18s
```

Failing tests:

- `tests/unit/test_lifecycle_binding.py::test_annotation_binding_defaults_to_source_order_when_ordering_is_omitted`
- `tests/unit/test_lifecycle_binding.py::test_non_string_ordering_reports_field_and_runtime_type_without_calling_value`

Failure evidence:

```text
TypeError: LifecycleAnnotationBinding.__init__() missing 1 required positional argument: 'ordering'
```

```text
Expected regex: 'invalid lifecycle annotation binding at binding\\.ordering: expected ordering identifier, got function'
Actual message: 'invalid lifecycle annotation binding at binding.ordering: unsupported ordering <function ...>'
```

Nearby regression validation:

```bash
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run pytest -q tests/unit/test_lifecycle_plan.py tests/doc/test_lifecycle_architecture_doc.py
```

Observed result:

```text
39 passed in 0.17s
```

---

## Observed failing evidence

The new lifecycle binding tests fail for the intended missing behavior:

- omitted ordering metadata is not currently defaulted by `LifecycleAnnotationBinding`
- non-string ordering values are treated as unsupported ordering values and include unstable Python repr text instead of a deterministic runtime-type diagnostic

The nearby plan and architecture-doc regression suites pass, so the red signal is isolated to lifecycle annotation binding coverage.

---

## Ambiguity or mismatch

The TEST prompt says the expected first-pass ordering rules are:

- `source_order`
- `reverse_source_order`

The approved preflight, contract, design, `GENIA_STATE.md`, `docs/architecture/lifecycle.md`, and existing tests also include `stable_name_order`.

Because `GENIA_STATE.md` is final authority and the approved handoffs include `stable_name_order`, this TEST phase did not add a regression that rejects `stable_name_order`. Existing `stable_name_order` coverage remains unchanged.

The current helper is an internal Python helper and stores ordering as strings. Tests therefore use the existing internal helper shape rather than pretending a public Genia symbol-facing lifecycle binding API exists.

---

## Phase boundary confirmation

- Production code modified: no
- Project docs modified outside handoff: no
- Lifecycle execution added: no
- setup/teardown behavior added: no
- lifecycle runner invoked or implied: no
- parser/Core IR/evaluator/CLI/prelude changes: no
- Proceeded to implementation: no
