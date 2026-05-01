# === GENIA FAILING TEST PROMPT (LEAN) ===

Follow docs/process/llm-system-prompt.md.

CHANGE NAME: <short name>
CHANGE SLUG: <short-kebab-name>

GENIA_STATE.md is final authority.

---

# HANDOFF

Read:
- .genia/process/tmp/handoffs/<change-slug>/00-preflight.md
- .genia/process/tmp/handoffs/<change-slug>/01-contract.md
- .genia/process/tmp/handoffs/<change-slug>/02-design.md

If any are missing → STOP and report.

Write output to:
.genia/process/tmp/handoffs/<change-slug>/03-failing-tests.md

This file must be created.

---

0. BRANCH CHECK

- Must NOT be on main
- Must match pre-flight branch
- If mismatch → STOP

---

Write failing tests for <CHANGE NAME>.

Goal:
Define tests that prove the contract and currently FAIL.

Rules:
- Tests must fail before implementation
- Tests must prove behavior, not just execute code
- Cover happy path, edge cases, and failure cases
- Do not modify implementation (except minimal fixtures if required)
- Do not introduce behavior not in the contract
- If contract/design is unclear → STOP and report

---

1. TEST PLAN

List:
- files to add/update
- behavior groups to test
- contract invariants covered

---

2. REQUIRED COVERAGE

Include:
- happy path
- edge cases (boundary, empty/minimal, unusual valid inputs)
- failure cases (invalid inputs, invalid shapes/patterns)
- nearby regression risks

Tests must:
- assert concrete outputs
- fail on regression
- reflect current runtime reality
- avoid duplicating implementation logic

---

3. EXECUTION

Run the smallest useful set:
- new tests
- nearest related tests

Limit failures to 20. If exceeded → STOP and report.

---

4. FAILURE EVIDENCE

Classify each failure:
- expected failure (correct per contract)
- test bug
- contract/design ambiguity

Report:
- commands run
- failing tests (names and summaries)
- why they fail relative to contract

---

OUTPUT:

1. Test plan
2. Files changed
3. Commands run
4. Failing evidence
5. Ambiguities/blockers

No implementation. No redesign. No scope expansion.