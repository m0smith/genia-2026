# === GENIA DESIGN PROMPT (LEAN) ===

Follow docs/process/llm-system-prompt.md.

CHANGE NAME: <short name>
CHANGE SLUG: <short-kebab-name>

GENIA_STATE.md is final authority.

Prefer concise wording. Avoid repeating contract text unless needed for design clarity.

---

# HANDOFF

Read:
- .genia/process/tmp/handoffs/<change-slug>/00-preflight.md
- .genia/process/tmp/handoffs/<change-slug>/01-contract.md

If any are missing → STOP and report.

Write output to:
.genia/process/tmp/handoffs/<change-slug>/02-design.md

This file must be created.

---

0. BRANCH CHECK

- Must NOT be on main
- Must match pre-flight branch
- If mismatch → STOP

---

Create the implementation design for <CHANGE NAME>.

Rules:
- Do not implement
- Do not change the contract
- Do not add behavior
- If the contract is unclear → STOP and report the ambiguity
- Keep the design host-independent unless the contract explicitly says otherwise

---

1. PURPOSE

Translate the contract into implementation structure.

This defines how the behavior is organized, not new behavior.

---

2. SCOPE LOCK

Contract includes:
-

Contract excludes:
-

Do not expand scope.

---

3. ARCHITECTURE

Describe:
- where this fits
- affected components
- data flow
- integration points

---

4. FILE PLAN

New files:
-

Modified files:
-

Removed files:
-

---

5. DATA / INTERFACE DESIGN

Define:
- relevant data shapes
- value templates, variants, message formats if applicable
- functions/classes/interfaces affected
- parameters and return values

No implementation logic.

---

6. CONTROL / ERROR FLOW

Describe:
- execution flow
- pattern matching or decision structure
- where errors are detected
- how errors propagate
- boundaries that enforce correctness

Must match contract failure behavior.

---

7. TEST PLAN INPUT

List:
- invariants to test
- edge cases
- regression risks
- test files/locations

---

8. DOC IMPACT

Identify required updates:
- GENIA_STATE.md
- GENIA_RULES.md if needed
- GENIA_REPL_README.md if needed
- README.md if needed
- docs/book or other docs if needed

---

9. COMPLEXITY CHECK

Mark one:

[ ] Minimal
[ ] Necessary
[ ] Over-engineered

Explain briefly.

---

10. FINAL CHECK

Confirm:
- matches contract exactly
- no new behavior
- no host-specific assumptions
- ready for implementation

---

OUTPUT:
Clean structured design only.
No code. No speculation. No scope expansion.