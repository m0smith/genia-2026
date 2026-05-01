# === GENIA IMPLEMENTATION PROMPT (LEAN) ===

Follow docs/process/llm-system-prompt.md.

Read:
- pre-flight document
- approved contract
- approved design
- failing-test output, if available

GENIA_STATE.md is final authority.

---

0. BRANCH CHECK

- Must NOT be on main
- Must match pre-flight branch
- If mismatch → STOP
- Report active branch before editing

---

Implement <CHANGE NAME>.

Goal:
Make the approved failing tests pass with the smallest safe change.

Rules:
- Do not redesign
- Do not expand scope
- Do not add behavior not in the contract
- Preserve existing behavior
- Follow the approved design
- Do not update docs in this step unless required by test fixtures
- If contract/design is unclear → STOP and report ambiguity

---

1. CHANGE PLAN

Before editing, list:
- files to modify
- files to add
- files to remove
- purpose of each change

---

2. IMPLEMENTATION

Implement only:
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