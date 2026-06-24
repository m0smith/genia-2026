# === GENIA DESIGN (issue #492 r4-result-policy-include-flags) ===

Follow docs/process/llm-system-prompt.md.

CHANGE NAME: issue #492 r4-result-policy-include-flags
CHANGE SLUG: issue-492-r4-result-policy-include-flags

GENIA_STATE.md is final authority.

Read: 00-preflight.md (present), 01-contract.md (present). Branch check: on
`feature/issue-492-r4-result-policy-include-flags`, not `main`, matches
pre-flight. OK.

Rules honored: no implementation, no contract change, no new behavior. Contract
is unambiguous (per-field input/output table); no STOP required.

---

## 1. PURPOSE

Translate the contract into implementation structure: make
`_normalize_result_policy` write each accepted explicit `include_*` boolean
into the normalized map instead of emitting a hardcoded default, while keeping
all validation and rejection behavior unchanged.

---

## 2. SCOPE LOCK

Contract includes:
- Preserve accepted explicit booleans for `include_phase`, `include_scope`,
  `include_role`, `include_source_location`; default `true` when absent.
- Keep type validation and path-specific rejection diagnostics.

Contract excludes:
- `failure_order`, `cleanup`, `failure_policy` normalization changes.
- Any lifecycle execution, parser/IR/CLI/prelude changes, new fields.

Do not expand scope.

---

## 3. ARCHITECTURE

Where this fits:
- Single function `_normalize_result_policy(value)` in
  `src/genia/lifecycle_plan.py`, called from `normalize_lifecycle_plan` when
  the plan has a `result_policy` key. Pure data-shape utility, Python
  reference host only.

Affected components:
- `_normalize_result_policy` only. `_require_boolean`,
  `_reject_unknown_policy_fields`, `_require_policy_symbol`, `_symbol`, `_fail`
  are reused unchanged.

Data flow:
- `GeniaMap` in -> validate fields -> build normalized `GeniaMap` ->
  return. The only change: the per-field include value used to build the
  normalized map comes from the input when the field is present, else the
  default.

Integration points: none beyond the existing call site. `GeniaMap` is
immutable-style (`.put(...)` returns a new map), so construction order is the
only consideration.

---

## 4. FILE PLAN

New files: none.

Modified files:
- `src/genia/lifecycle_plan.py` - `_normalize_result_policy`.
- `tests/unit/test_lifecycle_plan.py` - add/extend result_policy tests.
- (Conditional) `GENIA_STATE.md` 9.3 and `docs/architecture/lifecycle.md` -
  wording clarification only if current text implies fixed values. Also update
  the test-count note in 9.3 if the unit-test total changes.

Removed files: none.

---

## 5. DATA / INTERFACE DESIGN

Function: `_normalize_result_policy(value: Any) -> GeniaMap` (signature
unchanged).

Normalized result_policy shape (unchanged keys):
- `failure_order: GeniaSymbol("observed_order")`
- `include_phase: bool`
- `include_scope: bool`
- `include_role: bool`
- `include_source_location: bool`

Per-field resolution rule (the design change):
- For each field in
  (`include_phase`, `include_scope`, `include_role`,
  `include_source_location`):
  - if `value.has(field)`: `field_value = value.get(field)`;
    `_require_boolean(field_value, f"{path}.{field}")`; use `field_value`.
  - else: use `True`.
- Build the normalized map from these resolved values (default `True` when
  absent), rather than hardcoding `True` and discarding the validated value.

Recommended structure (design intent, not code): compute the four resolved
booleans first (validating present ones), then construct the normalized
`GeniaMap` with `failure_order` plus the four resolved values. This keeps a
single construction site and avoids the current build-then-ignore pattern.

Parameters/returns: unchanged. No new public surface.

---

## 6. CONTROL / ERROR FLOW

Execution flow:
1. If `value` is not a `GeniaMap` -> `_fail(path, "expected map", value)`.
2. `_reject_unknown_policy_fields(value, allowed_fields, path, "result policy")`
   - unknown field -> ValueError (unchanged).
3. If `failure_order` present: `_require_policy_symbol`; if not
   `observed_order` -> ValueError (unchanged).
4. For each `include_*` field present: `_require_boolean`; non-boolean ->
   `_fail(path.field, "expected boolean", value)` (unchanged message).
5. Build normalized map using resolved per-field values (default `True`).
6. Return normalized map.

Where errors are detected: during per-field validation (steps 1-4), before the
normalized map is returned. No partial map is returned on failure.

How errors propagate: `ValueError` raised by `_fail` /
`_reject_unknown_policy_fields` / inline checks, surfacing through
`normalize_lifecycle_plan` to the caller. Deterministic path-based messages.

Boundaries enforcing correctness: validation precedes construction; the
function returns only after all present fields validate. Matches contract
failure behavior (raise, do not coerce, do not emit partial output).

Ordering note: validation must run for every present include field even though
values are now also consumed for output - do not short-circuit validation. A
non-boolean must still raise regardless of which field it is.

---

## 7. TEST PLAN INPUT

Invariants to test (in `tests/unit/test_lifecycle_plan.py`):
- Absent include fields -> all `true` (existing default test stays green).
- Explicit all-`true` -> all `true` (existing test stays green).
- Explicit all-`false` -> all `false` (NEW; locks the fix).
- Mixed explicit values (e.g., `include_phase: false`, `include_scope: true`,
  `include_role: false`, `include_source_location: true`) -> each preserved
  (NEW).
- Single explicit `false` with others absent -> that field `false`, others
  `true` default (NEW).

Edge cases:
- Non-boolean (symbol) for each include field still raises with the exact
  path-specific message (existing parametrized rejection tests stay green).
- Unknown result_policy field still rejected (existing behavior).
- `failure_order` other than `observed_order` still rejected (existing).

Regression risks:
- Accidentally changing default behavior when a field is absent.
- Reintroducing the build-then-ignore pattern in a refactor.
- Altering rejection messages relied on by parametrized tests.

Test files/locations:
- `tests/unit/test_lifecycle_plan.py` (extend the existing result_policy
  normalization test or add a focused `test_result_policy_preserves_explicit_false`).

Validation command:
`UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run pytest -q tests/unit/test_lifecycle_plan.py -v`
If docs change:
`UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run pytest -q tests/doc/test_lifecycle_architecture_doc.py tests/doc/test_semantic_doc_sync.py`

---

## 8. DOC IMPACT

- GENIA_STATE.md 9.3: confirm/clarify that result-policy `include_*` fields are
  validated as booleans with explicit accepted values preserved (default
  `true` when absent). Update the unit-test count line if the total changes.
- docs/architecture/lifecycle.md (~line 152): same clarification if its
  summary implies result-policy values are fixed.
- GENIA_RULES.md, GENIA_REPL_README.md, README.md: no change expected.
- Touch docs only if wording currently misstates the behavior; otherwise leave
  unchanged to avoid drift.

---

## 9. COMPLEXITY CHECK

[x] Minimal
[ ] Necessary
[ ] Over-engineered

Explain: The change removes a discard-and-default step and writes validated
values through. No new abstractions, no new control flow, no new fields.

---

## 10. FINAL CHECK

- Matches contract exactly: YES (per-field preserve, default `true`, unchanged
  diagnostics).
- No new behavior: YES (only stops discarding accepted input).
- No host-specific assumptions beyond the existing Python reference host
  utility: YES.
- Ready for implementation: YES.

OUTPUT: design above; implementation phase may proceed (test phase first per
prompt plan).
