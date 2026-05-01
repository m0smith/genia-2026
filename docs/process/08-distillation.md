# === GENIA DISTILLATION PROMPT (LEAN) ===

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
- .genia/process/tmp/handoffs/<change-slug>/03-failing-tests.md
- .genia/process/tmp/handoffs/<change-slug>/04-implementation.md
- .genia/process/tmp/handoffs/<change-slug>/06-doc-sync.md
- .genia/process/tmp/handoffs/<change-slug>/07-audit.md

If required handoffs are missing → STOP and report.

Write output to:
.genia/process/tmp/handoffs/<change-slug>/08-distillation.md

This file must be created.

---

0. BRANCH CHECK

- Must NOT be on main
- Must match pre-flight branch
- If mismatch → STOP

---

Distill <CHANGE NAME>.

Goal:
Extract durable, canonical documentation from handoffs and eliminate process artifacts.

Rules:
- Do not invent behavior
- Do not preserve phase/process text
- Prefer minimal wording
- GENIA_STATE.md is final authority
- If sources conflict → align to GENIA_STATE.md or flag

---

1. EXTRACT

From handoffs, keep ONLY:
- invariants
- data models
- contracts
- user-visible behavior
- error behavior
- tested limitations
- stable patterns

Discard:
- phase logs
- planning text
- repeated explanations
- speculative content
- tool-specific notes

---

2. MAP TO CANONICAL DOCS

Map extracted content to:

- GENIA_STATE.md (authoritative behavior + maturity)
- GENIA_RULES.md (semantics, if changed)
- README.md (user-facing, if needed)
- GENIA_REPL_README.md (if CLI/REPL affected)
- docs/design/* (structural concepts)

Do NOT create new doc categories.

---

3. APPLY CHANGES (MINIMAL)

For each target file:
- update only impacted sections
- preserve structure and tone
- avoid duplication

---

4. CONSISTENCY CHECK

Ensure alignment across:
- GENIA_STATE.md
- GENIA_RULES.md
- README.md
- GENIA_REPL_README.md
- examples

No contradictions.

---

5. CLEANUP

Determine:
- which handoff files are now redundant

After extraction:
- mark entire handoff directory as safe to delete

Do NOT migrate handoff files into docs.

---

6. COMPLEXITY CHECK

[ ] Minimal and clear  
[ ] Slightly expanded but justified  
[ ] Too verbose  

Explain only if not minimal.

---

OUTPUT:

1. Extracted durable content
2. Destination for each item
3. Files updated
4. Handoff directory safe to delete
5. Any discarded content worth noting

No redesign. No speculation. No process artifacts.