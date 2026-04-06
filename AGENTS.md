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

📌 If these disagree, **GENIA_STATE.md is the final authority**

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

If a feature doesn’t fit → update closest chapter or create a new one.

---

## Required Workflow for Any Change

### Step 1: Read First

Agents MUST read:

* `GENIA_STATE.md`
* `GENIA_RULES.md`
* Relevant chapter(s) in `docs/book/`

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

---

### Step 5: Validate Truthfulness

Before finishing, verify:

* Docs match actual parser/runtime behavior
* No feature is documented unless implemented
* Partial features are labeled as partial

---

## Documentation Rules (VERY IMPORTANT)

### 1. No Speculation

Docs must NOT describe:

* Planned features as implemented
* Idealized behavior
* Future syntax

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

---

## Codex Prompt Requirements

Every Codex prompt must include:

* Instruction to read:

  * `GENIA_STATE.md`
  * `GENIA_RULES.md`
* Instruction to update documentation
* Clear constraints

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
