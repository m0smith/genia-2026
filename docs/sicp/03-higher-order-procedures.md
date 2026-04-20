# 03. Higher-Order Procedures

## Cold Open

If you copy the same loop shape three times and only swap the inner action, your code is begging for a better deal.

## What You'll Learn

- that functions are ordinary values in Genia
- how to pass a function into another function
- why `map`, `filter`, and `reduce` feel like reusable thought patterns

## Tiny Runnable Example

Prediction prompt: does Genia really let a function travel through another function?

```genia
square(x) = x * x
apply_twice(f, x) = f(f(x))

apply_twice(square, 2)
```
Classification: **Likely valid** (not directly tested)

```text
16
```

## Why This Matters

Higher-order code lets you reuse a process shape without copying the whole recipe.

## Core Concept

When a function can be passed around like a value, you can separate:

- the shape of the work
- the custom rule for each item

That is the heart of abstraction.

## Visual / Mental Model

Think of `map` as a cookie cutter.
The dough changes.
The cutter shape stays the same.

## Genia Implementation

- named functions are first-class values
- lambdas are implemented
- autoloaded helpers such as `map`, `filter`, and `reduce` are available

## Common Mistakes

- forgetting to pass the function value itself
- accidentally calling the helper too early

**Illustrative** — not runnable
```genia
apply_twice(square(2), 2)
```
Classification: **Illustrative** (not directly runnable)

That passes a number, not a function.

## Failure Case

If a higher-order helper expects a function and receives a plain value instead, the call fails at runtime.

## Exercises

1. Prediction: what does `map((x) -> x + 1, [1, 2, 3])` return?
2. Fix the bug: change `apply_twice(square(2), 3)` into a valid call.
3. Tiny build task: write `apply_three_times(f, x)`.

## Stretch Challenge

Write a `compose(f, g, x)` helper that runs `f(g(x))`.

## Reality Check

### ✅ Implemented

- functions as values
- lambdas
- `map`, `filter`, and `reduce`

### ⚠️ Partial

- there is no separate protocol system for "callable" beyond current runtime behavior

### ❌ Not Implemented

- static type-driven generic dispatch

## Summary

Higher-order procedures are how you stop rewriting the same work pattern and start reusing thought.
