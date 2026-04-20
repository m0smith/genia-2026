# Patterns in Genia

## Core Model

Templates define patterns.  
Patterns match values.  
Values are matched, not inspected imperatively.

---

## Named Patterns

Patterns can be named:

    NaturalNumber = n when n >= 0

Usage:

    NaturalNumber(x)

Equivalent to:

    x when x >= 0

---

## Binding

Patterns bind values:

    NaturalNumber(n)
    Point2(x, y)
    {name, email}

Bindings are local to the match branch.

---

## Pattern Categories

All templates produce patterns:

- Refinement → value constraints
- Open Shape → flexible structure
- Closed Shape → exact structure
- Variant → alternatives
- Contract → uses patterns (does not define them)

---

## Composition

Patterns compose:

    Positive =
      NaturalNumber(n) when n > 0

    SmallPositive =
      Positive(n) when n < 100

---

## Matching Behavior

- Patterns either match or do not match
- No coercion
- No implicit conversion
- Failure = pattern miss

---

## Design Principles

- Pattern-first
- Minimal syntax
- Runtime-evaluated
- Composable

---

## Non-Goals

Patterns do NOT:

- create a static type system
- introduce implicit conversions
- replace explicit matching 