# === GENIA IMPLEMENTATION PROMPT ===

READ FIRST:

* Pre-flight document
* Spec output
* Design output

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

0. BRANCH DISCIPLINE

---

Before doing anything:

* Verify current branch is NOT `main`
* Verify branch matches Pre-flight
* If mismatch → STOP
* Report active branch before proceeding

---

Implement <CHANGE NAME>.

Your only job is to make the approved failing tests pass.

Rules:
- Do not redesign.
- Do not expand scope.
- Do not add new behavior.
- Prefer minimal changes.
- Preserve existing passing behavior.
- Update no docs in this step unless required by test fixtures.

Run:
- the new tests
- the nearest existing related tests
- the full suite if practical

Report exactly what changed and the test results.

---

1. PURPOSE

---

Implement exactly what is defined in the Spec and organized by the Design.

This step is for code changes only.

---

2. SCOPE LOCK

---

Allowed:

* implement the defined behavior
* make the minimal required code changes
* add any small supporting internal changes required by the Design

Forbidden:

* redesigning the feature
* adding extra behavior
* expanding scope
* “while I’m here” cleanup unrelated to this change
* changing semantics not defined in the Spec

If Spec or Design is unclear:
→ STOP and report the ambiguity
Do NOT invent behavior.

---

3. IMPLEMENTATION RULES

---

Must:

* follow the Design exactly
* preserve existing semantics unless the Spec explicitly changes them
* keep changes minimal and local
* follow existing project patterns and naming
* keep behavior portable where required by the Spec

Must NOT:

* add hidden behavior
* introduce host-specific semantics into the language contract
* claim support for behavior not actually implemented
* update docs in this step beyond minimal inline comments if truly necessary

---

4. REQUIRED WORK

---

Implement:

* the behavior defined in the Spec
* the structures/interfaces defined in the Design
* the error behavior defined in the Spec
* the integration points defined in the Design

Also ensure:

* examples continue to run if affected
* existing tests are not silently invalidated

---

5. CODE CHANGE PLAN

---

List before editing:

* files to modify
* files to add
* files to remove (if any)

For each file, state its purpose briefly.

---

6. SAFETY CHECKS

---

Before finalizing, verify:

* no scope expansion occurred
* no unrelated files were changed
* no behavior beyond the Spec was introduced
* failure behavior matches the Spec
* names and structures match the Design

---

7. OUTPUT FORMAT

---

Provide:

1. Summary of implemented changes
2. Files changed
3. Any blocked items or ambiguities
4. Anything that must be verified in the Test step

Do NOT provide a redesign.
Do NOT provide speculative future work unless something is blocked.

---

8. COMPLEXITY CHECK

---

Confirm whether the implementation is:

[ ] Minimal and direct
[ ] Slightly broader than ideal but necessary
[ ] Too broad

If broader than ideal, explain why.

---

9. FINAL CHECK

---

Before finishing, confirm:

* Implementation matches Spec
* Implementation matches Design
* No unapproved behavior added
* Ready for Test prompt
