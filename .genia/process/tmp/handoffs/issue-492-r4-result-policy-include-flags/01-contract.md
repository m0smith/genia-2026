# === GENIA CONTRACT (issue #492 r4-result-policy-include-flags) ===

Follow docs/process/llm-system-prompt.md.

CHANGE NAME: issue #492 r4-result-policy-include-flags
CHANGE SLUG: issue-492-r4-result-policy-include-flags

GENIA_STATE.md is the final authority.

Read: 00-preflight.md (present). Branch check: on
`feature/issue-492-r4-result-policy-include-flags`, not `main`, matches
pre-flight. OK.

Rules honored: no implementation, no scope expansion, no new behavior beyond
pre-flight, host-independent contract.

---

## 1. PURPOSE

Lock the normalization contract for the four boolean observability fields of a
lifecycle plan `result_policy`: `include_phase`, `include_scope`,
`include_role`, and `include_source_location`.

Accepted explicit boolean values MUST be preserved in normalized output. An
explicit `false` must not be silently normalized to the default `true`. This
closes the issue #451 audit gap where accepted input did not match normalized
output.

---

## 2. SCOPE (FROM PRE-FLIGHT)

Included:
- `result_policy` normalization of `include_phase`, `include_scope`,
  `include_role`, `include_source_location`.
- Preserving accepted explicit booleans in the normalized map.
- Tests locking the behavior, including explicit `false`.
- Doc-wording clarification only if needed (GENIA_STATE 9.3,
  docs/architecture/lifecycle.md).

Excluded:
- Lifecycle runner, cleanup execution, phase execution, setup/teardown
  annotation behavior, native-test lifecycle hooks, command/file/pipe/repl
  lifecycle behavior.
- Parser, IR, evaluator, builtins, CLI, prelude changes.
- Any change to `failure_order`, `cleanup`, or `failure_policy` normalization.

---

## 3. BEHAVIOR

Inputs:
- A lifecycle plan map that contains a `result_policy` map (validated by
  `validate_lifecycle_plan` / normalized by `normalize_lifecycle_plan`).
- Within `result_policy`, each of the four `include_*` fields is OPTIONAL and,
  when present, MUST be a boolean.

Outputs (normalized `result_policy` map):
- `failure_order`: `observed_order` (unchanged; only `observed_order`
  accepted).
- For each of `include_phase`, `include_scope`, `include_role`,
  `include_source_location`:
  - absent  -> `true` (default)
  - present and `true`  -> `true`
  - present and `false` -> `false`

State changes: none. The plan is inert data; normalization returns a new
`GeniaMap`. No execution, no I/O, no global state.

---

## 4. SEMANTICS

Evaluation behavior:
- Normalization is a pure function of input data. Each `include_*` field is
  independent; explicit values for one field do not affect another.
- The default `true` applies only when a field is absent.

Matching behavior: not applicable (no pattern matching introduced).

Edge cases:
- Mixed explicit values (e.g., `include_phase: true`, `include_scope: false`)
  are each preserved as given.
- A `result_policy` with all four explicitly `false` normalizes all four to
  `false`.
- An empty `result_policy` map normalizes all four to the `true` default.

Error behavior:
- A non-boolean `include_*` value raises `ValueError` with a deterministic
  path-specific diagnostic:
  `invalid lifecycle plan at plan.result_policy.<field>: expected boolean, got <type>`
- An unknown field under `result_policy` raises:
  `invalid lifecycle plan at plan.result_policy.<key>: unsupported result policy field`
- A `failure_order` other than `observed_order` raises:
  `invalid lifecycle plan at plan.result_policy.failure_order: unsupported failure order <value>`
- `result_policy` not a map raises:
  `invalid lifecycle plan at plan.result_policy: expected map, got <type>`

---

## 5. FAILURE

What causes failure:
- Non-boolean value for any `include_*` field.
- Unknown/unsupported field under `result_policy`.
- Unsupported `failure_order`.
- `result_policy` value that is not a map.

Resulting error: `ValueError` with the deterministic path-based message above.

What does NOT happen:
- No partial normalization is returned on failure (raises instead).
- No lifecycle behavior executes.
- Accepted `false` is NOT coerced to `true`.
- No new fields are added to the normalized `result_policy`.

---

## 6. INVARIANTS

- The normalized `result_policy` always contains exactly:
  `failure_order`, `include_phase`, `include_scope`, `include_role`,
  `include_source_location`.
- For every `include_*` field: normalized value equals the explicit input
  value when present, else `true`.
- `false` is a valid, accepted, preserved value for every `include_*` field.
- Validation accepts a value if and only if normalization preserves it:
  accepted input round-trips to normalized output for these fields.
- Diagnostics are deterministic and path-specific.
- Plans remain inert data; normalization has no side effects.

---

## 7. EXAMPLES

Minimal:
```
result_policy: { include_phase: false }
=>
result_policy: {
  failure_order: observed_order,
  include_phase: false,
  include_scope: true,
  include_role: true,
  include_source_location: true,
}
```

Real:
```
result_policy: { include_scope: false, include_source_location: false }
=>
result_policy: {
  failure_order: observed_order,
  include_phase: true,
  include_scope: false,
  include_role: true,
  include_source_location: false,
}
```

Rejection:
```
result_policy: { include_role: quote(yes) }
=> ValueError:
   invalid lifecycle plan at plan.result_policy.include_role: expected boolean, got symbol
```

---

## 8. NON-GOALS

- No result-record emission or result-policy execution.
- No change to `failure_order` accepted values.
- No change to cleanup or failure_policy normalization, including their fixed
  preservation fields.
- No new `result_policy` fields.
- No host-specific behavior beyond the Python reference host utility.

---

## 9. DOC NOTES

- GENIA_STATE.md section 9.3 describes lifecycle plan data-shape support
  (Experimental, Python reference host only). The sentence "Result policy
  validation preserves deterministic failure observability fields" should be
  read as / clarified to: result-policy `include_*` fields are validated as
  booleans and their explicit accepted values are preserved in normalized
  output (default `true` when absent); `failure_order` accepts only
  `observed_order`. Update wording only if it currently implies the values are
  fixed.
- Mark behavior as: experimental.

---

## 10. FINAL CHECK

- Precise and testable: YES (explicit per-field input/output table).
- No implementation details: YES (no code, no function bodies).
- No scope expansion: YES (matches pre-flight scope lock).
- Consistent with GENIA_STATE.md 9.3: YES (clarifies, does not contradict; the
  shape already lists these boolean fields).

OUTPUT: contract above is the authoritative behavior for this change.
