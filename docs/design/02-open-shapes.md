# Open Shape Templates (Flexible Structure)

## Purpose

Open shapes define flexible structure.

They answer:
> “This value has at least this structure.”

---

## Core Idea

An open shape is a set of fields:

    {name, email}

---

## Named Patterns

Open shapes can be named:

    User = {name, email}

Usage:

    User({name, email})

---

## Matching Behavior

    match value
      User({name, email}) -> ...

Extra fields are allowed.

---

## Partial Matching

Patterns may match subsets:

    Named = {name}

    match value
      Named({name}) -> ...

---

## Composition

Shapes compose:

    a = {name: "Matt"}
    b = {email: "m@example.com"}

    c = merge(a, b)

---

## Key Properties

- Structural (not nominal)
- Extensible
- Partial matching allowed
- Field order does not matter

---

## Use Cases

- JSON data
- API responses
- pipeline transformations

---

## Failure Behavior

- Missing required fields → pattern miss

---

## Non-Goals

Open shapes do NOT:

- guarantee layout
- guarantee performance
- enforce exact structure
- replace closed shapes