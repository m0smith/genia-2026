# === GENIA DESIGN PROMPT ===

You are working in the Genia repo.

Before doing anything, read:
* Pre-flight document
- Spec output
- AGENTS.md
- GENIA_STATE.md
- GENIA_RULES.md
- GENIA_REPL_README.md
- README.md

GENIA_STATE.md is the final authority when files conflict.

Do not invent implemented behavior.
Do not expand scope.
Do not introduce new syntax unless the spec explicitly requires it.
Keep documentation truthful and current.
If this change affects behavior, update relevant tests and docs.

---

0. BRANCH DISCIPLINE

---

Before doing anything:

* Verify current branch is NOT `main`
* Verify branch matches Pre-flight
* If mismatch → STOP

---

Create the design for implementing the approved spec for <CHANGE NAME>.

Map the spec to:
- files/modules to change
- functions/classes/data structures affected
- minimal algorithm
- migration/compatibility concerns
- test locations
- docs locations

Do not implement.
Do not change the spec.
Do not add behavior not already specified.

---

1. PURPOSE

---

Translate the Spec into structure.

This defines **how the behavior will be organized**, not what it does.

No code implementation.

---

2. SCOPE LOCK

---

Must follow Spec exactly.

* Do NOT add behavior
* Do NOT expand scope
* Do NOT reinterpret requirements

If Spec is unclear → STOP and report

---

3. ARCHITECTURE OVERVIEW

---

Describe:

* Where this fits in the system
* What modules/components are involved
* How data flows through the system

---

4. FILE / MODULE CHANGES

---

List all changes:

* ## New files:

* ## Modified files:

* ## Removed files (if any):

---

5. DATA SHAPES

---

Define all relevant data:

* Structures
* Value templates (refinement, shape, variant, etc.)
* Message formats (if applicable)

Be explicit and consistent with Spec.

---

6. FUNCTION / INTERFACE DESIGN

---

Define:

* Function names
* Parameters
* Return values
* Expected behavior (brief, not full spec)

No implementation logic.

---

7. CONTROL FLOW

---

Describe:

* Execution flow
* Key decision points
* Pattern matching structure (if used)

---

8. ERROR HANDLING DESIGN

---

Define:

* Where errors are detected
* How they are propagated
* What boundaries enforce correctness

Must match Spec failure behavior.

---

9. INTEGRATION POINTS

---

Describe interaction with:

* existing modules
* runtime/interpreter
* CLI / REPL / flow system (if applicable)

---

10. TEST DESIGN INPUT

---

Prepare for test stage:

* What needs to be tested
* Key invariants (from Spec)
* Edge cases to cover

---

11. DOC IMPACT

---

Identify:

* GENIA_STATE.md changes
* Docs/book sections affected
* Examples that must be added/updated

---

12. CONSTRAINTS

---

Must:

* follow existing patterns
* preserve minimalism
* avoid unnecessary abstraction

Must NOT:

* introduce new concepts not in Spec
* depend on host-specific behavior
* change existing semantics

---

13. COMPLEXITY CHECK

---

Is this design:

[ ] Minimal
[ ] Necessary
[ ] Over-engineered

## Explain:

---

14. FINAL CHECK

---

Before finishing:

* Matches Spec exactly
* No new behavior introduced
* Structure is clear and implementable
* Ready for implementation without ambiguity

---

## OUTPUT

Produce a clean, structured design document.

No code. No speculation. No scope expansion.
