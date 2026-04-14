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

- the ants demos are now pure deterministic simulations with explicit world + RNG state threading; this does not change the concurrency model and does not use process/cell scheduling
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

## Actors

Actors build on cells to provide a message-passing stateful abstraction.

### Minimal example

```genia
handler(state, msg, _ctx) = ["ok", state + msg]
a = actor(0, handler)
actor_send(a, 5)
actor_send(a, 10)
```

Expected behavior:

- the handler receives `(state, msg, ctx)` and must return an effect: `["ok", new_state]` or `["reply", new_state, response]`
- for `actor_send`, any response in a `["reply", ...]` effect is discarded
- messages are processed one at a time in FIFO order
- after both messages drain, state is `15`

### Synchronous request-reply

```genia
handler(state, msg, _ctx) = ["reply", state + msg, state + msg]
a = actor(0, handler)
actor_call(a, 5)
```

Expected behavior:

- `actor_call(a, 5)` sends the message and blocks until the handler returns
- the handler returns `["reply", new_state, response]`
- `actor_call` returns the `response` value (`5` in this example)
- if the handler returns `["ok", new_state]` during an `actor_call`, the reply value is `new_state`
- if the handler throws, the reply is `none("actor-error")` and the actor enters failed state

### Edge case example

```genia
handler(state, msg, _ctx) = ["ok", state + msg]
a = actor(0, handler)
actor_alive?(a)
```

Expected behavior:

- `actor_alive?(a)` returns `true` while the backing worker thread is alive

### Failure case example

```genia
bad_handler(state, msg, _ctx) = "not-a-valid-effect"
a = actor(0, bad_handler)
actor_send(a, 1)
```

Expected behavior:

- the handler returns an invalid effect shape (not `["ok", new_state]` or `["reply", new_state, response]`)
- the actor's backing cell enters failed state
- subsequent `actor_send` calls raise `RuntimeError`

### actor_call failure case

```genia
failing(state, msg, _ctx) = 1 / 0
a = actor(0, failing)
actor_call(a, 1)
```

Expected behavior:

- the handler throws during `actor_call`
- the reply ref is set to `none("actor-error")` before the cell enters failed state
- `actor_call` returns `none("actor-error")` instead of blocking forever

### Actor API

| Helper | Description |
| --- | --- |
| `actor(initial_state, handler)` | Create an actor backed by a cell |
| `actor_send(actor, msg)` | Send a message for async processing |
| `actor_call(actor, msg)` | Send a message and block for the reply |
| `actor_alive?(actor)` | Check whether the worker thread is alive |

Handler shape: `handler(state, msg, ctx) -> ["ok", new_state]` or `handler(state, msg, ctx) -> ["reply", new_state, response]`

Effect protocol:

- `["ok", new_state]` — update state only (for `actor_send`; for `actor_call` the reply is `new_state`)
- `["reply", new_state, response]` — update state and deliver `response` to the caller
- both shapes are accepted by both `actor_send` and `actor_call`

### Current actor limitations

- actors are a thin prelude layer over cells
- no `actor_stop` (graceful shutdown) yet
- no supervision, links, or monitors
- failure semantics are inherited from cell fail-stop behavior
- `ctx` is `{}` for `actor_send`; `{reply_to: <ref>}` for `actor_call`
- if a handler throws during `actor_call`, the reply is `none("actor-error")` and the actor enters failed state

## Implementation status

### ✅ Implemented

- prelude-backed public ref/process helper surface with `help(...)` visibility
- host-backed process handles and message sending
- serialized handler execution per process
- fail-stop cell abstraction with cached error state
- restart semantics via `restart_cell`
- actor helpers: `actor`, `actor_send`, `actor_call`, `actor_alive?`

### ⚠️ Partial

- behavior depends on host-thread scheduling timing
- restart discards queued pre-restart updates in this phase instead of draining them
- cell errors are exposed as cached error strings (`some(error_string)`) rather than structured language error values
- actors are a thin prelude layer over cells; no public actor restart or stop API yet

### ❌ Not implemented

- language-level scheduler
- selective receive
- timeouts in message receive syntax
- `actor_stop` (graceful shutdown)
- supervision / links / monitors
- generalized flow runtime semantics (`|>` is expression-level composition only in Phase 1)
- lazy sequences
- multi-output flow stages
- backpressure and cancellation
