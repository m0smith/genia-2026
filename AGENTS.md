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
* No process artifact may live in docs/ after merge.

---

# ⚙️ CORE ARCHITECTURE RULE

Genia is divided into four zones:

1. **Language Contract**
2. **Core IR (portability boundary)**
3. **Host Adapters**
4. **Docs / Tests / Examples**

Rule:
> A change should affect only ONE zone whenever possible.

If a change crosses zones:
→ split it into multiple steps

---

# 🧪 SPEC-FIRST DEVELOPMENT

All behavior must be grounded in:

- parse expectations
- IR expectations
- eval behavior
- CLI behavior
- flow behavior
- normalized errors

Specification lives in:
- `spec/*`

Rule:
> Spec defines behavior, not implementation.

---

# 🧠 REQUIRED WORKFLOW (MANDATORY)

for every change, use pre-flight → contract → design → failing tests → implementation → docs sync → audit

Every change MUST follow this pipeline:
## Required LLM Change Discipline

Every issue must be completed as separate phases:

1. `preflight`
2. `contract`
3. `design`
4. `test`
5. `implementation`
6. `docs`
7. `audit`
8. `distillation`

Each phase must be a separate prompt and a separate commit.

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
