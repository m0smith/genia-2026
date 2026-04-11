# 08. Pipelines and Flow

## Cold Open

You have data.
Then you have data moving.
Those are not the same feeling.

Pipelines are where Genia starts acting like a conveyor belt instead of a calculator.

## What You'll Learn

- how `|>` rewires call shape
- how value pipelines differ from Flow pipelines
- why CLI pipe mode feels Unix-ish without becoming a separate language

## Tiny Runnable Example

Prediction prompt: what hits the end of the conveyor belt?

```genia
inc(x) = x + 1
double(x) = x * 2

3 |> inc |> double
```

```text
8
```

## Why This Matters

Pipelines make sequential transformation readable.
Flow makes that idea lazy and stream-shaped.

## Core Concept

`|>` feeds the current value into the next stage.
With plain values, that feels direct.
With Flow values, it becomes a data conveyor belt.

## Visual / Mental Model

Picture a conveyor belt.
Each station changes, filters, or consumes the item moving past it.

## Genia Implementation

- `|>` is implemented
- ordinary pipeline call shapes are implemented
- Flow is a runtime value family
- `lines`, `each`, `collect`, and `run` are implemented public helpers

## Common Mistakes

- confusing value pipelines with Flow pipelines
- forgetting that `-p` mode already injects `stdin |> lines |> ... |> run`

**Conceptual example — not directly runnable**
```genia
stdin |> lines |> map(trim) |> filter((line) -> line != "") |> each(print)
```

## Failure Case

Flow does not appear magically.
You need explicit Flow-producing or Flow-consuming stages.

## Exercises

1. Prediction: what does `10 |> inc |> inc` return?
2. Rewrite for clarity: turn nested calls into a pipeline.
3. Tiny build task: make a three-stage numeric pipeline.

## Stretch Challenge

Take a shell one-liner you use often and sketch the matching Genia Flow pipeline.

## Reality Check

### ✅ Implemented

- value pipelines
- Flow runtime
- CLI pipe mode
- explicit Flow helper stages

### ⚠️ Partial

- later chapters still keep Flow examples small because debugging and orchestration surfaces are intentionally minimal

### ❌ Not Implemented

- implicit value-to-Flow conversion everywhere
- invisible stream magic

## Summary

Pipelines make transformation readable.
Flow turns that readability into streaming behavior without inventing a second language.
