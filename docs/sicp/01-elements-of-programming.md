# 01. Elements of Programming

## Cold Open

You changed one number in one place and the program got better.
Then you changed the same idea in three places and the program got worse.

That is the first programming lesson:
raw values are easy, but naming and combining them is where your brain stops drowning.

## What You'll Learn

- how Genia treats expressions as value-producing machines
- how names and functions reduce repetition
- how `some(...)` and `none(...)` already show up in everyday code

## Tiny Runnable Example

Prediction prompt: what comes back from this whole bundle?

```genia
square(x) = x * x

[1 + 2, square(4), some(7), none]
```
Classification: **Likely valid** (not directly tested)

```text
[3, 16, some(7), none("nil")]
```

## Why This Matters

If everything is an expression, you can keep composing without switching mental gears.
That makes Genia feel smaller than it really is.

## Core Concept

Genia leans hard on a simple rule:
expression in, value out.

Numbers do it.
Function calls do it.
Even absence values do it.

## Visual / Mental Model

Think of each expression as a tiny vending machine.
You put syntax in the slot and a value drops out.
Sometimes the snack is `42`.
Sometimes it is `some(7)`.
Sometimes the machine honestly says `none("nil")`.

## Genia Implementation

- literals, arithmetic, names, and function calls are implemented
- `none` normalizes to `none("nil")`
- `some(value)` is a real runtime value, not pseudo-syntax

## Common Mistakes

- forgetting that a function body is just an expression
- expecting `none` to be magic emptiness instead of an actual value

**Illustrative** — not runnable
```genia
square = x * x
```
Classification: **Illustrative** (not directly runnable)

That is assignment, not a function definition.

## Failure Case

If you use an unbound name, Genia tells you directly.
`square = x * x` fails because `x` is not defined in that scope.

## Exercises

1. Prediction: what does `[square(2), square(3)]` produce?
2. Fix the bug: turn `double = x + x` into a real function.
3. Rewrite for clarity: replace a repeated `n * n` with a named helper.

## Stretch Challenge

Write `sum_of_squares(a, b)` using `square`.

## Reality Check

### ✅ Implemented

- literals
- arithmetic
- names
- function calls
- `some(...)` and `none(...)`

### ⚠️ Partial

- this chapter only waves at absence pipelines; chapter 09 does the real work

### ❌ Not Implemented

- `if`
- statement-only `return`
- magical null behavior

## Summary

The big win here is not math.
It is the habit of seeing Genia code as little value machines you can name and recombine.
