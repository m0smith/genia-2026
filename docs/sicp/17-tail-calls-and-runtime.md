# 17. Tail Calls and Runtime

## Cold Open

Recursive elegance is cute until it blows the stack.
Tail calls are how elegance earns its keep.

## What You'll Learn

- what tail position means in runtime terms
- how Genia guarantees proper tail calls
- why that guarantee changes which recursive designs are practical

## Tiny Runnable Example

Prediction prompt: what does the runtime hand back after this tail-recursive walk?

```genia
countdown(n, acc) =
  (0, acc) -> acc |
  (n, acc) -> countdown(n - 1, acc + 1)

countdown(6, 0)
```

```text
6
```

## Why This Matters

Without tail-call optimization, some of the nicest recursive designs become performance lies.

## Core Concept

Tail position means the current function has nothing left to do after the call.
That lets the runtime reuse the same frame.

## Visual / Mental Model

Reusing the same plate.
No growing stack of dirty dishes.

## Genia Implementation

- proper tail-call optimization is implemented
- the current runtime uses an explicit trampoline
- final pipeline stages also preserve tail position

## Common Mistakes

- assuming a recursive call is tail-recursive just because it is near the end
- forgetting that extra arithmetic after the call breaks tail position

## Failure Case

`n * fact(n - 1)` is recursive, but not tail-recursive.
The multiplication still has to happen after the call returns.

## Exercises

1. Prediction: what does `countdown(2, 10)` return?
2. Fix the bug: convert a non-tail recursive helper into accumulator style.
3. Tiny build task: write a tail-recursive `sum_list(xs, acc)`.

## Stretch Challenge

Explain why tail-call optimization is a semantic guarantee here, not just a lucky optimization.

## Reality Check

### ✅ Implemented

- proper tail-call optimization
- tail position through function bodies, case arms, blocks, and final pipeline stages

### ⚠️ Partial

- non-tail recursion still consumes stack in the ordinary way

### ❌ Not Implemented

- magical optimization of every recursive shape

## Summary

Tail calls are where language semantics and runtime engineering shake hands.
