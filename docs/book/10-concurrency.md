# Chapter 10: Concurrency

Genia currently exposes host-backed concurrency primitives and a runtime-backed fail-stop cell helper layer in stdlib.
The public `ref`, `spawn`, `send`, and `process_alive?` names are thin prelude wrappers over that host-backed runtime layer.

## Minimal example

```genia
counter = cell(0)
cell_send(counter, (n) -> n + 1)
cell_get(counter)
```

Expected behavior:

- update runs asynchronously
- after the mailbox drains, `cell_get(counter)` returns `1`

## Edge case example

```genia
state = ref(1)
a = cell_with_state(state)
cell_send(a, (x) -> x + 1)
cell_send(a, (_) -> map_get(1, "bad"))
```

Expected behavior:

- first update succeeds
- second update fails
- backing ref still holds `2`
- `cell_failed?(a)` becomes `true`
- `cell_error(a)` returns `some(error_string)`

## Failure case example

```genia
cell_send(cell(0), 42)
```

Expected behavior:

- raises `TypeError` because `cell_send` expects a callable update function.

## Current model

- public ref helpers from `src/genia/std/prelude/ref.genia`:
  - `ref`, `ref_get`, `ref_set`, `ref_is_set`, `ref_update`
- `spawn(handler)` creates a host-thread process with FIFO mailbox semantics
- `send(process, message)` enqueues messages
- `process_alive?(process)` checks worker liveness
- public process helpers from `src/genia/std/prelude/process.genia`:
  - `spawn`, `send`, `process_alive?`
- stdlib cell helpers:
  - `cell`, `cell_with_state`
  - `cell_send`, `cell_get`, `cell_state`
  - `cell_failed?`, `cell_error`
  - `restart_cell`, `cell_status`, `cell_alive?`
- cells process at most one queued update at a time
- failed updates preserve last successful state
- failed cells cache an error string and reject future `cell_send` / `cell_get`
- `restart_cell` clears failure and discards queued pre-restart updates in this phase
- nested `cell_send` calls made during an update are committed only if that update succeeds

## Implementation status

### ✅ Implemented

- prelude-backed public ref/process helper surface with `help(...)` visibility
- host-backed process handles and message sending
- serialized handler execution per process
- fail-stop cell abstraction with cached error state
- restart semantics via `restart_cell`

### ⚠️ Partial

- behavior depends on host-thread scheduling timing
- restart discards queued pre-restart updates in this phase instead of draining them
- cell errors are exposed as cached error strings (`some(error_string)`) rather than structured language error values

### ❌ Not implemented

- language-level scheduler
- selective receive
- timeouts in message receive syntax
- generalized flow runtime semantics (`|>` is expression-level composition only in Phase 1)
- lazy sequences
- multi-output flow stages
- backpressure and cancellation
