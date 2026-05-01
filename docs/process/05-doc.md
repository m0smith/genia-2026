# === GENIA DOC SYNC PROMPT (LEAN) ===

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

If any are missing → STOP and report.

Write output to:
.genia/process/tmp/handoffs/<change-slug>/06-doc-sync.md

This file must be created.

---

0. BRANCH CHECK

- Must NOT be on main
- Must match pre-flight branch
- If mismatch → STOP

---

Sync docs for <CHANGE NAME>.

Goal:
Make documentation match the actual implemented and tested behavior.

Rules:
- Document only what is implemented and verified by tests
- Do not add future behavior
- Do not expand scope
- Keep updates minimal and local
- Examples must match real syntax/output

---

1. SCOPE

Update ONLY for:
- contract-defined behavior
- implemented code
- verified test results

Do NOT:
- document unimplemented features
- “clean up everything” outside scope

---

2. FILES TO UPDATE

Core:
- GENIA_STATE.md (authoritative)
- GENIA_RULES.md (only if semantics changed)
- GENIA_REPL_README.md (if affected)
- README.md (if user-facing changes)

Supporting (if needed):
- docs/design/*
- docs/cheatsheet/*
- docs/host-interop/*
- examples/*

---

3. UPDATE PLAN

For each file:
- sections impacted
- what must change
- minimal wording updates

Preserve structure and tone.

---

4. GENIA_STATE.md (CRITICAL)

Ensure it:
- reflects exact behavior
- marks maturity (Experimental / Partial / Stable)
- lists limitations honestly
- does NOT overstate capabilities

---

5. RULES / SEMANTICS

Update GENIA_RULES.md only if:
- evaluation behavior changed
- pattern/matching semantics changed

Keep minimal and precise.

---

6. EXAMPLES

Ensure:
- examples run (if applicable)
- outputs match real behavior
- no reliance on unimplemented features

Update or add minimal examples if needed.

---

7. CONSISTENCY CHECK

Verify alignment across:
- GENIA_STATE.md
- GENIA_RULES.md
- GENIA_REPL_README.md
- README.md
- examples

No contradictions.

---

8. TRUTH CHECK

Docs must:
- reflect real behavior
- clearly state limitations
- avoid exaggeration

---

9. COMPLEXITY CHECK

Mark one:

[ ] Minimal and clear  
[ ] Slightly expanded but justified  
[ ] Too verbose  

Explain only if not minimal.

---

OUTPUT:

1. Summary of doc changes  
2. Files updated  
3. Key wording changes  
4. Risks or ambiguities  

No redesign. No speculation. Only truth.