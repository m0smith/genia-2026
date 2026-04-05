# Chapter 10: Concurrency

Genia currently exposes host-backed concurrency primitives and a small cell helper layer in stdlib.

## Minimal example

```genia
counter = cell(0)
cell_send(counter, (n) -> n + 1)
cell_get(counter)
```

## Edge case example

```genia
a = cell("idle")
cell_alive?(a) -> true
```

## Failure case example

```genia
cell_send(["not", "a", "cell"], (x) -> x)
```

Expected behavior:

- runtime pattern-match failure because the input does not match the cell tuple shape.

## Current model

- `spawn(handler)` creates a host-thread process with FIFO mailbox semantics
- `send(process, message)` enqueues messages
- `process_alive?(process)` checks worker liveness
- stdlib cell helpers: `cell`, `cell_send`, `cell_get`, `cell_state`, `cell_alive?`

## Implementation status

### ✅ Implemented

- host-backed process handles and message sending
- serialized handler execution per process
- cell abstraction in stdlib

### ⚠️ Partial

- behavior depends on host-thread scheduling timing

### ❌ Not implemented

- language-level scheduler
- selective receive
- timeouts in message receive syntax
- generalized flow runtime semantics (`|>` is expression-level composition only in Phase 1)
- lazy sequences
- multi-output flow stages
- backpressure and cancellation
