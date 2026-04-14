# LLM Contract

This document is the shared cross-tool LLM contract for Genia.

Its job is to keep Codex, GitHub Copilot, and other tool-specific instruction files aligned without creating a second semantic spec.

## Precedence

Instruction precedence for repository work is:

1. active system / developer / user instructions for the current tool/session
2. `GENIA_STATE.md`
3. `GENIA_RULES.md`
4. `AGENTS.md`
5. `docs/ai/LLM_CONTRACT.md`
6. tool-specific instruction files

If these disagree about implemented behavior, `GENIA_STATE.md` is the final authority.

## What This Contract Does

- defines the shared cross-tool alignment rules
- points tool-specific instruction files back to canonical docs
- prevents tool-specific files from drifting into their own semantic constitution

This contract does not redefine Genia language semantics.

## Cross-Tool Rules

All LLM-facing tool instruction files must:

- reference:
  - `GENIA_STATE.md`
  - `GENIA_RULES.md`
  - `AGENTS.md`
  - `docs/ai/LLM_CONTRACT.md`
- treat `GENIA_STATE.md` as the final authority for implemented behavior
- avoid redefining language semantics, runtime behavior, or source-of-truth precedence locally
- prefer references over duplicated semantic rules
- remind agents to update docs and tests with behavior/code changes
- stay consistent with the book-driven-development rules in `AGENTS.md`

## Semantic Scope

Canonical semantic rules live in:

- `GENIA_STATE.md`
- `GENIA_RULES.md`
- relevant `docs/book/*` chapters
- relevant `docs/sicp/*` chapters when present

Tool-specific files may add workflow guidance, editor-specific reminders, or task-shaping advice, but they must not redefine protected topics such as:

- Option / absence semantics
- pipeline semantics
- pattern matching semantics
- Core IR or portability boundaries
- host/runtime behavior

When a protected semantic fact already has short canonical wording in the authoritative docs, prefer referencing that wording instead of restating it in tool-local instructions.

## Documentation And Example Discipline

Tool-specific instruction files must reinforce the repository rule that:

- any change to language behavior, syntax, runtime semantics, parser rules, or examples must update the authoritative docs
- book and SICP examples must stay truthful, runnable where appropriate, and synchronized with actual implementation

## Prompting Rule

When creating Codex or Copilot task prompts for repository work, include instructions to:

- read the authoritative docs first
- keep `GENIA_STATE.md` and relevant docs/book chapters up to date
- keep tests synchronized with behavior changes

## Validation

Repository tooling may validate tool-specific instruction files against this contract.
Repository tooling may also validate a small machine-readable semantic-facts surface against the authoritative docs.

Protected semantic facts currently live in:

- `docs/contract/semantic_facts.json`
- `tests/test_semantic_doc_sync.py`

That validation should enforce:

- required canonical references
- no conflicting authority claims
- no semantic redefinition in tool-local files
- reminders to update docs and tests
