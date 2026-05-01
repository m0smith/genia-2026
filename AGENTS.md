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
- Cross-doc semantic guardrails live in `docs/contract/semantic_facts.json` and `tests/test_semantic_doc_sync.py`
“Contract” defines behavior only.
It MUST NOT include tests.

Shared spec YAML files and pytest tests belong to the TEST phase.
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
- `tests/test_semantic_doc_sync.py`

Tool-specific instruction files (for example GitHub Copilot or editor/task-specific agent files) must remain consistent with:
- `GENIA_STATE.md`
- `GENIA_RULES.md`
- this file
- `docs/ai/LLM_CONTRACT.md`
- relevant shared docs

They must not redefine language semantics or source-of-truth precedence.
Prefer references over duplicated semantic rules.

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

--------------------------------
INTENT
--------------------------------

The goal is not to prevent growth.

The goal is to ensure that every addition:
- sharpens the language
- reinforces existing mental models
- makes Genia simpler, not broader

---

## Cheatsheet Sync Rule (CRITICAL)

`docs/cheatsheet/*` must remain a truthful quick-reference surface for implemented behavior only.

When language/runtime/API-facing behavior or user-facing examples change, agents must also update relevant cheatsheet pages.

At minimum, review and update as needed:

* `docs/cheatsheet/core.md`
* `docs/cheatsheet/unix-power-mode.md`

Cheatsheets must not include:

* unimplemented helpers/operators
* speculative or planned features presented as available
* call shapes that do not match the current runtime

If cheatsheet content conflicts with source-of-truth docs, `GENIA_STATE.md` remains final authority and cheatsheets must be corrected.

### Cheatsheet Example Validation Rule

Every runnable example added or changed in a cheatsheet **must** include a `[case: <id>]` marker and a matching entry in the sidecar JSON file under `tests/data/`:

| Cheatsheet | Sidecar JSON | Test module |
|---|---|---|
| `docs/cheatsheet/piepline-flow-vs-value.md` | `tests/data/pipeline_flow_vs_value_cases.json` | `tests/test_cheatsheet_pipeline_flow_vs_value.py` |
| `docs/cheatsheet/core.md` | `tests/data/cheatsheet_core_cases.json` | `tests/test_cheatsheet_core.py` |
| `docs/cheatsheet/quick-reference.md` | `tests/data/cheatsheet_quick_reference_cases.json` | `tests/test_cheatsheet_quick_reference.py` |
| `docs/cheatsheet/unix-power-mode.md` | `tests/data/cheatsheet_unix_power_mode_cases.json` | `tests/test_cheatsheet_unix_power_mode.py` |
| `docs/cheatsheet/unix-to-genia.md` | `tests/data/cheatsheet_unix_to_genia_cases.json` | `tests/test_cheatsheet_unix_to_genia.py` |

Marker placement: add `<!-- [case: <id>] -->` on the line immediately before the opening ` ``` ` fence of the runnable snippet.

JSON case entry shape:
```json
{
  "id": "<id>",
  "source": "<genia source>",
  "expected_result": "<display string>",
  "expected_stdout": "<optional stdout string>",
  "stdin_data": ["optional", "lines"]
}
```

Agents must run `pytest tests/test_cheatsheet_*.py` after editing any cheatsheet to catch drift.

---

## SICP Validation Rule (CRITICAL)

`docs/sicp/*` is an executable learning surface when present.

Runnable Genia blocks in SICP chapters must follow the fence/expected-output contract in `docs/sicp/AGENTS.MD` and remain truthful to current implementation.

When editing SICP chapters, agents must:

* keep `docs/sicp/index.md` aligned with the published chapter set
* run `pytest tests/test_sicp_code_blocks.py`

---

## `@doc` Style Validation Rule

When editing any of these files:

* `docs/style/doc-style.md`
* `docs/cheatsheet/core.md` (the `@doc Quick Reference` section)
* `docs/cheatsheet/quick-reference.md` (the `@doc Quick Reference` section)
* `docs/book/03-functions.md` (the `Documenting Functions` or `@doc Style Guide` sections)

agents must run:

```
pytest tests/test_doc_style_sync.py
```

This validates that:

* the style guide retains its required sections and examples
* cheatsheet `@doc` sections stay consistent with the style guide
* book `@doc` content matches the style guide's allowed headers and Markdown subset
* the linter's constants match the style guide
* prelude `@doc` strings (when present) pass the linter

---

## Core Philosophy

### 1. Preserve Simplicity

Genia must remain:

* Minimal
* Expressive
* Human-readable
* Easy to implement

Avoid:

* Extra syntax
* Cleverness over clarity
* Hidden behavior

---

### 2. Pattern Matching Is the Core

Genia is a **pattern-matching-first language**.

Agents must not continue into the next phase unless explicitly prompted.

Commit prefixes must match the phase:

- `preflight(scope): ... issue #123`
- `contract(scope): ... issue #123`
- `design(scope): ... issue #123`
- `test(scope): ... issue #123`
- `feat(scope): ... issue #123`
- `fix(scope): ... issue #123`
- `docs(scope): ... issue #123`
- `audit(scope): ... issue #123`
- `distillation(scope): ... issue #123`

The `test` phase must commit failing tests before implementation.
The `implementation` phase must reference the failing-test commit SHA.

## Drift-Prevention Rules

- Keep docs, tests, and implementation aligned
- Update documentation when behavior or examples change
- Update tests when behavior, wording, or protected semantic facts change
- Host-only behavior must keep `LANGUAGE CONTRACT:` and `PYTHON REFERENCE HOST:` labels where applicable
- Do not leave deleted-doc references in tests, tooling, or instruction files
- No process artifact may live in docs/ after merge.

## Required Workflow for Any Change

1. update `GENIA_STATE.md`
2. update any other affected core docs
3. update implementation only for already-defined behavior
4. update or add tests
5. run the relevant audit/validation

---

# 🚫 HARD CONSTRAINTS

Agents MUST NOT:

- invent behavior not defined in contract
- update docs to describe unimplemented features
- change semantics without updating STATE
- mix design and implementation in a single step
- perform repo-wide renames in a single pass
- redefine language behavior inside host adapters

---

# 🔁 RENAME SAFETY RULE

Renames MUST be performed in phases:

1. introduce alias
2. migrate usage incrementally
3. update tests
4. remove old name later

Never:
- rename everything at once

---

# 🌍 MULTI-HOST RULES

Future hosts (Node, Java, Rust, Go, C++):

- MUST follow the shared contract
- MUST NOT redefine behavior
- MUST pass spec tests
- MUST treat Core IR as the portability boundary

Python is the reference host.

---

# 🧠 PROMPT DISCIPLINE

Each prompt must perform ONE type of work:

- Contract
- Design
- Implementation
- Test
- Docs
- Audit
- Distillation

Never combine responsibilities.

---

# 🧾 DOCUMENTATION TRUTH RULE

Docs must:

- describe ONLY implemented behavior
- clearly label partial features
- avoid implying future capabilities
- match testable behavior

---

# 🧪 TESTING RULE

Tests must:

- validate real behavior
- cover edge cases
- fail on regression

No vague assertions.

---

# 🧩 PHILOSOPHY

Genia prioritizes:

- minimalism
- pattern-first design
- explicit behavior
- portability via Core IR
- truth over convenience

---

# 🔒 FINAL RULE

If something is unclear, incomplete, or conflicting:

STOP and resolve truth before proceeding.

Never guess.

---

# ✅ SUMMARY

This repository is:

- the source of truth
- the implementation
- the contract

It is NOT:

- a tutorial
- a learning-content repository
- a teaching resource

---

# 🚀 END
