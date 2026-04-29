You are performing Doc Distillation for Genia.

Target:
<files or folder>

Before doing anything, read:
- AGENTS.md
- GENIA_STATE.md (final authority)
- GENIA_RULES.md
- README.md

Goal:
Ensure only minimal, truthful, canonical documentation remains.

Steps:

1. Classify each file:
   - KEEP (authoritative)
   - EXTRACT (contains useful content)
   - DELETE (redundant, outdated, or process artifact)

2. Extract ONLY:
   - invariants
   - data models
   - contracts
   - patterns

3. Discard:
   - phase language
   - historical comparisons
   - speculative content
   - duplicated explanations

4. Map extracted content to:
   - GENIA_STATE.md
   - GENIA_RULES.md
   - docs/design/*
   - README.md

5. Produce:
   - extracted content (cleaned)
   - destination for each piece
   - files to delete

Rules:
- GENIA_STATE.md is the final authority
- Do not invent behavior
- Do not preserve process artifacts
- Prefer minimalism