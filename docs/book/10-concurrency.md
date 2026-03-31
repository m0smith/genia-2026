# Chapter 10: Concurrency

Genia currently exposes host-backed concurrency primitives and a small agent helper layer in stdlib.

## Minimal example

```genia
counter = agent(0)
agent_send(counter, (n) -> n + 1)
agent_get(counter)
```

## Edge case example

```genia
a = agent("idle")
agent_alive?(a) -> true
```

## Failure case example

```genia
agent_send(["not", "an", "agent"], (x) -> x)
```

Expected behavior:

- runtime pattern-match failure because the input does not match the agent tuple shape.

## Current model

- `spawn(handler)` creates a host-thread process with FIFO mailbox semantics
- `send(process, message)` enqueues messages
- `process_alive?(process)` checks worker liveness
- stdlib agent helpers: `agent`, `agent_send`, `agent_get`, `agent_state`, `agent_alive?`

## Implementation status

### ✅ Implemented

- host-backed process handles and message sending
- serialized handler execution per process
- agent abstraction in stdlib

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
