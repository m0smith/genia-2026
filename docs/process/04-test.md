# === GENIA TEST PROMPT ===

READ FIRST:

* Pre-flight document
* Contract output
* Design output
* Implementation changes

Do a Genia pre-flight for issue/change: <CHANGE NAME>.

Read the required project docs first.

Output:
- scope includes
- scope excludes
- source of truth files
- current behavior
- desired behavior
- non-goals
- affected files
- risk of drift
- test strategy
- docs impact
- go/no-go recommendation

Do not write code.
Do not redesign the feature.
---

0. BRANCH DISCIPLINE

---

Before doing anything:

* Verify current branch is NOT `main`
* Verify branch matches Pre-flight
* If mismatch → STOP
* Report active branch before proceeding

---
Write failing tests for <CHANGE NAME> based only on the approved Contract and design.

Rules:
- Tests must fail before implementation.
- Tests must prove the behavior, not just exercise code.
- Include edge cases and regression cases.
- Do not change implementation code except test fixtures if needed.
- Do not introduce behavior not in the Contract.

Run the relevant tests and report the failing evidence.

---

1. PURPOSE

---

Verify that the implementation matches the Contract exactly.

This step is for tests and verification only.

Do NOT redesign.
Do NOT add new behavior.
Do NOT expand scope.

---

2. SCOPE LOCK

---

Test only what is defined in the Contract and implemented in this change.

Must cover:

* required behavior
* invariants
* edge cases
* failure cases

Must NOT:

* introduce new semantics
* test speculative future behavior
* rewrite implementation during the test step unless a tiny, obvious correction is required and explicitly called out

If the Contract is unclear:
→ STOP and report the ambiguity

---

3. TEST GOALS

---

Prove:

* the feature behaves as specified
* failure behavior matches the Contract
* edge cases are handled correctly
* no regression was introduced in nearby behavior

---

4. REQUIRED COVERAGE

---

Include tests for:

1. Happy path

* normal expected usage
* representative successful cases

2. Edge cases

* boundary values
* empty/minimal cases
* structurally unusual but valid cases

3. Failure cases

* invalid inputs
* invalid shapes/patterns
* expected errors or rejection behavior

4. Regression coverage

* nearby existing behavior that could break because of this change

---

5. TEST DESIGN RULES

---

Tests must:

* be driven by the Contract invariants
* assert concrete behavior, not vague success
* fail when behavior regresses
* reflect current language/runtime reality
* avoid duplicating the implementation logic inside the test

Tests must NOT:

* assume unimplemented capabilities
* lock in accidental behavior not stated in the Contract
* rely on host quirks unless explicitly part of the implementation boundary

---

6. TEST PLAN

---

Before writing tests, list:

* files to add or update
* what each test group verifies
* which Contract invariants each group covers

---

7. EXECUTION

---

Run the relevant test commands.

Also run any targeted checks needed for:

* parser behavior
* interpreter/runtime behavior
* CLI/REPL behavior
* example execution
* regression suites near the changed area

Use the smallest set of commands that gives real confidence.

---

8. RESULTS

---

Report:

* tests added or changed
* commands run
* pass/fail results
* any failures found
* whether failures are implementation bugs, test bugs, or contract/design ambiguity

---

9. FAILURE HANDLING

---

If tests fail:

* identify the exact cause
* do NOT silently weaken the test
* do NOT change expected behavior unless the Contract was wrong
* recommend the smallest corrective action

If implementation changes are required:

* state that clearly
* defer broader fixes to the next implementation pass unless the fix is tiny and obvious

---

10. DOC / EXAMPLE VALIDATION INPUT

---

Identify anything the Docs step must reflect, including:

* partial behavior
* caveats
* sharp edges
* any example updates required

---

11. COMPLEXITY CHECK

---

Confirm whether the test suite is:

[ ] Minimal but sufficient
[ ] Slightly broader than ideal but justified
[ ] Too weak
[ ] Too broad

## Explain:

---

12. FINAL CHECK

---

Before finishing, confirm:

* tests cover spec-defined behavior
* tests cover failure behavior
* tests cover edge cases
* tests provide regression protection
* results are real, not assumed
* ready for Docs prompt

---

## OUTPUT

Provide:

1. Test summary
2. Files changed
3. Commands run
4. Results
5. Gaps or follow-up needed

No redesign. No speculation. No scope expansion.
