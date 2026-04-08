When working in this repository:

- Follow AGENTS.md first
- Treat GENIA_STATE.md, GENIA_RULES.md, GENIA_REPL_README.md, and README.md as authoritative

## Behavior Rules
- Never invent or assume language semantics
- Never redesign behavior without explicit instruction
- Prefer minimal diffs over large refactors
- Preserve backward compatibility unless told otherwise

## Change Requirements
For ANY change to:
- parser
- evaluator
- stdlib
- CLI
- pipeline behavior

You MUST:
- update tests
- update docs
- explain impact

## Code Style
- Keep logic readable and explicit
- Avoid unnecessary abstraction
- Match existing patterns

## Error Handling
- Include actual received types in error messages
- Avoid vague errors

## If Uncertain
- Do not guess
- Summarize ambiguity
- Offer options instead