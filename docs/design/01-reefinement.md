# Refinement Templates (Value Constraints)

## Purpose

Refinements constrain values.

They answer:
> “This value is valid only if it satisfies a condition.”

---

## Core Idea

A refinement is:

    Value + Predicate

Example:

    NaturalNumber = n when n >= 0

---

## Named Patterns

Refinements are named patterns:

    NaturalNumber = n when n >= 0

Usage:

    NaturalNumber(x)

---

## Binding

    NaturalNumber(n)

binds:
- n → matched value

---

## Composition

Refinements compose:

    Positive =
      NaturalNumber(n) when n > 0

    PositiveEven =
      Positive(n) when n % 2 == 0

---

## Pattern Usage

    fact =
      0 -> 1
      NaturalNumber(n) when n > 0 -> n * fact(n - 1)

---

## Failure Behavior

- Mismatch = pattern miss
- No coercion
- No implicit conversion

---

## Design Principles

- Pattern-first
- Runtime evaluated
- Composable
- Minimal syntax

---

## Non-Goals

Refinements do NOT:

- create new runtime representations
- enforce compile-time guarantees (initially)
- replace pattern matching