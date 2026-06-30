# GENIA AGENTS GUIDE

This document defines how AI agents (Copilot, Codex, ChatGPT) must operate within the Genia repository.

It establishes:
- sources of truth
- architectural boundaries
- required workflow discipline
- rules for safe evolution

---

# 🧭 REPOSITORY ROLE

This repository (`genia-2026`) is the **authoritative implementation and semantics repository** for Genia.

It owns:
- language behavior
- runtime behavior
- CLI behavior
- flow semantics
- concurrency semantics
- Core IR (portability boundary)
- host adapters
- specification and conformance tests

This repository does NOT contain tutorial content, learning content, or external examples.

---

# 📚 SOURCE OF TRUTH (ORDERED)

When sources conflict, resolve in this order:

1. `GENIA_STATE.md` (**FINAL AUTHORITY**)
2. `GENIA_RULES.md`
3. `GENIA_REPL_README.md`
4. `README.md`
5. `spec/*` (behavioral truth via tests)
6. `docs/host-interop/*`
7. `docs/architecture/*`
8. implementation (`src/*`, `hosts/*`)
9. `docs/process/run-change.md`

Rules:
- Tests must reflect actual behavior
- Implementation must match STATE + RULES
- Docs must describe ONLY what is implemented
- Cross-doc semantic guardrails live in `docs/contract/semantic_facts.json` and `tests/doc/test_semantic_doc_sync.py`
- “Contract” defines behavior only. It MUST NOT include tests.
- Shared spec YAML files and pytest tests belong to the TEST phase.

---

# 🚫 NON-AUTHORITATIVE SOURCES

The following MUST NOT define behavior:

- external repositories
- design notes not reflected in STATE
- comments in code not reflected in STATE

Rule:
> If it is not in `GENIA_STATE.md`, it is not part of the language.

`GENIA_STATE.md` is the final authority for implemented behavior.

---

# 📖 DOCUMENTATION MODEL

Documentation in this repository must be:

- concise
- implementation-aligned
- test-verifiable

Allowed documentation:

- CLI behavior
- runtime behavior
- host interop
- architectural boundaries
- cheatsheets tied to real behavior

Prohibited:

- speculative features
- tutorial content
- narrative explanation beyond what is required for correctness

## Documentation Truth Model

Truth hierarchy:

1. `GENIA_STATE.md`
2. `GENIA_RULES.md`
3. `GENIA_REPL_README.md`
4. `README.md`
5. `spec/*`
6. `docs/host-interop/*`
7. `docs/architecture/*`
8. implementation (`src/*`, `hosts/*`)

* no doc may claim more than `GENIA_STATE.md`
* examples must include classification
* host-only behavior must be labeled
* contract vs Python reference host wording must be explicit when relevant
* avoid absolute claims without evidence
* test coverage must be described honestly

Banned certainty phrases in docs unless narrowly evidenced:

* `all examples`
* `complete coverage`
* `fully aligned`
* `no drift`

---

## Cross-Tool Instruction Sync

Shared cross-tool LLM guidance lives in `docs/ai/LLM_CONTRACT.md`.
Treat it as the shared cross-tool adapter contract below the main source-of-truth docs, not as a replacement for them.

Protected semantic sync guardrails live in:
- `docs/contract/semantic_facts.json`
- `tests/doc/test_semantic_doc_sync.py`

Tool-specific instruction files (for example GitHub Copilot or editor/task-specific agent files) must remain consistent with:
- `GENIA_STATE.md`
- `GENIA_RULES.md`
- this file
- `docs/ai/LLM_CONTRACT.md`
- relevant shared docs

They must not redefine language semantics or source-of-truth precedence.
Prefer references over duplicated semantic rules.

---

## Product Priority

Before proposing or implementing new feature work, read:
- `docs/strategy/killer-workflow.md`
- `docs/strategy/release-roadmap.md`

Before creating new issues/tickets, also read:
- `docs/process/08-roadmap-ticketing.md`

**Current active release: R5 — Native Test Migration / Genia-Facing Coverage Wave 1.**
R4 (Lifecycle Generalization) is complete. When asked for new Genia work with no release specified, classify work against R5 first. If it is not native-test migration or Genia-facing coverage work, mark it as non-R5 and defer, park, or classify it to R6 unless the user explicitly asked for it. See `docs/strategy/release-roadmap.md` and `docs/ai/LLM_CONTRACT.md` for full R5 scope and agent guidance.

Prefer work that strengthens Genia's first killer workflow:
**Outcome-aware validated data pipelines.**

```text
messy records in → clear pipelines → validated shaped output / reports + useful diagnostics
```

If a proposed change does not support that workflow, treat it as parking-lot/future work
unless explicitly approved.

The strategy doc is a prioritization guide, not a language contract.
`GENIA_STATE.md` remains the final authority for implemented behavior.

---

## Non-Negotiable Rule (CRITICAL)

> Any change to language behavior, syntax, runtime semantics, parser rules, or examples MUST also update:
>
> * `GENIA_STATE.md`
> * relevant chapter(s) in `docs/book/`
>
> Documentation must describe **only behavior that is implemented and verified by tests**

No exceptions.

---

--------------------------------
CORE SURFACE FREEZE
--------------------------------

Genia maintains a deliberately small and stable core surface.

New features MUST pass all of the following criteria:

1. Reinforce value templates
   - The feature strengthens or composes with:
     - refinement
     - shapes (open/closed)
     - variants
     - contracts

2. Reinforce canonical patterns
   - The feature aligns with and strengthens:
     - pattern matching
     - flow/pipeline model
     - value-first design
   - It must not introduce competing paradigms

3. Reduce ambiguity
   - The feature makes programs easier to reason about
   - It must not introduce multiple equivalent ways to express the same concept
   - It must not blur existing semantics

--------------------------------
REJECTION CRITERIA
--------------------------------

A feature MUST NOT be added if it:

- duplicates existing capability in a different form
- introduces a second way to express an existing pattern
- adds syntax without increasing clarity
- expands the surface area without strengthening the core model
