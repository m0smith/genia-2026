# GitHub Copilot Instructions

Before making changes, read:

- `GENIA_STATE.md`
- `GENIA_RULES.md`
- `AGENTS.md`
- `docs/ai/LLM_CONTRACT.md`

## Precedence

Follow repository instructions according to the hierarchy defined in `docs/ai/LLM_CONTRACT.md`.

If there is any conflict about implemented behavior, `GENIA_STATE.md` is the final authority.

## Copilot-specific guidance

- Keep changes minimal and focused
- Prefer existing patterns over invention
- Update documentation and tests with code changes
- Do not redefine language semantics in this file
- Refer back to the canonical docs instead of duplicating semantic rules