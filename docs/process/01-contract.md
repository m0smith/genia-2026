# === GENIA SPEC PROMPT (LEAN) ===

Follow docs/process/llm-system-prompt.md  
Read the pre-flight document for this change.

GENIA_STATE.md is the final authority.

---

0. BRANCH CHECK

- Must NOT be on main
- Must match pre-flight branch
- If mismatch → STOP

---

Write the implementation-ready contract for <CHANGE NAME>.

Rules:
- No implementation
- No scope expansion
- No new behavior beyond pre-flight
- Must remain host-independent

If it is not written here, it does not exist.

---

1. PURPOSE

Define the exact behavior of the change.

---

2. SCOPE (FROM PRE-FLIGHT)

Included:
- 

Excluded:
- 

---

3. BEHAVIOR

Define precisely:
- inputs
- outputs
- state changes (if any)

---

4. SEMANTICS

Define:
- evaluation behavior
- matching behavior (if applicable)
- edge cases
- error behavior

---

5. FAILURE

Define:
- what causes failure
- resulting error
- what does NOT happen

---

6. INVARIANTS

List truths that must always hold:
- 
- 

---

7. EXAMPLES

Minimal:
- 

Real:
- 

---

8. NON-GOALS

Explicitly NOT included:
- 
- 

---

9. DOC NOTES

- How GENIA_STATE.md should describe this
- Mark as: experimental / partial / stable

---

10. FINAL CHECK

- Precise and testable
- No implementation details
- No scope expansion
- Consistent with GENIA_STATE.md

---

OUTPUT:
Clean structured contract only.
Prefer minimal wording. Avoid repetition.