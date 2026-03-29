Here’s a clean, production-ready **`AGENTS.md`** tailored for your Genia project, Codex usage, and your workflow as an architect-level developer.

---

# AGENTS.md

## Purpose

This document defines how AI agents (e.g., Codex, ChatGPT, or other automated contributors) should operate within the Genia codebase.

The goal is to ensure:

* Consistency with Genia’s design philosophy
* Alignment with current implementation state
* High-quality, maintainable contributions
* Continuous documentation accuracy

---

## Source of Truth

Agents **must treat the following files as authoritative**:

* `GENIA_STATE.md` → Current implementation state
* `GENIA_RULES.md` → Language semantics and rules
* `GENIA_REPL_README.md` → Execution and REPL behavior
* `README.md` → Project overview

📌 These files **must be consulted before making any changes** 

---

## Core Principles

### 1. Preserve Simplicity

Genia is designed to be:

* Minimal
* Expressive
* Human-readable
* Easy to implement across runtimes

Avoid:

* Unnecessary syntax
* Over-engineering
* Hidden complexity

---

### 2. Pattern Matching First

Genia is fundamentally a **pattern-matching language**.

Agents should:

* Prefer pattern matching over conditionals
* Expand pattern matching expressiveness where appropriate
* Avoid introducing traditional `if` constructs

---

### 3. “decide” Is the Only Conditional

All conditional logic must use:

```
decide
```

Never introduce:

* `if`
* `switch`
* ternary operators

---

### 4. Immutability by Default

* Variables are immutable unless explicitly designed otherwise
* Avoid side effects unless clearly intentional

---

### 5. Functional Core

Favor:

* Pure functions
* Recursion (with TCO in mind)
* Composition

Avoid:

* Imperative loops (except `repeat`, when defined)
* Mutable shared state

---

## Current Architecture Awareness

Agents must align with the **actual implementation state**, not an idealized design.

Before coding:

1. Read `GENIA_STATE.md`
2. Confirm what is already implemented
3. Extend — do not reinvent

---

## Required Workflow for Changes

### Step 1: Understand Context

* Read relevant `.md` files
* Identify gaps vs. current implementation

### Step 2: Design First

* Propose minimal, idiomatic solution
* Ensure consistency with Genia philosophy

### Step 3: Implement

* Keep changes small and focused
* Avoid breaking existing behavior

### Step 4: Update Documentation (MANDATORY)

Every meaningful change must update:

* `GENIA_STATE.md` → reflect new capabilities
* `GENIA_RULES.md` → if semantics changed
* `README.md` → if user-facing behavior changed

---

## Code Style Guidelines

### Function Definitions

Prefer concise, pattern-based definitions:

```
fact(0) -> 1 |
fact(n) -> n * fact(n - 1)
```

---

### Pattern Matching

Favor expressive destructuring:

```
head([x, .._]) -> x
```

---

### Naming

* Use clear, semantic names
* Avoid abbreviations unless idiomatic

---

## Optimization Guidelines

Agents may introduce optimizations **only if**:

* They preserve semantics
* They reduce runtime complexity or allocations
* They align with simplicity goals

Examples:

* Tail-call optimization (TCO)
* Pattern match flattening
* Basic IR transformations

---

## When Adding Features

Agents must:

1. Justify the feature:

   * What problem does it solve?
   * Why is it necessary?

2. Ensure:

   * It fits the language philosophy
   * It does not introduce unnecessary syntax

3. Provide:

   * Examples
   * Updated documentation

---

## When Refactoring

Allowed when:

* Improves clarity
* Reduces duplication
* Enables future features

Must:

* Preserve behavior
* Update docs if structure changes

---

## Codex Prompting Rules

When generating prompts for Codex:

* Always include:

  * Reference to `GENIA_STATE.md`
  * Instruction to update documentation
* Be explicit about:

  * Scope
  * Constraints
  * Expected output

---

### Example Codex Prompt Pattern

```
Read GENIA_STATE.md and GENIA_RULES.md before making changes.

Task:
[clear description]

Constraints:
- Do not introduce new syntax unless necessary
- Preserve pattern matching semantics
- Keep implementation minimal

After completion:
- Update GENIA_STATE.md to reflect changes
- Update GENIA_RULES.md if semantics changed
```

---

## Anti-Patterns (Do NOT Do)

* Introduce `if` statements
* Add unnecessary keywords
* Overcomplicate pattern matching
* Ignore documentation updates
* Reimplement existing functionality
* Drift from functional paradigm

---

## Testing Expectations

Agents should:

* Add or update examples
* Validate edge cases
* Ensure pattern matching correctness

---

## Long-Term Vision Alignment

Genia aims to be:

* A small, portable core language
* Easily implementable in multiple host languages
* Friendly to both humans and AI

Every contribution should move toward that goal.

---

## Final Rule

If unsure:

👉 Choose the **simplest solution that fits the philosophy**.


