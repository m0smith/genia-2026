# === GENIA PRE-FLIGHT ===

CHANGE NAME: <short name of change>

---

You are working in the Genia repo.

Before doing anything, read:
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

--------------------------------
HARD STOP — PRE-FLIGHT ONLY
--------------------------------

You MUST STOP after producing the pre-flight output.

You are NOT allowed to:
- create branches
- run tests
- write spec files
- modify any files
- run the spec runner
- commit anything
- proceed to spec/design/implementation/audit

If you do any of the above, the response is INVALID.

After pre-flight, WAIT for the next prompt.

Do NOT assume the next step.

If you find yourself writing YAML, code, or running commands,
you have already gone too far. Stop immediately.

---

0. BRANCH

---

Branch required:
YES

Branch type:
[ ] feature
[ ] fix
[ ] refactor
[ ] docs
[ ] exp

Branch slug: <short-kebab-name>

Expected branch: <branch-type>/<branch-slug>

Base branch:
main

Rules:

* No work begins on `main`
* Branch must be created before Spec
* One branch per change

---

1. SCOPE LOCK

---

## Change includes:

## Change does NOT include:

---

2. SOURCE OF TRUTH

---

Authoritative files:

* GENIA_STATE.md (final authority)
* GENIA_RULES.md
* README.md
* AGENTS.md

## Additional relevant:

## Notes:

---

3. FEATURE MATURITY

---

Stage:
[ ] Experimental
[ ] Partial
[ ] Stable

## How this must be described in docs:

---

4. CONTRACT vs IMPLEMENTATION

---

## Contract (portable semantics):

## Implementation (Python today):

## Not implemented:

---

5. TEST STRATEGY

---

## Core invariants:

## Expected behaviors:

## Failure cases:

## How this will be tested:

---

6. EXAMPLES

---

## Minimal example:

## Real example (if applicable):

---

7. COMPLEXITY CHECK

---

Is this:
[ ] Adding complexity
[ ] Revealing structure

## Justification:

---

8. CROSS-FILE IMPACT

---

## Files that must change:

*

Risk of drift:
[ ] Low
[ ] Medium
[ ] High

---

9. PHILOSOPHY CHECK

---

Does this:

* preserve minimalism? YES / NO
* avoid hidden behavior? YES / NO
* keep semantics out of host? YES / NO
* align with pattern-matching-first? YES / NO

## Notes:

---

10. PROMPT PLAN

---

Will use full pipeline?
YES

Steps:

* Preflight
* Spec
* Design
* Test
* Implementation
* Docs
* Audit

---

## FINAL GO / NO-GO

Ready to proceed?
YES / NO

## If NO, what is missing:
