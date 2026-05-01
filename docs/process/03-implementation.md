# === GENIA IMPLEMENTATION PROMPT (LEAN) ===

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
- .genia/process/tmp/handoffs/<change-slug>/03-failing-tests.md

If any are missing → STOP and report.

Write output to:
.genia/process/tmp/handoffs/<change-slug>/04-implementation.md

This file must be created.

---

0. BRANCH CHECK

- Must NOT be on main
- Must match pre-flight branch
- If mismatch → STOP

---

Implement <CHANGE NAME>.

Goal:
Make the approved failing tests pass with the smallest safe change.

Rules:
- Do not redesign
- Do not expand scope
- Do not add behavior not in the contract
- Preserve existing behavior
- Follow the approved design exactly
- Keep changes minimal and local
- Do not update docs in this step unless required by tests
- If contract/design is unclear → STOP and report

---

1. CHANGE PLAN

Before editing, list:
- files to modify
- files to add
- files to remove
- purpose of each change

---

2. IMPLEMENTATION

Implement ONLY:
- behavior defined in the contract
- structures/interfaces defined in the design
- failure behavior defined in the contract
- integration points defined in the design

No “while I’m here” cleanup.

---

3. VALIDATION

Run:
- new failing tests
- nearest related tests
- full suite if practical

Verify:
- no unrelated files changed
- no scope expansion
- failure behavior matches contract
- names/structures match design

If more than 20 tests fail → STOP and report instead of continuing.

---

4. COMPLEXITY CHECK

Mark one:

[ ] Minimal and direct  
[ ] Broader than ideal but necessary  
[ ] Too broad  

Explain only if not minimal.

---

OUTPUT:

1. Summary of changes  
2. Files changed  
3. Tests run and results  
4. Blockers or ambiguities  
5. Anything for the Test step to verify  

No redesign. No speculative future work.