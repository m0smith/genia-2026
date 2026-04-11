# 12. Laziness and Streams

## Cold Open

Sometimes the smartest computation is the one you have not done yet.

That sounds lazy because it is.
Useful lazy.

## What You'll Learn

- how `delay(...)` and `force(...)` work
- how streams differ from Flow
- why "only compute what you need" is a serious design move

## Tiny Runnable Example

Prediction prompt: does the delayed computation run once or twice here?

```genia
p = delay(1 + 2)

[force(p), force(p)]
```

```text
[3, 3]
```

## Why This Matters

Laziness changes cost.
It can also change architecture by letting you describe a potentially large process without paying for all of it up front.

## Core Concept

`delay(...)` stores work for later.
`force(...)` asks for the result.
Streams build on that idea with delayed tails.

## Visual / Mental Model

Imagine a stack of index cards face down.
You flip only the next card you need.

## Genia Implementation

- promises via `delay(...)` and `force(...)` are implemented
- stream helpers such as `stream_cons`, `stream_map`, `stream_filter`, and `stream_take` are implemented
- streams are distinct from Flow

## Common Mistakes

- mixing up streams and Flow
- assuming laziness appears automatically in ordinary expressions

## Failure Case

`delay(...)` is explicit.
If you do not delay the work, Genia evaluates the expression normally.

## Exercises

1. Prediction: what does `stream_take(2, stream_filter((x) -> x > 1, ...))` feel like conceptually?
2. Fix the bug: replace eager work with an explicit `delay(...)`.
3. Tiny build task: build a three-element lazy stream and take two items.

## Stretch Challenge

Explain, in one sentence, when you would choose Flow versus a stream.

## Reality Check

### ✅ Implemented

- `delay(...)`
- `force(...)`
- stream helpers

### ⚠️ Partial

- the stream library is intentionally small

### ❌ Not Implemented

- automatic lazy evaluation for the whole language

## Summary

Laziness is not about doing less work forever.
It is about doing work later, and only when later finally arrives.
