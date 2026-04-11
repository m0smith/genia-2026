# SICP with Genia — Outline

## Purpose

This document defines the structure of the SICP-with-Genia learning system.

- this is the source of truth for WHAT to write
- `WRITING_GUIDE.md` defines HOW to write it
- `AGENTS.MD` defines workflow and validation

Only teach behavior that exists in Genia today.

## Book Philosophy

This book should feel like:

- SICP in spirit
- Genia in syntax and semantics
- Head First in delivery
- truthful to the current implementation

## Core Teaching Principles

- start with tension, not definitions
- ask for predictions before answers
- move from tiny concrete examples to mental models
- include failure cases and common traps
- keep examples small, vivid, and runnable
- repeat core metaphors so the reader remembers them

## Chapter Template

Every chapter must use this section order:

1. `## Cold Open`
2. `## What You'll Learn`
3. `## Tiny Runnable Example`
4. `## Why This Matters`
5. `## Core Concept`
6. `## Visual / Mental Model`
7. `## Genia Implementation`
8. `## Common Mistakes`
9. `## Failure Case`
10. `## Exercises`
11. `## Stretch Challenge`
12. `## Reality Check`
13. `## Summary`

`## Reality Check` must contain these exact subheadings:

- `### ✅ Implemented`
- `### ⚠️ Partial`
- `### ❌ Not Implemented`

## Part I — Building Abstractions with Procedures

### 01. Elements of Programming

- values
- names
- expressions
- operators
- function calls
- `none` and `some`

### 02. Procedures and Processes

- function definitions
- recursion
- iterative versus recursive processes
- tail-call optimization

### 03. Higher-Order Procedures

- functions as values
- passing and returning functions
- `map` / `filter` / `reduce` patterns
- composition

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
- matching `some` and `none`

### 06. Symbolic Data

- `quote`
- `quasiquote`
- `unquote`
- expression-as-data

### 07. Generic Operations

- abstraction barriers
- interface thinking
- representation independence

## Part III — Flow, Time, and State

### 08. Pipelines and Flow

- `|>` operator
- value versus flow
- flow stages
- CLI pipelines
- `stdin` and `stdout`

### 09. Absence and Option Semantics

- `none(reason)`
- `none(reason, context)`
- `some(value)`
- `map_some`
- `flat_map_some`
- propagation versus recovery

### 10. State and Identity

- refs
- mutation versus immutability
- identity versus value

### 11. Concurrency

- process helpers
- message-passing concepts
- coordination

### 12. Laziness and Streams

- delayed computation
- stream thinking
- processing only what is needed

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

## Planned Chapter Files

The chapter set defined by this outline is:

- `01-elements-of-programming.md`
- `02-procedures-and-processes.md`
- `03-higher-order-procedures.md`
- `04-data-structures.md`
- `05-pattern-matching.md`
- `06-symbolic-data.md`
- `07-generic-operations.md`
- `08-pipelines-and-flow.md`
- `09-absence-and-option-semantics.md`
- `10-state-and-identity.md`
- `11-concurrency.md`
- `12-laziness-and-streams.md`
- `13-code-as-data.md`
- `14-evaluators.md`
- `15-language-variations.md`
- `16-core-ir.md`
- `17-tail-calls-and-runtime.md`
- `18-machines-and-compilation.md`
