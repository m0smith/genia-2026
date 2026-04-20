# === GENIA SPEC PROMPT ===

READ FIRST:

* AGENTS.md
* GENIA_STATE.md (final authority)
* GENIA_RULES.md
* README.md

Then read:

* Pre-flight document for this change

---

0. BRANCH DISCIPLINE

---

Before doing anything:

* Verify current branch is NOT `main`
* Verify branch matches Pre-flight
* If mismatch → STOP

---

1. PURPOSE

---

Define the exact behavior of the change.

This is the **source of truth** for all later steps.

No implementation allowed.

---

2. SCOPE (FROM PRE-FLIGHT)

---

Respect scope lock:

## Included:

## Excluded:

Do NOT expand scope.

---

3. BEHAVIOR DEFINITION

---

Describe:

* What the feature does
* Inputs
* Outputs
* State changes (if any)

---

4. SEMANTICS

---

Define:

* Evaluation behavior
* Matching behavior (if applicable)
* Error behavior
* Edge case handling

Be explicit.

---

5. FAILURE BEHAVIOR

---

Define:

* What causes failure
* What error is produced
* What does NOT happen on failure

---

6. INVARIANTS

---

List truths that must always hold:

*
*

These drive tests later.

---

7. EXAMPLES

---

Minimal:

*

Real:

*

Must be consistent with current language behavior.

---

8. NON-GOALS

---

Explicitly state what this does NOT do:

*
*

---

9. IMPLEMENTATION BOUNDARY

---

This spec MUST:

* describe behavior independent of host
* NOT assume Python specifics
* remain portable

---

10. DOC REQUIREMENTS

---

State how this must appear in docs:

* GENIA_STATE.md wording
* Whether marked experimental/partial/stable
* Any warnings needed

---

11. COMPLEXITY CHECK

---

Is this:

[ ] Minimal
[ ] Necessary
[ ] Overly complex

## Explain:

---

12. FINAL CHECK

---

Before finishing:

* No implementation details included
* No scope expansion
* Consistent with GENIA_STATE.md
* Behavior is precise and testable

---

## OUTPUT

Produce a clean, structured spec.

No code. No design. No implementation.

If it is not written here, it does not exist.