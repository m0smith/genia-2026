# === GENIA PRE-FLIGHT PROMPT (LEAN) ===

Follow docs/process/llm-system-prompt.md.

CHANGE NAME: <short name>
CHANGE SLUG: <short-kebab-name>

GENIA_STATE.md is final authority.

HARD STOP:
Produce pre-flight only.
Do not create branches, edit files, run tests, write contracts, or commit.

---

# HANDOFF

Handoff directory:
.genia/process/tmp/handoffs/<change-slug>/

Write output to:
.genia/process/tmp/handoffs/<change-slug>/00-preflight.md

This file must be created.

---

0. BRANCH

Branch required: YES
Branch type: feature / fix / refactor / docs / exp
Branch slug: <short-kebab-name>
Expected branch: <branch-type>/<branch-slug>
Base branch: main

Rules:
- No work on main
- Branch must exist before contract
- One branch per change

---

1. SCOPE LOCK

Includes:
-

Excludes:
-

---

2. SOURCE OF TRUTH

Authoritative:
- GENIA_STATE.md
- GENIA_RULES.md
- README.md
- AGENTS.md

Additional relevant:
-

Notes:
-

---

3. FEATURE MATURITY

Stage:
[ ] Experimental
[ ] Partial
[ ] Stable

Doc wording:
-

---

## 3a. Portability Analysis

Follow docs/process/extensions/portability-analysis.md.

Complete this before proceeding to Contract.

---

4. CONTRACT vs IMPLEMENTATION

Portable contract:
-

Python implementation today:
-

Not implemented:
-

---

5. TEST STRATEGY

Core invariants:
-

Expected behavior:
-

Failure cases:
-

Test approach:
-

---

6. EXAMPLES

Minimal:
-

Real:
-

---

7. COMPLEXITY CHECK

[ ] Adding complexity
[ ] Revealing structure

Justification:
-

---

8. CROSS-FILE IMPACT

Files likely to change:
-

Risk of drift:
[ ] Low
[ ] Medium
[ ] High

---

9. DOC DISTILLATION CHECK

Creates process artifacts?
[ ] YES → run Doc Distillation
[ ] NO

Adds docs/design or docs/architecture files?
[ ] YES → classify KEEP / EXTRACT / DELETE
[ ] NO

Doc drift risk:
[ ] Low
[ ] Medium
[ ] High

---

10. PHILOSOPHY CHECK

- preserves minimalism? YES / NO
- avoids hidden behavior? YES / NO
- keeps semantics out of host? YES / NO
- aligns with pattern-matching-first? YES / NO

Notes:
-

---

11. PROMPT PLAN

Pipeline:
- Preflight
- Contract
- Design
- Test
- Implementation
- Docs
- Audit
- Distillation

---

FINAL GO / NO-GO

Ready to proceed?
YES / NO

Missing:
-