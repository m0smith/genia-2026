# Contracts (Boundary Guarantees)

## Purpose

Contracts define usage boundaries.

They answer:
> “What does this function accept and return?”

---

## Core Idea

Contracts reference patterns:

    fact(n: NaturalNumber) -> NaturalNumber

---

## Named Pattern Usage

Contracts use named patterns:

    process(user: User) -> Result

---

## Sources of Patterns

Contracts may reference:

- refinements
- open shapes
- closed shapes
- variants

---

## Behavior

- validated at runtime
- violations produce clear errors
- no coercion

---

## Benefits

- safer APIs
- clearer intent
- easier debugging

---

## Non-Goals

Contracts do NOT:

- define patterns
- enforce static typing
- replace pattern matching