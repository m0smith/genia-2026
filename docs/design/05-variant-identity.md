# Variant Templates (Alternatives / ADTs)

## Purpose

Variants define closed alternatives.

They answer:
> “This value is one of these cases.”

---

## Core Idea

A variant is a closed set:

    Result =
      Ok(value)
      Err(reason)

---

## Named Patterns

Variant constructors are patterns:

    Ok(v)
    Err(e)

---

## Matching

    match result
      Ok(v) -> ...
      Err(e) -> ...

---

## Binding

    Ok(v)

binds:
- v → inner value

---

## Composition

Variants wrap values:

    UserState =
      Loading
      Loaded(User)
      Failed(Error)

---

## Properties

- Closed set
- Explicit cases
- Exhaustive matching possible

---

## Existing Forms

    some(x)
    none

---

## Non-Goals

Variants do NOT:

- allow extension after definition
- behave like inheritance