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

**R9 — Value Templates & Representations is complete.**
**R10 — Configuration & Secrets is complete.** Its approved contract and E10-1
provider/ordinary acquisition, E10-2 defaults/conversion-validation, E10-3 protected-carrier/matching, E10-4 protected sinks, E10-5 explicit declassification, E10-6 cross-mode hardening, E10-7 composed validated-pipeline proving case, and E10-8 release truth audit are complete. For new Genia work with no release specified,
consult the release roadmap and classify it as a follow-up, a later release,
infrastructure, or parking-lot item; do not expand R10 implicitly. Release
planning never makes candidate syntax or behavior implemented and never skips
contract, design, failing-test, implementation, documentation, or audit phases.
**R11 — AI Composition is complete.** E11-1 through E11-8 are complete. Its Experimental
Python-host boundary provides text and R9-validated JSON `model/4` ordinary-callable
and Outcome behavior through an offline deterministic fixture plus one explicit
Google Gemini direct-REST capability, with shared conformance and cross-mode
fixture hardening, E11-5 application-owned list/Flow `scan` conversation composition, E11-6 Outcome-aware validated-pipeline proving case, E11-7 release-example truth synchronization, and E11-8 release truth audit/distillation. Follow-ups and later releases
require their own gates. Preserve the ordinary
callable/value/Outcome/R9/R10/Flow boundary recorded in
`docs/design/r11-ai-composition-contract.md`. See `docs/strategy/release-roadmap.md` and
`docs/ai/LLM_CONTRACT.md` for release boundaries.
**R12 — Retrieval & Grounding is complete.** Its approved E12-0 contract and
Experimental E12-1 through E12-8 implementation remain the release boundary. Its ordinary `chunk/2` boundary validates exact
document/span values and owns Unicode-code-point slicing, provenance, and exact
R9 represented metadata preservation without a provider capability. Its
`embed/4` boundary adds explicit chunk/query variants, exact identity-preserving
finite embeddings, R10 `quote(embed_call)` authority, and one deterministic
opaque Python fixture attempt without retry or networking. `index/4` returns an
opaque compatibility-bearing handle, `retrieve/4` consumes an explicit query
embedding and returns exact ordered indexed evidence or no-results absence, and
provider-backed `rerank/4` preserves the exact duplicate-aware evidence/provenance
multiset while changing only order and finite scores. E12-6 adds pure ordinary
grounded context/answer composition with exact ordered evidence, first-occurrence
exact-source deduplication, successful-R11-Outcome gating, and one supplied
unchanged model call; it adds no public grounding builtin or citation policy. E12-7 adds concern-specific R10/cross-mode hardening, bounded-demand and recursive non-leakage proofs, existing parse/Core IR regression coverage, and one complete validated grounded composition without new semantics. E12-8 release-example truth synchronization adds documentation verification only, and E12-9 completes the release truth audit/distillation without runtime behavior. Follow-ups and later releases require their own gates. Preserve the
ordinary value/callable/Outcome/R9/R10/R11 boundary in
`docs/design/r12-retrieval-grounding-contract.md`; do not infer a RAG or
vector-store framework, hidden query embedding, citation rendering semantics,
or later-ticket implementation authority.
**R13 — Configuration Resolution Ergonomics is complete (epic #608); E13-0 is
approved and E13-1 through E13-8 are complete.** Its approved boundary is ordinary callable
configuration/secret views over an explicit R10 provider, explicit program-CLI
adaptation, one narrow `.env` source capability, and deterministic conventional
provider composition. It must preserve R10 Outcomes, immutable snapshots,
protected carriers/sinks/declassification, lexical lookup, and map/module-only
named access. E13-1 adds inert qualified view construction and exact one-call
R10 delegation; E13-2 purely normalizes explicit string arguments into the
existing literal source descriptor without acquiring process state; E13-3 reads one exact explicit path once with deterministic parsing and no discovery, interpolation, or refresh; E13-4 composes the fixed conventional provider; E13-5 verifies cross-mode, diagnostic, protected-boundary, and ordinary-call/Core IR preservation without new semantics; E13-6 proves the Outcome-aware validated-pipeline composition without new semantics; E13-7 release-example truth synchronization adds documentation verification only; and E13-8 completes the release truth audit/distillation without runtime behavior. R13
adds no syntax, Core IR, lifecycle provider binding,
dependency injection, or ambient lookup. See
`docs/strategy/r13-configuration-resolution-ergonomics.md`.
**R14 — Composable Lifecycles is in progress (epic #619); E14-0 is approved
and E14-1/E14-2/E14-3/E14-4/E14-5 are implemented (issues #621, #692, #693,
#694, #622).** R14 is scoped to one lifecycle model with parent/child execution
scopes, deterministic peer lifecycle attachments, repeated element scopes
over eager and lazy pipelines, one explicit R10/R13 provider binding, and
outbound HTTP as the vertical proving consumer. E14-1 implements the
HTTP-free instance/scope core: `lifecycle_scope`, `lifecycle_child`,
`lifecycle_context`, the scope lifetime state machine, and the
entry/work/unwind algorithm with its partial-entry/failure matrix. E14-2
proves that same algorithm at three-or-more-peer breadth (deterministic
enter/reverse-unwind order, every partial-entry/failure-matrix row,
later-only context visibility, peer isolation, and attachment order
independent of ancestor depth) with no runtime-code change — it adds no new
public function. E14-3 adds `lifecycle_repeat(peers, source, element_work)`:
one fresh element scope per consumed List (eager, exhaustive) or Flow (lazy,
no-over-pull, single-use) element, with reserved `quote(element)`/
`quote(index)` context populated before any peer's own `enter` runs, and
early-close cleanup reduced to the existing Flow finalization rule — no new
list/Flow mechanism. E14-4 adds `lifecycle_config(provider)`: a pure
factory validating an already-constructed R10/R13 `GeniaConfigProvider` and
returning one reserved `quote(config)` peer whose `enter` captures (never
acquires) the provider; reserved-name non-shadowing is inherited entirely
from the existing peer-list mechanism, so this adds zero change to
`lifecycle_runtime.py` or `configuration.py`. The record-oriented proving
case (#695) must still show multiple peer lifecycles per element without
adding AWK syntax or replacing Flow/Seq/Outcome transformations. Preserve
the boundaries that lifecycle context is not mutable lexical state,
attachment order is not parentage, expired element context does not leak
through lazy values, annotations remain inert, import/load performs no
lifecycle or network activation, and protected HTTP sinks do not weaken
R10. E14-5 adds `http_operation(method, base_url, path, headers, query,
body)`: one inert, closed `HttpOperation` value with zero network IO,
validating all six fields in declared order (method/base_url/path/
headers/query/body) and injecting an implicit `content-type` header only
when `body` validates and none is already set. This is the first R14-HTTP
ticket and adds no host capability at all — `web.http_send`/transport
remain later tickets. No R14 behavior beyond E14-1/E14-2/E14-3/E14-4/E14-5
is implemented merely because its roadmap, issues, or contract exist.
E14-6 (#623, Python host outbound HTTP transport capability) is the next
gate. See `docs/design/r14-composable-lifecycle-contract.md`,
`docs/strategy/r14-composable-lifecycles.md`, and `GENIA_STATE.md` sections
9.8-9.12.

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

Agents must run `uv run pytest tests/test_cheatsheet_*.py` after editing any cheatsheet to catch drift.

---

## Composability Matrix Sync Rule (CRITICAL)

`docs/design/composability-matrix.md` is a very important facet of Genia: it
is the one place that explains, for value templates, refinements, shapes,
representations, and patterns, what composes with what and why — the
mechanism that keeps `secret(x)`, `json(x)`, and `json(Person(x))` legible as
one coherent model instead of unrelated special cases. It is a design aid
(`GENIA_STATE.md` remains final authority), but it must stay accurate.

`tests/doc/test_composability_matrix_sync.py` enforces this automatically: it
re-derives the full Template/representation/matcher family (every `*_match`
helper, plus `represent`, `strip_representation`, `json_decode`,
`json_encode`, and `json_schema`) directly from `src/genia/builtins.py` and
`src/genia/std/prelude/*.genia` — not from a hand-maintained list — and fails
if any member is missing from the matrix, missing from `GENIA_STATE.md`, or
if the matrix mentions a family-shaped name that no longer exists in code.

Agents must:

* run `uv run pytest tests/doc/test_composability_matrix_sync.py` after adding,
  renaming, or removing any Template/representation/matcher-family builtin
  (a `*_match` helper, a new representation/carrier primitive, or a new
  structural-source compiler like `json_schema`), and after editing the
  matrix itself
* when the test reports a missing name, update the matrix's "Current
  foundation" or the relevant release-relationships table (for example "R9
  relationships") to describe how the new/changed builtin composes with
  existing Template, representation, and pattern concepts — not just add the
  bare name
* when a later release changes a composition boundary the matrix already
  documents, review and update the matrix in the same change, per its own
  "must be reviewed whenever a later release changes one of these
  composition boundaries" instruction
* never let the matrix claim to be authoritative; it must keep its
  `PROPOSED / EXPLORATORY` status and `GENIA_STATE.md` is final authority
  disclaimer

This rule exists because the family-derivation test only catches missing or
stale *names* — it cannot verify that the matrix's prose about a builtin is
still correct. Treat a passing test as a floor, not a substitute for reading
the relevant matrix row when composability behavior changes.

---

## SICP Validation Rule (CRITICAL)

`docs/sicp/*` is an executable learning surface when present.

Runnable Genia blocks in SICP chapters must follow the fence/expected-output contract in `docs/sicp/AGENTS.MD` and remain truthful to current implementation.

When editing SICP chapters, agents must:

* keep `docs/sicp/index.md` aligned with the published chapter set
* run `uv run pytest tests/test_sicp_code_blocks.py`

---

## `@doc` Style Validation Rule

`docs/style/doc-style.md` §11–§12 is the source of truth for public function
metadata and documentation coverage. Every public prelude function must carry
both `@doc` and `@category`.

When a public prelude function is added, or its `@doc` or `@meta` changes,
agents must run `python tools/gen_function_docs.py` in the same change and
commit the resulting `docs/reference/**` pages and `mkdocs.yml` navigation.
CI enforces both `tools/gen_function_docs.py --check` and
`tools/lint_doc.py --require-coverage`.

The GitHub Wiki function reference is a generated mirror published by
`tools/publish_wiki.sh`. Never edit the generated Wiki pages by hand.

When editing any of these files:

* `docs/style/doc-style.md`
* `docs/cheatsheet/core.md` (the `@doc Quick Reference` section)
* `docs/cheatsheet/quick-reference.md` (the `@doc Quick Reference` section)
* `docs/book/03-functions.md` (the `Documenting Functions` or `@doc Style Guide` sections)

agents must run:

```
uv run pytest tests/test_doc_style_sync.py
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

Parking-lot documents are non-authoritative idea capture only. They must not be treated as implemented behavior or source-of-truth language semantics.

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

This repository is managed by `uv`. Run pytest as `uv run pytest ...`, never as
bare `pytest ...`; a bare command may select a system environment without the
locked development dependencies. Full regression uses
`uv run pytest -n auto -q`. `pytest-xdist` and PyYAML are declared project
dependencies, so treat them as unavailable only if the corresponding `uv run`
command fails.

In environments that restrict local sockets, full regression is the union of
these two required partitions:

```
uv run pytest -n auto -q -m "not loopback"
uv run pytest -n auto -q -m loopback
```

Run the `loopback` partition with local loopback socket permission. Do not treat
the sandbox-safe partition alone as full regression, and do not convert socket
permission failures into skips.

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
