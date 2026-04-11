# 13. Code as Data

## Cold Open

The weirdest power move in SICP is not recursion.
It is looking at code and saying, "You are just another value now."

## What You'll Learn

- how Genia exposes expression structure as data
- how helper functions inspect quoted expressions
- why this matters before you even build an evaluator

## Tiny Runnable Example

Prediction prompt: what operator is hiding inside this quoted call?

```genia
operator(quote(add(1, 2)))
```

```text
add
```

## Why This Matters

If you can inspect program structure, you can teach a machine to transform or evaluate it.

## Core Concept

Quoted code is not mystical.
It is structured data with conventions.

## Visual / Mental Model

Take apart a toy robot and sort its pieces on a table.
You are not running it.
You are inspecting the pieces.

## Genia Implementation

- syntax helpers such as `operator`, `operands`, and `match_branches` are implemented
- quoted expressions use stable data shapes

## Common Mistakes

- assuming helpers work on arbitrary values instead of the expected quoted shape
- forgetting that quoted identifiers are symbols

## Failure Case

If a helper expects a specific expression kind and you hand it the wrong shape, it raises a clear error.

## Exercises

1. Prediction: what does `operator(quote(square(9)))` return?
2. Tiny build task: inspect the operands of a quoted call.
3. Rewrite for clarity: keep quoted data and evaluated data in separate names.

## Stretch Challenge

Quote a small expression and list, in prose, which syntax helper you would use to inspect each part.

## Reality Check

### ✅ Implemented

- quoted syntax as data
- syntax inspection helpers

### ⚠️ Partial

- this is still a compact helper layer, not a macro expander

### ❌ Not Implemented

- macro systems
- arbitrary compile-time rewriting pipelines

## Summary

Code-as-data is the bridge from "writing programs" to "reasoning about programs structurally."
