# === GENIA AUDIT / TRUTH REVIEW ===

CHANGE NAME: <short name of change>

---

0. BRANCH CHECK

---

Verify:

* Work was NOT done on `main`
* Branch name matches change
* Scope matches branch intent
* No unrelated changes included

## Violations:

---

1. INPUTS (REQUIRED)

---

Must read completely before auditing:

Authoritative:

* AGENTS.md
* GENIA_STATE.md (final authority)
* GENIA_RULES.md
* GENIA_REPL_README.md
* README.md

Relevant (only those touched):

* docs/cheatsheet/*
* docs/host-interop/*
* spec/*

Pipeline artifacts:

* Spec output
* Design output
* Implementation changes
* Test changes
* Docs sync changes

Notes:

* Do not assume anything not present in these files
* If sources conflict → GENIA_STATE.md wins

---

2. SCOPE LOCK

---

This audit:

* verifies correctness
* detects drift
* enforces truth alignment
* proposes minimal fixes

This audit does NOT:

* redesign features
* expand scope
* introduce new behavior
* speculate future capabilities

If a fix requires redesign:
→ mark as FAIL and stop at recommendations

---

3. AUDIT SUMMARY

---

Status:
[ ] PASS
[ ] PASS WITH ISSUES
[ ] FAIL

Summary:

* <1–3 sentences, brutally honest>

---

4. SPEC ↔ IMPLEMENTATION CHECK

---

Verify:

* behavior matches Spec exactly
* no silent additions
* no missing required behavior
* edge cases handled as defined

## Mismatches:

---

5. DESIGN ↔ IMPLEMENTATION CHECK

---

Verify:

* structure matches Design
* no architectural drift
* no extra abstractions added

## Mismatches:

---

6. TEST VALIDITY

---

Verify:

* tests cover:

  * core behavior
  * edge cases
  * failure cases
* tests assert correct outputs (not vague success)
* tests fail if behavior regresses

## Missing / weak tests:

## False confidence risks:

---

7. TRUTHFULNESS REVIEW

---

Strict checks:

Docs must:

* describe only implemented behavior
* clearly label partial features
* not imply future capabilities
* match actual runtime behavior

Examples must:

* run if marked runnable
* match real syntax/output
* not rely on unimplemented features

## Violations:

---

8. CROSS-FILE CONSISTENCY

---

Verify alignment across:

* GENIA_STATE.md
* GENIA_RULES.md
* GENIA_REPL_README.md
* README.md
* docs/cheatsheet/*
* host/spec docs (if relevant)

## Drift detected:

Risk level:
[ ] Low
[ ] Medium
[ ] High

---

9. PHILOSOPHY CHECK

---

Does this change:

* preserve minimalism? YES / NO
* avoid hidden behavior? YES / NO
* keep semantics out of host? YES / NO
* align with pattern-matching-first? YES / NO

## Violations:

---

10. COMPLEXITY AUDIT

---

Is this change:

[ ] Minimal and necessary
[ ] Slightly complex but justified
[ ] Over-engineered

## Justification:

## Anything removable:

---

11. ISSUE LIST

---

For each issue:

Severity:
[ ] Critical (incorrect behavior / lies in docs)
[ ] Major (drift / missing coverage)
[ ] Minor (clarity / style)

* File(s):
* Problem:
* Why it matters:
* Minimal fix:

---

12. RECOMMENDED FIXES (ORDERED)

---

1.
2.
3.

Rules:

* smallest possible corrections
* no redesign
* no feature creep

---

13. OPTIONAL PATCH

---

Apply ONLY if:

* fix is obvious
* fix is local
* no redesign required

Otherwise:
→ skip and defer to next prompt

---

14. VALIDATION

---

Must confirm:

* tests executed
* results observed
* examples verified
* docs checked against real behavior

## Evidence:

---

## FINAL VERDICT

Ready to merge?
YES / NO

If NO:

* blocking issues:
* required follow-up prompts:
