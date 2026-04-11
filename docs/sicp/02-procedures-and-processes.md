# 02. Procedures and Processes

## Cold Open

You can write a recursive function in ten seconds.
You can also accidentally build a stack-shaped disaster in ten seconds.

So the real question is not only, "Does it recurse?"
It is, "What process does that recursion create?"

## What You'll Learn

- how Genia function definitions describe processes
- the difference between recursive structure and tail-recursive process shape
- why proper tail calls matter

## Tiny Runnable Example

Prediction prompt: what does this accumulator version return?

```genia
sum_to(n, acc) =
  (0, acc) -> acc |
  (n, acc) -> sum_to(n - 1, acc + n)

sum_to(5, 0)
```

```text
15
```

## Why This Matters

Two functions can compute the same answer while using space very differently.
SICP cares about that, and Genia does too.

## Core Concept

A procedure is the thing you define.
A process is the shape of work it creates while running.

Tail position is the cheat code:
when the final action is the next call, Genia can reuse the same plate instead of stacking a new one.

## Visual / Mental Model

Ordinary recursion is a stack of plates.
Tail recursion is reusing the same plate.

## Genia Implementation

- named functions with case bodies are implemented
- proper tail-call optimization is implemented for calls in tail position
- pattern matching is the only conditional model

## Common Mistakes

- writing recursion that does extra work after the recursive call
- assuming every recursive function is automatically tail-recursive

**Conceptual example — not directly runnable**
```genia
fact(n) =
  0 -> 1 |
  n -> n * fact(n - 1)
```

That is recursive, but the multiplication happens after the call returns.

## Failure Case

A non-tail recursive process can still grow the work stack.
Genia guarantees tail calls, not magic optimization for every recursive shape.

## Exercises

1. Prediction: what does `sum_to(3, 10)` return?
2. Fill in the blank: finish a tail-recursive `countdown(n, acc)`.
3. Rewrite for clarity: convert a "do work after recursion" helper into accumulator style.

## Stretch Challenge

Implement a tail-recursive `reverse(xs, acc)` using pattern matching.

## Reality Check

### ✅ Implemented

- function definitions
- recursion
- case-style branching
- proper tail calls

### ⚠️ Partial

- the docs describe process shapes, but Genia does not expose a full profiler for visualizing them

### ❌ Not Implemented

- `if`
- imperative loop syntax beyond the existing `repeat` surface taught elsewhere in the main book

## Summary

SICP's old question still matters:
what process does your procedure create?
In Genia, tail position is where elegance turns into runtime leverage.
