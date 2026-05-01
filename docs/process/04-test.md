# === GENIA TEST PROMPT (LEAN) ===

Follow docs/process/llm-system-prompt.md.

Read:
- pre-flight document
- approved contract
- approved design
- implementation changes

GENIA_STATE.md is final authority.

---

0. BRANCH CHECK

- Must NOT be on main
- Must match pre-flight branch
- If mismatch → STOP
- Report active branch before editing

---

Test <CHANGE NAME>.

Goal:
Verify the implementation matches the contract exactly.

Rules:
- Do not redesign
- Do not expand scope
- Do not add behavior
- Do not weaken tests to fit implementation
- Test only contract-defined behavior
- If contract/design is unclear → STOP and report ambiguity

---

1. TEST PLAN

Before editing, list:
- files to add or update
- behavior groups to test
- contract invariants covered

---

2. REQUIRED COVERAGE

Cover:
- happy path
- edge cases
- failure behavior
- nearby regression risks

Tests must:
- assert concrete behavior
- fail on regression
- reflect current runtime reality
- avoid duplicating implementation logic

Tests must NOT:
- assume unimplemented behavior
- lock in accidental behavior
- rely on host quirks unless contract-approved

---

3. EXECUTION

Run the smallest useful set:
- new tests
- nearest related tests
- parser/runtime/CLI/example checks if affected
- full suite if practical

---

4. FAILURE HANDLING

If tests fail:
- identify exact cause
- classify as implementation bug, test bug, or contract/design ambiguity
- do not silently weaken expectations
- recommend smallest corrective action

Only make implementation changes if the fix is tiny, obvious, and explicitly reported.

---

5. DOC INPUT

Note anything docs must reflect:
- caveats
- partial behavior
- examples
- sharp edges

---

6. COMPLEXITY CHECK

Mark one:

[ ] Minimal but sufficient
[ ] Broader than ideal but justified
[ ] Too weak
[ ] Too broad

Explain only if not minimal/sufficient.

---

OUTPUT:
1. Test summary
2. Files changed
3. Commands run
4. Results
5. Failures/gaps/follow-up

No redesign. No speculation. No scope expansion.