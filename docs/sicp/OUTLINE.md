# SICP with Genia — Outline

## Purpose

This document defines the **structure of the SICP with Genia book**.

- This is the **source of truth for WHAT to write**
- All chapters MUST align with this outline
- AGENTS.md defines HOW to write, not WHAT to write

---

## Book Philosophy

This book:
- Follows the spirit of SICP
- Uses **Genia as the implementation language**
- Uses **Head First / reptile-brain-aware teaching**
- ONLY teaches features that exist in Genia today

---

## Core Teaching Principles

- Start with **problems, not theory**
- Use **prediction before explanation**
- Favor **concrete → abstract**
- Use **small, composable examples**
- Highlight **failure cases**
- Reinforce with **repetition and variation**
- Make concepts **visual and narrative**

---

## Chapter Template (MANDATORY)

Each chapter MUST follow this structure:

1. Cold Open (problem, puzzle, or failure)
2. What You’ll Learn
3. Tiny Runnable Example
4. Why This Matters
5. Core Concept
6. Visual / Mental Model
7. Genia Implementation
8. Common Mistakes
9. Failure Case
10. Exercises
11. Stretch Challenge
12. Reality Check:
   - ✅ Implemented
   - ⚠️ Partial
   - ❌ Not Implemented
13. Summary

---

## Part I — Building Abstractions with Procedures

### 01. Elements of Programming
- values
- names
- expressions
- operators
- function calls
- `none` / `some`

### 02. Procedures and Processes
- function definitions
- recursion
- iterative vs recursive processes
- tail-call optimization

### 03. Higher-Order Procedures
- functions as values
- passing and returning functions
- map / filter / reduce patterns
- composition

---

## Part II — Building Abstractions with Data

### 04. Data Structures
- lists
- maps
- nesting
- structural thinking

### 05. Pattern Matching (Core Genia Feature)
- tuple matching
- list matching
- rest patterns
- matching `some` / `none`

### 06. Symbolic Data
- quote
- quasiquote
- unquote
- expression-as-data

### 07. Generic Operations
- abstraction barriers
- interface thinking
- representation independence

---

## Part III — Flow, Time, and State

### 08. Pipelines and Flow
- `|>` operator
- value vs flow
- flow stages
- CLI pipelines
- `stdin`, `stdout`

### 09. Absence and Option Semantics
- `none(reason)`
- `none(reason, context)`
- `some(value)`
- `map_some`, `flat_map_some`
- propagation vs failure

### 10. State and Identity
- refs
- mutation vs immutability
- identity vs value

### 11. Concurrency
- process helpers
- message passing concepts
- coordination

### 12. Laziness and Streams
- delayed computation
- flow-based thinking
- processing only what is needed

---

## Part IV — Metalinguistic Abstraction

### 13. Code as Data
- building expressions
- transforming expressions

### 14. Evaluators
- evaluation model
- environments
- small interpreter concepts

### 15. Language Variations
- alternative evaluation strategies
- extending the language

---

## Part V — Implementation and Runtime

### 16. Core IR
- lowering from syntax
- simplified internal representation

### 17. Tail Calls and Runtime
- stack behavior
- recursion efficiency

### 18. Machines and Compilation
- conceptual machines
- compilation pipeline
- future host support

---

## Enforcement Rules

- All chapters MUST exist in this outline
- No new chapters without updating this file
- Chapters MUST follow the template above
- Chapters MUST reflect current Genia capabilities