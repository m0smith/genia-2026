# 10. State and Identity

## Cold Open

Most of Genia nudges you toward value transformation.
Then real programs whisper, "Yes, but what if I need one thing to change over time?"

That is where refs enter the room.

## What You'll Learn

- why state changes the questions you ask
- how refs provide a small explicit mutable cell
- why identity is different from value

## Tiny Runnable Example

Prediction prompt: what lives inside the ref after one update?

```genia
r = ref(10)
ref_update(r, (n) -> n + 5)
ref_get(r)
```

```text
15
```

## Why This Matters

SICP spends serious time on the cost of introducing state.
Genia keeps the surface small, but the conceptual warning still applies.

## Core Concept

A value is what something is.
Identity is which particular thing keeps existing while its contents change.

## Visual / Mental Model

Think of a ref as a labeled jar.
The label stays the same.
The contents can change.

## Genia Implementation

- refs are implemented as host-backed runtime cells
- `ref`, `ref_get`, `ref_set`, `ref_is_set`, and `ref_update` are implemented public helpers

## Common Mistakes

- reaching for refs when plain value transformation would do
- forgetting that state introduces timing and coordination questions

## Failure Case

Ref helpers expect an actual ref handle.
Passing an ordinary number where a ref is required produces a runtime error.

## Exercises

1. Prediction: what does `ref_get(ref(3))` return?
2. Fix the bug: swap the arguments in a broken `ref_update` call.
3. Tiny build task: make a ref that increments twice.

## Stretch Challenge

Model a tiny score counter with one ref and two helper functions.

## Reality Check

### ✅ Implemented

- refs
- explicit state update helpers

### ⚠️ Partial

- refs are host-backed capabilities, so this chapter teaches semantics, not storage internals

### ❌ Not Implemented

- widespread mutable object fields
- implicit shared-state safety guarantees

## Summary

State is powerful precisely because it complicates reasoning.
Genia keeps it explicit so you feel that tradeoff instead of hiding it.
