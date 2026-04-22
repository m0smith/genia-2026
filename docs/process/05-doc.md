# === GENIA DOC SYNC PROMPT ===

READ FIRST:

* Pre-flight document
* Spec output
* Design output
* Implementation changes
* Test results
* AGENTS.md
* GENIA_STATE.md (final authority)
* GENIA_RULES.md
* GENIA_REPL_README.md
* README.md

---

0. BRANCH DISCIPLINE

---

Before doing anything:

* Verify current branch is NOT `main`
* Verify branch matches Pre-flight
* If mismatch → STOP
* Report active branch before proceeding

---

1. PURPOSE

---

Synchronize all documentation with the **actual implemented behavior**.

This step defines the **official, published truth** of the system.

No new behavior. No speculation.

---

2. SCOPE LOCK

---

Update docs ONLY for:

* behavior defined in Spec
* behavior implemented in code
* behavior verified by tests

Must NOT:

* document future features
* imply unimplemented capabilities
* expand scope
* “clean up everything” unrelated to this change

---

3. SOURCE OF TRUTH RULE

---

* GENIA_STATE.md is the final authority
* If any doc conflicts → GENIA_STATE.md must be corrected OR other docs aligned

---

4. REQUIRED DOC UPDATES

---

Update as needed:

### Core

* GENIA_STATE.md
* GENIA_RULES.md
* README.md
* GENIA_REPL_README.md

### Supporting

* docs/cheatsheet/*
* docs/host-interop/*

### Examples

* examples/* (if affected)

---

5. UPDATE STRATEGY

---

For each affected file:

* locate impacted sections
* update only what changed
* preserve existing structure and tone
* avoid duplication

---

6. GENIA_STATE.md (CRITICAL)

---

Ensure it:

* reflects exact implemented behavior
* includes feature maturity (Experimental / Partial / Stable)
* documents limitations and missing pieces
* does NOT overstate capabilities

---

7. GENIA_RULES.md

---

Update only if:

* semantics changed
* pattern behavior changed
* evaluation rules changed

Must remain precise and minimal.

---

8. README.md

---

Update only if:

* user-facing behavior changed
* new capability is exposed
* examples need adjustment

Keep concise. No deep internals.

---

9. BOOK / GUIDE DOCS

---

Update relevant sections to:

* explain the feature clearly
* match actual behavior
* include accurate examples

If behavior is partial → say so explicitly.

---

10. EXAMPLES

---

Ensure:

* all examples compile/run (if applicable)
* outputs match real behavior
* no reliance on unimplemented features

Update or add minimal examples as needed.

---

11. TRUTHFULNESS CHECK

---

Verify:

Docs do NOT:

* exaggerate features
* imply completeness when partial
* describe unimplemented behavior

Docs DO:

* reflect reality
* clearly state limitations
* remain consistent across files

---

12. CROSS-FILE CONSISTENCY

---

Ensure alignment across:

* GENIA_STATE.md
* GENIA_RULES.md
* GENIA_REPL_README.md
* README.md
* examples

No contradictions allowed.

---

13. CHANGE SUMMARY

---

List:

* files updated
* sections changed
* new examples added
* removed or corrected statements

---

14. COMPLEXITY CHECK

---

Docs are:

[ ] Minimal and clear
[ ] Slightly expanded but justified
[ ] Too verbose / redundant

## Explain:

---

15. FINAL CHECK

---

Before finishing, confirm:

* all docs match implementation
* GENIA_STATE.md is accurate and complete
* examples are correct
* no speculative content exists
* ready for Audit prompt

---

## OUTPUT

Provide:

1. Summary of doc changes
2. Files updated
3. Key wording added/modified
4. Any remaining risks or ambiguities

No redesign. No speculation. Only truth.
