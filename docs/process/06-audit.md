# === GENIA AUDIT PROMPT (LEAN) ===

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
- .genia/process/tmp/handoffs/<change-slug>/04-implementation.md
- .genia/process/tmp/handoffs/<change-slug>/06-doc-sync.md

If any are missing → STOP and report.

Write output to:
.genia/process/tmp/handoffs/<change-slug>/07-audit.md

This file must be created.

---

0. BRANCH CHECK

Verify:
- not on main
- branch matches change
- no unrelated changes

If violated → report.

---

Audit <CHANGE NAME>.

Assume the implementation is wrong until proven correct.

If change is low risk, focus only on:
- contract vs implementation
- tests vs contract
- docs vs behavior

Rules:
- Do not redesign
- Do not expand scope
- Do not introduce new behavior
- Focus on correctness, consistency, and truth

---

1. SUMMARY

Status:
[ ] PASS
[ ] PASS WITH ISSUES
[ ] FAIL

Summary (1–3 sentences):

---

2. CORE CHECKS

Verify:

- Contract ↔ Implementation match
- Design ↔ Implementation match
- Tests ↔ Contract coverage
- Docs ↔ actual behavior
- No scope expansion
- Edge cases handled

Mismatches:
-

---

3. TEST QUALITY

Check:
- covers core behavior, edge cases, failure cases
- asserts concrete results
- fails on regression

Gaps / risks:
-

---

4. DOC TRUTH

Docs must:
- reflect implemented behavior only
- clearly mark partial features
- avoid implying future capability

Examples must:
- match real syntax/output
- not rely on unimplemented features

Violations:
-

---

5. CONSISTENCY

Check alignment across:
- GENIA_STATE.md
- GENIA_RULES.md (if relevant)
- GENIA_REPL_README.md (if relevant)
- README.md
- examples

Drift:
-

Risk level:
[ ] Low
[ ] Medium
[ ] High

---

6. COMPLEXITY

[ ] Minimal and necessary
[ ] Slightly complex but justified
[ ] Over-engineered

Explain only if not minimal.

---

7. ISSUES

For each:

Severity:
[ ] Critical
[ ] Major
[ ] Minor

- File(s):
- Problem:
- Why it matters:
- Minimal fix:

---

8. RECOMMENDED FIXES

1.
2.
3.

Rules:
- smallest possible fixes
- no redesign

---

9. VALIDATION

Confirm:
- tests were executed
- results observed
- examples verified
- docs checked against behavior

---

FINAL VERDICT:

Ready to merge?
YES / NO

If NO:
- blocking issues
- follow-up prompts needed