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
- stay consistent with the source-of-truth precedence and workflow rules in `AGENTS.md`

## Semantic Scope

Canonical semantic rules live in:

- `GENIA_STATE.md`
- `GENIA_RULES.md`
- relevant implementation-aligned docs
- relevant specs and runtime docs when present

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
- examples must stay truthful, runnable where appropriate, and synchronized with actual implementation

## Prompting Rule

When creating Codex or Copilot task prompts for repository work, include instructions to:

- read the authoritative docs first
- keep `GENIA_STATE.md` and relevant core docs up to date
- keep tests synchronized with behavior changes

## Product Priority / Killer Workflow

Before proposing major new work, read:
- `docs/strategy/killer-workflow.md`
- `docs/strategy/release-roadmap.md`

Before creating new issues or tickets, also read:
- `docs/process/08-roadmap-ticketing.md`

Agents must:

- read the killer workflow strategy and release roadmap before proposing or implementing major new work
- explicitly classify each change's relationship to the killer workflow
- classify each proposed ticket as: current release, next release, infrastructure, follow-up, or parking lot
- prefer changes that strengthen Outcome-aware validated data pipelines
- route unrelated ideas to parking lot unless explicitly approved
- avoid treating `docs/strategy/killer-workflow.md` or `docs/strategy/release-roadmap.md` as implemented behavior — they are strategy and planning guides, not language contracts

The strategy and roadmap docs do not define implemented behavior. `GENIA_STATE.md` remains final authority.

## Active Release: R4 — Lifecycle Generalization

**Current active release is R4.**

R3 (Native Test Expansion Wave 1) is complete. R4 (Lifecycle Generalization) is now the active release focus.

When an LLM agent is asked for new Genia work and no release is specified:

1. Classify the work against R4 first.
2. If the work is R4 lifecycle work — lifecycle plan shape, phase shape, scope model, cleanup rules, failure rules, annotation binding model, deterministic source-order / reverse-source-order execution rules, or portable lifecycle docs — proceed through the normal phase pipeline.
3. If the work is not R4, mark it as non-R4 and either defer/parking-lot it or proceed only if the user explicitly asked for it.

R4 is not a bucket for actors, servers, notebooks, UI, or plugins. Those may use lifecycle later, but they are not R4 implementation targets by default.

R4 exclusions (do not include unless explicitly requested):
- server mode implementation
- actor lifecycle implementation
- arbitrary plugin system
- YAML lifecycle runner
- broad runtime rewrites
- lifecycle behavior not exercised by tests
- unrelated data-pipeline hardening (belongs to R6)

## Validation

Repository tooling may validate tool-specific instruction files against this contract.
Repository tooling may also validate a small machine-readable semantic-facts surface against the authoritative docs.

Protected semantic facts currently live in:

- `docs/contract/semantic_facts.json`
- `tests/doc/test_semantic_doc_sync.py`

That validation should enforce:

- required canonical references
- no conflicting authority claims
- no semantic redefinition in tool-local files
- reminders to update docs and tests
