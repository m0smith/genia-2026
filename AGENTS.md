# AGENTS.md

## Purpose

This document defines how AI agents (e.g., Codex, ChatGPT, or other automated contributors) must operate within the Genia codebase.

The goals are:

* Preserve Genia’s philosophy
* Ensure implementation and documentation never drift
* Maintain a **living, correct “Reasoned Schemer–style” learning system**
* Enforce high-quality, minimal, and consistent contributions

---

## Source of Truth

Agents **must treat the following as authoritative and synchronized**:

* `GENIA_STATE.md` → What is actually implemented (ground truth)
* `GENIA_RULES.md` → Language semantics (law)
* `GENIA_REPL_README.md` → Runtime behavior
* `README.md` → High-level overview
* `docs/book/*` → Learning system (must reflect reality)
* `docs/sicp/*` → SICP learning system when present (must reflect reality)
* `docs/host-interop/*` → Shared cross-host portability contract for multi-host work
* `spec/*` → Shared conformance scaffolding for multi-host work

📌 If these disagree, **GENIA_STATE.md is the final authority**

For multi-host / portability work, agents must also treat these as synchronized contract artifacts:

* `docs/host-interop/HOST_INTEROP.md`
* `docs/host-interop/HOST_PORTING_GUIDE.md`
* `docs/host-interop/HOST_CAPABILITY_MATRIX.md`
* `docs/architecture/core-ir-portability.md`
* `spec/README.md`
* `spec/manifest.json`
* `tools/spec_runner/README.md`
* `hosts/README.md`

---
## Cross-Tool Instruction Sync

Shared cross-tool LLM guidance lives in `docs/ai/LLM_CONTRACT.md`.
Treat it as the shared cross-tool adapter contract below the main source-of-truth docs, not as a replacement for them.

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

Agents must:

* Prefer pattern matching over all alternatives
* Improve pattern expressiveness when needed
* Avoid fallback to imperative constructs

---

### 3. Pattern Matching Is the Only Conditional Model

Allowed:

* Pattern matching in function definitions / case expressions

Forbidden:

* `if`
* `switch`
* ternary operators
* introducing conditional keywords

---

### 4. Immutability by Default

* No mutation unless explicitly designed
* Favor value transformation

---

### 5. Functional Core

Favor:

* Pure functions
* Recursion (TCO-aware)
* Composition

Avoid:

* Imperative loops (except `repeat`)
* Shared mutable state

---

### 6. Keep the Host Bridge Small

Public stdlib and library behavior should prefer implementation in Genia/prelude rather than host-language code whenever feasible.

Host code should primarily provide:

* Runtime primitives
* Capability bridges
* Unavoidable platform integration

Agents must avoid growing the public language surface around Python-specific behavior.

Minimizing host code matters because it improves:

* Multi-host portability
* Future native/direct compilation
* Smaller runtime footprint
* Easier reasoning about semantics

When adding new public helpers:

* Default to prelude wrappers, even when they are backed by host primitives
* Avoid host-only convenience helpers unless there is a compelling runtime reason

Rule of thumb for placement:

Keep a feature in Python/host code only when at least one of these is true:

* it directly touches host resources or capabilities
* it depends on threading, blocking, I/O, files, bytes, processes, or stream runtime primitives
* it is core parser/compiler/evaluator/runtime substrate
* moving it into Genia would materially harm correctness, portability, simplicity, or performance at the current phase

Otherwise, prefer implementing it in Genia/prelude.

In particular:

* raw capability access such as `argv()` may remain host-backed
* interpretation, transformation, and user-facing semantics over those raw values should prefer prelude
* agents should actively look for chances to shrink Python-side pure transformation logic
* prefer a minimal runtime kernel in the host language, with language-visible semantics layered in Genia/prelude
* Flow/rules are the model example in this phase:
  * keep lazy pull-based single-use flow mechanics in host code
  * prefer rule orchestration, defaulting, validation, and other language-visible semantics in Genia/prelude when feasible
* parser/compiler/evaluator substrate may remain host-backed
* syntax/programs-as-data helpers are the other model example in this phase:
  * keep parsing, lowering, quoting substrate, and metacircular runtime substrate in host code
  * prefer user-facing selectors, structural helpers, and semantic glue over quoted forms in Genia/prelude
* agents should actively look for chances to shrink Python-side structural inspection and pure helper glue, not only business logic
* public help/discovery is the third model example in this phase:
  * keep only the minimal host help substrate, rendering, and generic bridge fallback in host code
  * prefer public-surface discovery derived from prelude docstrings and autoload registrations over hand-curated Python API narration
* avoid duplicating public API inventories in host code when prelude/autoload metadata already provides the source of truth

### 7. Shared Semantics Across Hosts

Python is the current implemented reference host unless `GENIA_STATE.md` says otherwise.

For multi-host work:

* shared semantics come first
* Core IR is the portability boundary
* shared spec tests under `spec/` are authoritative across hosts
* host-specific code must not redefine language behavior
* capability additions or coverage changes must update `docs/host-interop/HOST_CAPABILITY_MATRIX.md`
* changes to the shared host contract must update `spec/manifest.json`
* docs/book remains a truthful teaching interface and must distinguish implemented hosts from planned/scaffolded ones
* agents must prefer portable/shared semantics over host-local convenience
* future Codex prompts for host work must instruct the agent to keep shared docs/spec/tests/book content in sync
* host-local tests and docs do not override the shared host contract once it is documented in the shared interop/spec artifacts

---

## Book-Driven Development (CRITICAL)

The `docs/book/` directory is not documentation.

It is the **primary interface for understanding Genia**.

Agents must:

* Treat chapters as executable learning artifacts
* Keep them aligned with real implementation
* Update them alongside any change

When `docs/sicp/` chapters are present, they follow the same executable-learning-artifact discipline and may be validated by automated tests.

---

## Chapter Mapping Responsibility

Agents must map features → chapters:

| Feature          | Chapter             |
| ---------------- | ------------------- |
| Data / literals  | 01-core-data        |
| Pattern matching | 02-pattern-matching |
| Functions        | 03-functions        |
| Conditionals     | 02-pattern-matching |
| Lists            | 05-lists            |
| Recursion        | 06-recursion        |
| repeat           | 07-repeat           |
| Protocols        | 08-protocols        |
| Errors/retries   | 09-errors           |
| Concurrency      | 10-concurrency      |
| Host portability | 15-reference-host-and-portability |

If a feature doesn’t fit → update closest chapter or create a new one.

---

## Required Workflow for Any Change

### Step 1: Read First

Agents MUST read:

* `GENIA_STATE.md`
* `GENIA_RULES.md`
* Relevant chapter(s) in `docs/book/`

For host / portability work, agents MUST also read:

* `docs/host-interop/HOST_INTEROP.md`
* `docs/host-interop/HOST_PORTING_GUIDE.md`
* `docs/host-interop/HOST_CAPABILITY_MATRIX.md`
* `docs/architecture/core-ir-portability.md`
* `spec/README.md`
* `spec/manifest.json`
* `tools/spec_runner/README.md`
* relevant `hosts/*/README.md` and `hosts/*/AGENTS.md`

---

### Step 2: Design

* Keep solution minimal
* Align with philosophy
* Avoid introducing syntax unless necessary

---

### Step 3: Implement

* Small, focused changes
* Preserve existing behavior

---

### Step 4: Update Documentation (MANDATORY)

Agents MUST update:

* `GENIA_STATE.md`
* Relevant chapter(s)
* Examples if behavior changed
* Relevant `docs/cheatsheet/*` pages when public language/runtime/API examples or call shapes changed

For host / portability work, agents MUST also update the relevant shared contract files when they change:

* `docs/host-interop/*`
* `spec/manifest.json`
* `tools/spec_runner/README.md`
* `hosts/*`

---

### Step 5: Validate Truthfulness

Before finishing, verify:

* Docs match actual parser/runtime behavior
* No feature is documented unless implemented
* Partial features are labeled as partial
* Cheatsheet entries match implemented behavior and current call shapes

---

## Documentation Rules (VERY IMPORTANT)

### 1. No Speculation

Docs must NOT describe:

* Planned features as implemented
* Idealized behavior
* Future syntax

## Documentation Style (`@doc`)

Public functions must follow the canonical `@doc` style guide in `docs/style/doc-style.md`.
Keep this file small; put detailed formatting rules there, not here.

Good:

```genia
@doc "Adds one to x."
inc(x) -> x + 1
```

Bad:

```genia
@doc "This function adds one to x by using the implementation below."
inc(x) -> x + 1
```

All public functions MUST follow the `@doc` style guide.

---

### 2. Every Feature Must Include

In book chapters:

* Minimal example
* Edge case example
* Failure case example

---

### 3. Implemented vs Missing

Each chapter must include:

* ✅ What is implemented
* ⚠️ What is partial
* ❌ What is not implemented

---

### 4. Examples Must Be Real

All examples must:

* Reflect actual syntax
* Be executable or testable
* Match current runtime behavior

---

## Generated Documentation Sections

Some parts of documentation must be treated as **generated truth**.

Markers:

```
<!-- GENERATED:section-name:start -->
...
<!-- GENERATED:section-name:end -->
```

Agents:

* MAY update content inside markers
* MUST NOT remove markers
* SHOULD regenerate based on code when possible

---

## Code Style Guidelines

### Functions

```
fact(0) -> 1 |
fact(n) -> n * fact(n - 1)
```

---

### Pattern Matching

```
head([x, .._]) -> x
```

---

### Naming

* Clear, semantic
* No unnecessary abbreviations

---

## Optimization Guidelines

Allowed only if:

* Semantics unchanged
* Simplicity preserved
* Measurable improvement

Examples:

* TCO
* Pattern match optimization
* Small IR improvements

---

## Feature Additions

Agents must:

1. Justify necessity
2. Prove alignment with philosophy
3. Add examples
4. Update docs

---

## Refactoring Rules

Allowed when:

* Improves clarity
* Enables features
* Reduces duplication

Must:

* Preserve behavior
* Update documentation

---

## Testing Expectations

Agents must:

* Add examples or tests
* Cover edge cases
* Validate pattern matching behavior
* Prefer `tests/cases/` for black-box language-semantic behavior that should stay reusable across hosts
* Keep host/runtime-substrate checks in host-specific pytest tests when moving them to cases would hide what is actually being validated
* Split mixed tests when appropriate:
  * reusable source/result/error behavior goes to semantic cases
  * parser internals, debug protocols, package-resource loading, thread/race-sensitive behavior, and other host-specific checks stay in pytest

---

## Codex Prompt Requirements

Every Codex prompt must include:

* Instruction to read:

  * `GENIA_STATE.md`
  * `GENIA_RULES.md`
* Instruction to update documentation
* Clear constraints

For host / portability work, prompts must also include:

* instruction to read/update `docs/host-interop/*`
* instruction to read/update `spec/manifest.json` and `tools/spec_runner/README.md`
* instruction to keep `hosts/*`, root docs, and relevant `docs/book/*` content synchronized

---

### Standard Prompt Template

```
Read GENIA_STATE.md and GENIA_RULES.md before making changes.

Task:
[description]

Constraints:
- Do not introduce unnecessary syntax
- Preserve pattern matching semantics
- Keep implementation minimal

After completion:
- Update GENIA_STATE.md
- Update relevant docs/book chapters
- Ensure examples match real behavior
```

---

## Anti-Patterns (STRICTLY FORBIDDEN)

* Introducing `if`
* Overcomplicating pattern matching
* Adding unnecessary keywords
* Ignoring documentation updates
* Reimplementing existing features
* Documenting unimplemented behavior

---

## Final Rule

If unsure:

👉 Choose the simplest solution that fits the philosophy
👉 And make sure the book teaches it correctly
