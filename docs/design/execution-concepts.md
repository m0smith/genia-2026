# Execution Concepts

> **Status: PROPOSED / EXPLORATORY**
> This document is a design note only.
> It does not describe implemented behavior.
> See `GENIA_STATE.md` for actual behavior.

---

## Purpose

Keep core execution concepts distinct. Each concept owns exactly one job.
No concept may steal another concept's job.

---

## Concept Definitions

| Concept | Responsibility | Must NOT own |
|---|---|---|
| **file/source** | Where code comes from (file path, stdin, `-c` string, pipe) | scope, metadata, phase selection |
| **module** | Where code belongs; runtime namespace; export boundary | file loading strategy, test execution, phase control |
| **annotation** | Metadata attached to a top-level binding | execution logic, lifecycle control, behavioral transforms |
| **lifecycle** | Ordered phases that select and run code (e.g., begin / row / end) | source loading, module resolution, annotation semantics |
| **unit test** | Consumer of annotations + lifecycle; validates behavior | language syntax, lifecycle definition, module structure |
| **execution mode** | How a Genia run is shaped (file / command / pipe / REPL) | lifecycle phases, module loading order, annotation meaning |

---

## What Each Concept Must NOT Do

| Concept | Hard boundaries |
|---|---|
| file/source | Must not define scope or export rules |
| module | Must not dictate which files are loaded or when |
| annotation | Must not introduce macros, compile-time transforms, or execution behavior |
| lifecycle | Must not load files or resolve modules |
| unit test | Must not extend language syntax or redefine lifecycle |
| execution mode | Must not own phase logic or annotation semantics |

---

## Dangerous Merges (bolt these early)

| Merge | Why it's dangerous |
|---|---|
| execution mode + lifecycle | mode selects a lifecycle; it must not become the lifecycle |
| module + file | a module may live in a file; a file is not a module |
| annotation + behavior | annotations are metadata only; behavior belongs elsewhere |
| unit test + language syntax | tests consume the language; they must not extend it |
| package + module | a package groups modules; it is not a module |
| autoload + import | autoload is a host-startup convention; it is not an import |

---

## Design Classification Rule

When adding a feature, classify it first.

Ask:
1. Is this source, scope, metadata, phase, runner, or behavior?
2. Which existing concept should own it?
3. Which concepts does it compose with?
4. Which concepts must it NOT redefine?
