# Closed Shape Templates (Structs)

## Purpose

Closed shapes define fixed structure.

They answer:
> “This value has exactly this structure.”

---

## Core Idea

A closed shape is a fixed set of fields:

    Point2(x, y)
    User(id, name, email)

---

## Named Patterns

Closed shapes define patterns automatically:

    Point2(x, y)

Usage:

    match p
      Point2(x, y) -> ...

---

## Binding

    Point2(x, y)

binds:
- x, y → fields

---

## Matching Behavior

- Exact structure required
- No extra fields allowed

---

## Key Properties

- Fixed layout
- Efficient access
- Predictable structure

---

## Performance Goal

Closed shapes should support:

- direct field access
- compact representation

---

## Composition

Closed shapes compose by definition, not merging.

---

## Non-Goals

Closed shapes do NOT:

- behave like maps
- allow extension
- support inheritance

---

## Critical Rule

Closed shapes are not open shapes.