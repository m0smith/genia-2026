# GitHub Copilot Instructions

Before making changes, read:

- `GENIA_STATE.md`
- `GENIA_RULES.md`
- `AGENTS.md`
- `docs/ai/LLM_CONTRACT.md`

## Copilot-specific guidance

- Follow repository instruction precedence from `docs/ai/LLM_CONTRACT.md`.
- `GENIA_STATE.md` is the final authority for implemented behavior.
- Keep changes minimal and focused
- Prefer existing patterns over invention
- Update documentation and tests with code changes
- Keep relevant implementation-aligned docs and tests synchronized with actual behavior
- For browser/runtime-host work, keep `docs/browser/*`, `docs/host-interop/*`, `spec/manifest.json`, and `tools/spec_runner/README.md` synchronized with implemented-vs-planned status
- Do not redefine language semantics or source-of-truth precedence in this file
- Refer back to the canonical docs instead of duplicating semantic rules
- Keep protected semantic facts aligned with `docs/contract/semantic_facts.json` and `tests/test_semantic_doc_sync.py`
