# === GENIA DOC DISTILLATION PROMPT (LEAN) ===

Follow docs/process/llm-system-prompt.md.

Bias toward DELETE unless content is clearly canonical.

Target:
<files or folder>

GENIA_STATE.md is final authority.

Goal:
Reduce documentation to minimal, truthful, canonical form.

---

1. CLASSIFY FILES

For each file:
- KEEP (authoritative)
- EXTRACT (contains useful content)
- DELETE (redundant, outdated, or process artifact)

---

2. EXTRACT

Keep ONLY:
- invariants
- data models
- contracts
- patterns

Discard:
- phase/process language
- historical comparisons
- speculative content
- duplicated explanations

---

3. MAP CONTENT

Map extracted content to:
- GENIA_STATE.md
- GENIA_RULES.md
- docs/design/*
- README.md

---

4. OUTPUT

Provide:

1. File classification list
2. Extracted content (clean, minimal)
3. Destination for each extracted piece
4. Files safe to delete

---

Rules:
- Do not invent behavior
- Do not preserve process artifacts
- Prefer minimal wording
- If content conflicts → GENIA_STATE.md wins