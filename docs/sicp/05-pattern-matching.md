# 05. Pattern Matching

## Cold Open

Most languages ask, "What condition is true?"
Genia asks, "What shape did you hand me?"

That is not a cosmetic difference.
It changes how you think.

## What You'll Learn

- how Genia matches tuples, lists, and options
- why order matters in pattern matching
- how rest patterns and `_` keep definitions compact

## Tiny Runnable Example

Prediction prompt: which branch wins for each call?

```genia
describe(xs) =
  [] -> 0 |
  [x, .._] -> x

[describe([]), describe([5, 6])]
```

```text
[0, 5]
```

## Why This Matters

Pattern matching is Genia's conditional model.
If you learn this well, the rest of the language gets dramatically simpler.

## Core Concept

Patterns are lock shapes.
Values are keys.
The first key that fits opens the branch.

## Visual / Mental Model

Lock and key.
Not "run a test suite of booleans."
Not "write an `if` ladder."

## Genia Implementation

- tuple patterns are implemented
- list patterns with final rest are implemented
- `some(pattern)` and literal/structured `none(...)` matching are implemented
- guards with `?` are implemented

## Common Mistakes

- putting the catch-all branch too early
- trying to use rest patterns in the middle of a list pattern

**Example only — not runnable**
```genia
bad(xs) =
  [first, ..rest, last] -> first
```

## Failure Case

`..rest` must be the final list-pattern item.
If you move it earlier, the parser rejects the definition.

## Exercises

1. Prediction: what does `describe([9])` return?
2. Fix the bug: move a wildcard branch after the specific branch.
3. Tiny build task: write `first_or_zero(xs)`.

## Stretch Challenge

Write a matcher for `some(x)` and `none(...)` that returns a number in both cases.

## Reality Check

### ✅ Implemented

- tuple patterns
- list patterns
- rest patterns
- option matching
- guards

### ⚠️ Partial

- map patterns are implemented, but this chapter keeps the first pass focused on the core mental model

### ❌ Not Implemented

- `if`
- `switch`
- regex capture patterns

## Summary

In Genia, branching is shape-matching.
That single idea does a lot of work.
