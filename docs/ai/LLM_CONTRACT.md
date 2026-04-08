# LLM_CONTRACT.md

## Purpose

This file defines the shared contract that all coding assistants must follow in the Genia repository, including Codex, GitHub Copilot, ChatGPT, and other repository-aware agents.

It exists to prevent instruction drift across tool-specific files.

## Canonical hierarchy

Agents must interpret repository instructions in this order:

1. Active system / developer / user instructions
2. `GENIA_STATE.md`
3. `GENIA_RULES.md`
4. `AGENTS.md`
5. This file
6. Tool-specific instruction files such as:
   - `.github/copilot-instructions.md`
   - `.github/instructions/*`
   - other assistant-specific config files

If any repository instruction conflicts with implemented behavior, `GENIA_STATE.md` wins.

If any lower-level instruction conflicts with a higher-level one, the higher-level instruction wins.

## Shared model of Genia

Genia is a minimal, expressive, pattern-matching-first language.

Agents must preserve these principles:

- keep the language small and human-readable
- prefer pattern matching over introducing alternate conditional models
- avoid unnecessary syntax
- favor immutable, functional design
- keep host-specific behavior small and portable
- preserve shared semantics across hosts

## Truthfulness rules

Agents must not document or imply that a feature exists unless it is implemented and verified.

Agents must:

- describe only implemented behavior as implemented
- mark partial behavior as partial
- mark planned behavior as not implemented
- keep examples aligned with real parser/runtime behavior

## Synchronization rules

Any change affecting language behavior, syntax, runtime semantics, parser behavior, examples, portability contracts, or public API expectations must update all relevant docs in the same change.

At minimum, agents must update:

- `GENIA_STATE.md`
- `GENIA_RULES.md` when semantics change
- relevant `docs/book/*` chapters
- relevant host portability docs
- relevant specs and manifests
- relevant tests

## Prompt requirements for coding agents

Before making changes, agents must read:

- `GENIA_STATE.md`
- `GENIA_RULES.md`
- `AGENTS.md`

For host/portability work, agents must also read the shared host portability docs and spec files referenced by `AGENTS.md`.

Prompts should explicitly require documentation updates and tests.

When generating Codex prompts, include instructions to keep:
- `GENIA_STATE.md`
- `GENIA_RULES.md`
- `AGENTS.md`
- relevant `docs/book/*`
- relevant host/spec docs

up to date.

## What tool-specific files may do

Tool-specific instruction files may:

- adapt wording to the tool
- explain where to look first
- define editor or PR workflow details
- add task-specific reminders

Tool-specific instruction files must not:

- redefine Genia semantics
- redefine source-of-truth precedence
- override implemented behavior
- create new workflow obligations that conflict with `AGENTS.md`

## Drift policy

If a tool-specific instruction file contains a duplicated rule that has diverged from:
- `GENIA_STATE.md`
- `GENIA_RULES.md`
- `AGENTS.md`

the duplicated rule must be removed or replaced with a reference.

Prefer references over duplicated semantic content.

## Preferred reference wording

Use wording like:

“Follow `GENIA_STATE.md`, `GENIA_RULES.md`, `AGENTS.md`, and `docs/ai/LLM_CONTRACT.md`. Do not redefine semantics here.”

## Enforcement expectation

Repository automation should fail when tool-specific instruction files:

- omit required references
- claim conflicting authority
- duplicate protected semantic sections
- omit required synchronization reminders