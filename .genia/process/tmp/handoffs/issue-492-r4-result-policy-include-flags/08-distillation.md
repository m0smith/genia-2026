# === GENIA DISTILLATION / RECONCILIATION (issue #492 r4-result-policy-include-flags) ===

Follow docs/process/llm-system-prompt.md.

CHANGE NAME: issue #492 r4-result-policy-include-flags
CHANGE SLUG: issue-492-r4-result-policy-include-flags

GENIA_STATE.md is final authority.

Read: 00-preflight, 01-contract, 02-design, 03-failing-tests,
04-implementation, 06-doc-sync, 07-audit (all present). Branch check: on
`feature/issue-492-r4-result-policy-include-flags`, not `main`, matches
pre-flight. OK.

Goal: extract durable documentation into canonical docs and retire the
process artifacts. No new behavior; align to GENIA_STATE.md.

---

## 1. EXTRACTED DURABLE CONTENT

Durable facts worth keeping (all already captured in canonical docs - see
section 2):

- Contract: a lifecycle plan `result_policy` is inert data. The observability
  include flags `include_phase`, `include_scope`, `include_role`, and
  `include_source_location` are optional booleans; each explicit accepted
  value is preserved in normalized output; omitted flags default to `true`.
- `failure_order` accepts only `observed_order`.
- Error behavior: non-boolean include value, unknown result-policy field, and
  unsupported `failure_order` each raise `ValueError` with a deterministic
  path-specific diagnostic (e.g.
  `invalid lifecycle plan at plan.result_policy.include_phase: expected boolean, got symbol`).
- Invariant: for these fields, validation accepts a value iff normalization
  preserves it (accepted input round-trips to normalized output).
- Maturity: Experimental, Python reference host only; inert data, no execution.

Discarded (process-only, not migrated): phase logs, branch confirmations,
red/green command transcripts, planning text, the open/closed decision
narrative, and tool/cache notes.

---

## 2. DESTINATION FOR EACH ITEM

- Result-policy preservation contract + `failure_order` fix
  -> GENIA_STATE.md section 9.3 (DONE in doc-sync; authoritative).
- Architecture-level summary + issue #492 reference
  -> docs/architecture/lifecycle.md (DONE in doc-sync; defers to 9.3).
- Error/diagnostic behavior + invariants
  -> already implicit in GENIA_STATE 9.3 ("validates ... as booleans,
  preserving each explicit accepted value ... defaulting omitted flags to
  `true`") plus the existing deterministic-diagnostic statement. No further
  canonical edit required.
- Tested limitations (no runner/execution; inert data)
  -> already in GENIA_STATE 9.3 "Explicit limitations" list. Unchanged.

No new doc categories created. No handoff text migrated verbatim into docs.

---

## 3. FILES UPDATED (CANONICAL)

Updated during doc-sync (phase 06), confirmed sufficient here:
- GENIA_STATE.md (section 9.3): result-policy wording + test count 32 -> 35.
- docs/architecture/lifecycle.md: issue #492 ref + preservation clause.

No additional canonical edits needed at distillation. Code/tests already
committed in earlier phases:
- src/genia/lifecycle_plan.py (one-line preservation fix).
- tests/unit/test_lifecycle_plan.py (three preservation tests).

---

## 4. CONSISTENCY CHECK

- GENIA_STATE.md <-> code: aligned (preserve explicit booleans, default true,
  fixed failure_order).
- GENIA_RULES.md: no change needed (no semantics change).
- README.md / GENIA_REPL_README.md: no change needed (no user surface).
- docs/architecture/lifecycle.md: consistent, defers to 9.3.
- examples: unaffected.
- Tests green: lifecycle unit 35 passed; doc sync 92 passed.

No contradictions across canonical surfaces.

---

## 5. CLEANUP

Handoff files now redundant (durable content extracted to canonical docs):
- 00-preflight.md, 01-contract.md, 02-design.md, 03-failing-tests.md,
  04-implementation.md, 05-test-verification.md, 06-doc-sync.md, 07-audit.md,
  08-distillation.md, README.md.

The entire handoff directory
`.genia/process/tmp/handoffs/issue-492-r4-result-policy-include-flags/`
is SAFE TO DELETE after merge. Do NOT migrate these files into docs/.

Action required before merge (carried from audit, Issue 1):
- `git rm --cached` the three handoff files that were force-committed in
  earlier phases (03-failing-tests.md, 04-implementation.md,
  05-test-verification.md). They are gitignored (`.gitignore:83
  .genia/process/tmp/`) and must not be tracked. Keep them on disk only until
  the directory is deleted.
- Do not commit 00/01/02/06/07/08; they remain ignored.
- Commit the doc-sync edits (GENIA_STATE.md, docs/architecture/lifecycle.md)
  as the doc-sync/distillation commit.

---

## 6. COMPLEXITY CHECK

[x] Minimal and clear
[ ] Slightly expanded but justified
[ ] Too verbose

All durable content already lives in canonical docs; distillation only
confirms placement and schedules artifact cleanup.

---

## OUTPUT

1. Extracted durable content: result-policy include-flag preservation
   contract, `failure_order` fix, deterministic diagnostics, round-trip
   invariant, Experimental maturity.
2. Destination: GENIA_STATE.md 9.3 (authoritative) + docs/architecture/
   lifecycle.md (summary). Both already updated in doc-sync.
3. Files updated: GENIA_STATE.md, docs/architecture/lifecycle.md (doc-sync);
   src/genia/lifecycle_plan.py, tests/unit/test_lifecycle_plan.py (earlier
   phases).
4. Handoff directory safe to delete after merge; untrack the three
   force-committed handoff files first.
5. Discarded content worth noting: none of strategic value; only process logs.
