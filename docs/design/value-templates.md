
# Value Templates

## Status

Proposed

---

## Purpose

Value Templates define how values can:

* be constrained (refinement)
* be structured (shapes)
* be combined (composition)
* be used at boundaries (contracts)

They enable **structural compatibility** without requiring values to be copied into new nominal types.

---

## Core Principle

> Templates define patterns.
> Patterns match values.
> Compatible values can be used through templates without copying.

---

# Template Kinds

## Refinement

Refinements constrain values with predicates.

```genia
NaturalNumber = n : n >= 0
Even = n : n % 2 == 0
```

* evaluated at use/match time
* predicate false ⇒ failure
* does not create a new runtime type

---

## Open Shape

Open shapes define required structure with optional extra fields.

```genia
Named = {name, ..}
Located = {x, y, ..}
```

* structural
* extensible
* composable

---

## Closed Shape

Closed shapes define fixed structure.

### Record form

```genia
Point = {x, y}
```

### Positional labeled form

```genia
Person = [name, age, city]
```

* fixed arity
* predictable layout
* eligible for efficient access

---

## Variant

Variants define a closed set of alternatives.

```genia
Result = Ok(value) | Err(reason)
Maybe = Some(value) | None
```

---

## Contract

Contracts define boundary expectations.

```genia
distance :: Point, Point -> Number
render :: Named & Located -> none
```

* built from templates
* runtime-checked

---

# Template Composition

Templates compose using `&`.

```genia
A & B
```

Meaning:

> value must satisfy both templates

---

## Examples

### Refinement

```genia
Positive = n : n > 0
Even = n : n % 2 == 0
PositiveEven = Positive & Even
```

### Shape

```genia
Named = {name, ..}
Located = {x, y, ..}
NamedLocated = Named & Located
```

### Shape + Refinement

```genia
SafePoint = {x, y} & (x >= 0 and y >= 0)
```

---

## Initial Composition Scope

Supported:

* refinement & refinement
* open shape & open shape
* shape & refinement
* closed shape & refinement

Not yet supported:

* variant composition with `&`
* arbitrary higher-order combinations

---

# Template Application

## Overview

Templates can be applied to compatible values without copying or converting them.

This enables structural reuse of data.

---

## Operator Family

```genia
value @ Template     # apply
value @? Template    # check
value @! Template    # assert (strict)
```

---

## `@` — Apply

```genia
user @ NamedLocated
```

* returns the same value viewed through the template
* fails with runtime error if incompatible
* no copying
* no identity change

---

## `@?` — Check

```genia
user @? NamedLocated
```

* returns true or false
* does not apply the template
* does not raise errors

---

## `@!` — Strict Apply

```genia
user @! NamedLocated
```

* equivalent to `@`, but explicitly signals required success
* useful for invariants and debugging

---

## Semantics

Template application:

* does not change representation
* does not allocate new structures by default
* does not introduce a new nominal identity

---

## Compatibility

Template application works best with:

* refinements
* open shapes
* composed templates

More restricted for:

* closed shapes
* variants

---

# Labeled Positional Templates

## Purpose

Provide:

* compact positional storage
* named access
* efficient lookup

---

## Definition

```genia
Person = [name, age, city]
```

---

## Application

```genia
p = ["Matt", 42, "Bountiful"] @ Person
```

---

## Access

```genia
p/name
p/age
p/city
```

Semantics:

* labels map to fixed positions
* access is O(1)

---

## Important Rule

Named access is only valid through a template view:

```genia
["Matt", 42, "Bountiful"]/name   # invalid
```

```genia
(["Matt", 42, "Bountiful"] @ Person)/name   # valid
```

---

## Pattern Use

```genia
Person(name, age, city)
```

---

# Unified Operator Table

| Symbol | Meaning                |                      |
| ------ | ---------------------- | -------------------- |
| `=`    | define template        |                      |
| `:`    | constrain (refinement) |                      |
| `..`   | open structure         |                      |
| `&`    | composition            |                      |
| `      | `                      | variant alternatives |
| `::`   | contract               |                      |
| `@`    | apply template         |                      |
| `@?`   | check compatibility    |                      |
| `@!`   | assert apply           |                      |

---

# Example

```genia
Natural = n : n >= 0
Even = n : n % 2 == 0
NaturalEven = Natural & Even

Named = {name, ..}
Located = {x, y, ..}
NamedLocated = Named & Located

Person = [name, age, city]

render :: NamedLocated -> none

p = ["Matt", 42, "Bountiful"] @ Person
p/name
p/age

user = {name: "Matt", x: 1, y: 2}

user @? NamedLocated
  |> some(u) -> render(u)
  |> none -> skip
```

---

# Non-Goals

* no nominal type hierarchy
* no inheritance
* no required data copying
* no hidden structural mutation
* no implicit template application (initially)
* no full static type system

---

# Design Rule

> Behavior attaches to compatible values, not to nominal containers.

---

# Future Work

* implicit template application at contract boundaries
* richer composition rules
* closed-shape optimization strategies
* variant interaction rules

---

If you want next, I’d recommend:

👉 adding a short **cheatsheet version** (10–15 lines max)
👉 and then generating a **SPEC prompt just for `@` semantics** so implementation stays tight
