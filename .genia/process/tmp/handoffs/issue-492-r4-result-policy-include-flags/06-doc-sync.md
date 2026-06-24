# === GENIA DOC SYNC (issue #492 r4-result-policy-include-flags) ===

Follow docs/process/llm-system-prompt.md.

CHANGE NAME: issue #492 r4-result-policy-include-flags
CHANGE SLUG: issue-492-r4-result-policy-include-flags

GENIA_STATE.md is final authority.

Read: 00-preflight.md, 01-contract.md, 02-design.md, 04-implementation.md
(all present). Branch check: on
`feature/issue-492-r4-result-policy-include-flags`, not `main`, matches
pre-flight. OK.

Goal honored: make docs match the implemented and tested behavior; document
only what is verified; minimal, local edits.

---

## 1. SUMMARY OF DOC CHANGES

Two canonical/doc files updated to reflect that result-policy observability
include flags now preserve explicit accepted boolean values (default `true`
when omitted), and to correct the lifecycle-plan unit-test count. No new
behavior documented; no scope expansion.

---

## 2. FILES UPDATED

- `GENIA_STATE.md` (section 9.3, authoritative):
  - Replaced the vague sentence "Result policy validation preserves
    deterministic failure observability fields." with precise wording:
    `failure_order` is fixed to `observed_order`; the include flags
    (`include_phase`, `include_scope`, `include_role`,
    `include_source_location`) are validated as booleans, each explicit
    accepted value is preserved in normalized output, and omitted flags
    default to `true`.
  - Updated the validation line from "(32 tests)" to "(35 tests)" to match
    the three new result-policy preservation tests.
- `docs/architecture/lifecycle.md` (~line 152):
  - Added issue `#492` to the implementing-issues reference for
    `src/genia/lifecycle_plan.py`.
  - Added one sentence noting the result-policy include flags are validated
    as booleans, preserve explicit accepted values, and default omitted flags
    to `true` (issue #492).

Not changed (and why):
- `GENIA_RULES.md`: no evaluation/matching semantics changed (inert data
  normalization only).
- `GENIA_REPL_README.md`, `README.md`: no user-facing surface/CLI/REPL change.
- `examples/*`: result_policy is internal host data; no surface example uses
  it.

---

## 3. KEY WORDING CHANGES

Before (GENIA_STATE 9.3):
"Result policy validation preserves deterministic failure observability
fields."

After (GENIA_STATE 9.3):
"Result policy validation fixes `failure_order` to the deterministic
`observed_order` label and validates the observability include flags
(`include_phase`, `include_scope`, `include_role`,
`include_source_location`) as booleans, preserving each explicit accepted
value in the normalized output and defaulting omitted flags to `true`."

Rationale: the prior wording was ambiguous and could be read as implying the
include values are fixed. The new wording matches the contract decision
(preserve explicit accepted booleans) and the implemented one-line fix in
`_normalize_result_policy`.

---

## 4. TRUTH / CONSISTENCY CHECK

- GENIA_STATE 9.3 now states exactly what the code does: type-validate, then
  preserve the accepted value, default `true` when absent. Verified against
  `src/genia/lifecycle_plan.py` `_normalize_result_policy`.
- Test count "35 tests" matches the focused suite (3 new preservation tests
  added to the prior 32). Confirmed by running the suite: 35 passed.
- Maturity unchanged: still "Experimental, Python reference host only."
  Limitations list unchanged (no runner, no execution, inert data).
- Architecture doc remains a summary that defers to GENIA_STATE 9.3 for the
  full contract; the added sentence does not contradict it.

Doc validation run (writable cache; network-restricted uv unavailable, used
the project venv interpreter):
- `tests/unit/test_lifecycle_plan.py` -> 35 passed.
- `tests/doc/test_lifecycle_architecture_doc.py tests/doc/test_semantic_doc_sync.py`
  -> 92 passed.

---

## 5. COMPLEXITY CHECK

[x] Minimal and clear
[ ] Slightly expanded but justified
[ ] Too verbose

Two small wording edits plus a count correction; no new doc sections or
categories.

---

## 6. RISKS / AMBIGUITIES

- Low risk. The doc tests do not pin the literal test count or the prior
  phrase, so the edits did not break any doc guard (confirmed green).
- The only durable wording that downstream phases should rely on is the
  GENIA_STATE 9.3 sentence above; the architecture-doc sentence is a
  convenience summary.
