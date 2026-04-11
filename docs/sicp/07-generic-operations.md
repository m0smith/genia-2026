# 07. Generic Operations

## Cold Open

You can survive by poking directly at data shapes.
You scale by deciding which pokes should stay behind a nicer boundary.

## What You'll Learn

- why abstraction barriers matter
- how small helper functions hide representation details
- what "generic" means in Genia today and what it does not mean

## Tiny Runnable Example

Prediction prompt: what does the caller get back if the representation changes but the helper stays the same?

```genia
point(x, y) = {x: x, y: y}
x_of(p) = p/x
y_of(p) = p/y

[x_of(point(3, 4)), y_of(point(3, 4))]
```

```text
[3, 4]
```

## Why This Matters

SICP loves the idea that callers should depend on an interface, not on storage trivia.
That idea still holds even in a much smaller language.

## Core Concept

An abstraction barrier is a polite lie.
You hide the internal layout so the rest of the program can stay calm when implementation details move.

## Visual / Mental Model

Think of the helper layer as a front desk.
Users talk to the desk, not to the filing cabinets in the back room.

## Genia Implementation

- ordinary helper functions are implemented
- maps are implemented and useful for data representation
- module boundaries also support representation-hiding style

## Common Mistakes

- leaking raw structure all over the codebase
- promising "generic dispatch" when you really just mean "helper functions"

## Failure Case

Genia does not currently provide a full protocol or multimethod system for generic arithmetic towers in the classic SICP sense.
Teach interface thinking, not imaginary dispatch machinery.

## Exercises

1. Prediction: if `point` adds an extra key, what breaks in callers that use `x_of` and `y_of`?
2. Rewrite for clarity: replace `p/x` in three places with `x_of(p)`.
3. Tiny build task: add `move_x(dx, p)`.

## Stretch Challenge

Wrap a tiny record representation behind helper functions and never access its raw keys outside those helpers.

## Reality Check

### ✅ Implemented

- abstraction barriers through functions
- representation-hiding through modules and helpers

### ⚠️ Partial

- you can model generic operations with conventions and helper layers, but not with a full generic arithmetic system

### ❌ Not Implemented

- protocols as a finished public SICP-style generic dispatch layer
- multimethods

## Summary

In Genia today, "generic" mostly means disciplined interfaces and representation independence, not a giant dispatch framework.
