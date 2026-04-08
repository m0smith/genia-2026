Apply when working with tests.

Canonical references:
- `GENIA_STATE.md`
- `GENIA_RULES.md`
- `AGENTS.md`
- `docs/ai/LLM_CONTRACT.md`

Use the precedence and semantic rules from those files.
Do not redefine language semantics here.

## Rules
- Prefer behavior-based tests
- Do not couple tests to implementation details
- Keep tests readable and explicit
- Update docs and tests together when behavior changes

## Required Patterns
- Add regression tests for bugs
- Ensure failure before fix (when applicable)
- Match expected stdout/stderr exactly

## Genia Code Blocks
- Runnable code must match expected output blocks
- Output must be explicitly defined

## Naming
- Test names must describe behavior, not mechanics
