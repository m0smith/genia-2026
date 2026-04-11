# 11. Concurrency

## Cold Open

One process is a story.
Two processes are a scheduling problem.

The moment work overlaps in time, your tidy mental model starts sweating.

## What You'll Learn

- what Genia exposes today for lightweight process work
- why message passing is easier to reason about than shared mutation
- where the current concurrency surface is still intentionally small

## Tiny Runnable Example

Prediction prompt: what does Genia say about a fresh spawned process?

```genia
p = spawn((msg) -> msg)

process_alive?(p)
```

```text
true
```

## Why This Matters

Concurrency is where "works on my machine" turns into "why did that happen in that order?"
SICP's warning lights still matter.

## Core Concept

Message passing lets you think in terms of isolated workers instead of one giant shared soup.

## Visual / Mental Model

Picture actors passing notes through slots in a door.
You do not reach inside the other room.

## Genia Implementation

- `spawn`, `send`, and `process_alive?` are implemented
- process handles are runtime capability values

## Common Mistakes

- assuming concurrent behavior is deterministic just because the code looks short
- teaching process helpers as if they were a full distributed-systems framework

## Failure Case

Concurrency does not remove coordination problems.
It gives you explicit tools and asks you to use them carefully.

## Exercises

1. Prediction: what does `process_alive?(p)` likely return right after `spawn(...)`?
2. Tiny build task: spawn a process and send it one message.
3. Rewrite for clarity: separate process creation from later messaging.

## Stretch Challenge

Sketch a tiny supervisor idea in prose before writing any code.

## Reality Check

### ✅ Implemented

- process helpers
- message passing primitives

### ⚠️ Partial

- the public surface is intentionally small and host-backed

### ❌ Not Implemented

- a large concurrency framework
- formal distributed semantics

## Summary

Genia gives you concurrency tools, but it does not pretend concurrency stops being hard.
