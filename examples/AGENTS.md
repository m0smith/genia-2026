# Examples — Agent & Contributor Guide

## Purpose

Every file in `examples/` is a **public teaching artifact**.

A reader should be able to open any `.genia` file here and learn:

1. what the program does and how to run it
2. which Genia features it exercises
3. idiomatic Genia style

If an example is not instructional, it does not belong here.

---

## Source of Truth

Examples must reflect **actually implemented behavior**.

- `GENIA_STATE.md` is the final authority
- `GENIA_RULES.md` defines language invariants
- `AGENTS.md` (repo root) defines the broader agent contract

Examples must not demonstrate speculative or unimplemented features.

---

## Required Structure for Every `.genia` File

### 1. File Header Comment

Every example must begin with a block comment explaining:

- **what** the program does (one sentence)
- **how to run** it (exact CLI invocation)
- **features demonstrated** (bulleted list of Genia concepts)

Use the triple-quoted string style for the header:

```genia
# Example header pattern
"""
# Title

Short description of what this program does.

## Run

\`\`\`bash
genia examples/this_file.genia [args]
\`\`\`

## Features Demonstrated

* pattern matching with guards
* tail-recursive accumulator
* map and filter
* option/absence handling with `some`/`none`
"""
```

### 2. Function Docstrings

Public-facing or conceptually important functions should carry a docstring (`"""..."""` after `=`).

Keep docstrings short:

- purpose (one line)
- parameters and return when non-obvious
- omit docstrings on trivial one-liners whose name already says everything

### 3. Inline Comments

Use inline `#` comments to mark **teaching moments**:

- why a particular pattern was chosen
- where a notable Genia idiom appears
- edge cases or traps worth calling out

Avoid mechanical narration ("this line adds x to y").

---

## Style Guide for Examples

### Pattern Matching

- prefer pattern matching over any imperative alternative
- demonstrate guards (`?`) when the logic benefits from them
- show wildcard (`_`) and rest (`..name`) patterns where natural

### Naming

- clear, descriptive names — no single-letter names outside tiny lambdas
- helper functions named for what they return, not what they internally do

### Composition

- prefer small composable functions over monolithic blocks
- pipeline (`|>`) chains for data transformation
- recursion with accumulators for iteration

### Absence / Option

- use `some`/`none` where lookup or parse may fail
- demonstrate `map_some`, `flat_map_some`, `unwrap_or` in examples that handle missing data

### State

- use `ref`/`ref_get`/`ref_set`/`ref_update` for mutable state
- keep mutation localized and explicit

### Imports

- bind module exports to short local names for clarity

---

## Categories

Examples should cover a range of Genia surface area:

| Category | Examples |
|---|---|
| Core language | `sum-5th.genia` (pipelines, stdin) |
| Simulation / game | `ants.genia`, `ants_terminal.genia`, `tic-tac-toe.genia` |
| Web / REST | `http_service.genia`, `rest_*.genia` |
| Puzzle / data | `zip_json_puzzle.genia` |

When adding a new example, pick the category it belongs to and ensure it teaches something not already covered.

---

## Companion Docs

If an example needs more than a header comment to explain, add a companion `.md` file (e.g., `rest_services.md`, `zip_json_puzzle.md`).

Companion docs should include:

- brief architecture or design notes
- sample session / curl commands for services
- test instructions if applicable

---

## Validation

- every example must be parseable by the current interpreter
- examples with a `main` entry point should be runnable without error
- the test suite under `tests/` may include tests that exercise examples; keep examples and tests synchronized
- run `uv run pytest tests/test_examples.py` to verify

---

## Anti-Patterns

- **undocumented examples** — every file needs a header and at least key docstrings
- **dead code** — remove unused functions; examples should be clean
- **host-specific tricks** — prefer portable Genia idioms
- **speculative features** — never demonstrate syntax that does not work today
- **copy-paste boilerplate** — if multiple examples share the same pattern, that is fine for teaching, but each must still be self-contained and documented independently
