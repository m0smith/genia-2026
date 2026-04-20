# 09. Absence and Option Semantics

## Cold Open

The annoying bug is not the missing value.
It is the lie that the value was definitely there.

Genia tries hard not to tell that lie.

## What You'll Learn

- how `some(...)` and `none(...)` model presence and absence
- how structured `none(reason, context)` carries useful metadata
- how explicit helpers control recovery

## Tiny Runnable Example

Prediction prompt: does the pipeline unwrap the `some(...)`, and what comes out at the end?

```genia
inc(x) = x + 1

some(3) |> inc
```
Classification: **Likely valid** (not directly tested)

```text
some(4)
```

## Why This Matters

Absence is not rare.
It happens in lookups, parsing, indexing, and string search.
If the language handles it honestly, your code gets easier to trust.

## Core Concept

`some(value)` means "we have one."
`none(...)` means "we do not, and here is why."

Recovery is explicit.
That is the point.

## Visual / Mental Model

Think of `none(...)` as a broken track on the conveyor belt.
The train does not pretend the rail is fine.

## Genia Implementation

- `some(...)` and structured `none(...)` are implemented
- maybe-aware helpers such as `get`, `nth`, `find`, and `parse_int` are implemented
- pipeline lifting over `some(...)` and short-circuit on `none(...)` are implemented

## Common Mistakes

- assuming `some(...)` disappears automatically into a raw value
- forgetting to recover with `unwrap_or(...)` when you need a plain value

## Failure Case

If you pipeline a `none(...)` into later stages, those later stages do not run.
The same absence value comes back unchanged.

## Exercises

1. Prediction: what does `parse_int("41") |> map_some((n) -> n + 1)` return?
2. Fix the bug: turn a maybe result into a plain fallback with `unwrap_or`.
3. Tiny build task: chain two `get(...)` calls through a pipeline.

## Stretch Challenge

Write a small nested lookup that returns a default string when any hop is missing.

## Reality Check

### ✅ Implemented

- `some(...)`
- `none(reason, context?)`
- structured absence metadata
- explicit recovery helpers
- pipeline propagation rules

### ⚠️ Partial

- naming migration is still visible in compatibility helpers such as `get?`, `first_opt`, and `nth_opt`

### ❌ Not Implemented

- null-pointer-style silent failure
- implicit fallback values

## Summary

Genia treats absence as data, not as a hidden trap door.
That makes failures easier to inspect and pipelines easier to reason about.
