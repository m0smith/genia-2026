Apply when working on stdlib.

Canonical references:
- `GENIA_STATE.md`
- `GENIA_RULES.md`
- `AGENTS.md`
- `docs/ai/LLM_CONTRACT.md`

Use the precedence and semantic rules from those files.
Do not redefine language semantics here.

## Design Principles
- Functions must be composable
- Prefer small orthogonal primitives
- Avoid overlapping functionality

## Naming
- Keep naming consistent
- Prefer clarity over brevity

## Behavior
- Clearly define edge cases
- Handle absence (none-like values) consistently

## Constraints
- Do not introduce helpers that obscure behavior
- Keep functions predictable
- Update docs and tests with behavior/code changes

## Documentation
- Use `@doc` metadata for public functions (see `docs/style/doc-style.md`)
- Every function must document:
  - purpose
  - inputs
  - outputs
  - edge cases
