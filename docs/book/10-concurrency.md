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

- the pure ants demo uses explicit world + RNG state threading; this does not change the concurrency model and does not use process/cell scheduling
- `examples/ants_terminal.genia --mode actor` uses the actor/coordinator ants session from `examples/ants_actor.genia` as a teaching comparison while staying inside the current actor helper model
- `examples/ants_web.genia` can select pure or actor mode through its reset JSON/config UI, but it remains an HTTP/browser viewer over the same session helpers rather than a browser scheduler or browser-native Genia runtime
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
  - `cell_stop`
- cells process at most one queued update at a time
- failed updates preserve last successful state
- failed cells cache an error string and reject future `cell_send` / `cell_get`
- `restart_cell` clears failure/stopped state, discards queued pre-restart updates, and relaunches the worker thread if it has exited
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

- the handler receives `(state, msg, ctx)` and must return a tagged effect
- supported effects: `["ok", new_state]`, `["reply", new_state, response]`, `["stop", reason, new_state]`
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
- if the handler throws, the reply is `none("actor-error")` and the actor enters failed state

### actor_call with `["ok", new_state]`

```genia
handler(state, msg, _ctx) = ["ok", state + msg]
a = actor(0, handler)
actor_call(a, 3)
```

Expected behavior:

- the handler returns `["ok", new_state]` instead of `["reply", ...]`
- `actor_call` replies with `new_state` (`3` in this example)
- the same handler works with both `actor_send` and `actor_call`

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

- the handler returns an invalid effect shape (not `["ok", ...]`, `["reply", ...]`, or `["stop", ...]`)
- the actor's backing cell enters failed state with an error showing the received value and expected shapes
- subsequent `actor_send` calls raise `RuntimeError`

### Handler-initiated stop

```genia
handler(state, msg, _ctx) = ["stop", "done", state + msg]
a = actor(0, handler)
actor_send(a, 42)
```

Expected behavior:

- the handler returns `["stop", reason, new_state]`
- the final state (`42`) is committed
- the actor stops after processing the current message
- `actor_status(a)` returns `"stopped"` after the worker exits
- subsequent `actor_send` calls raise `RuntimeError`

When `actor_call` receives a `["stop", ...]` effect, the reply is `none("actor-stopped")`.

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
| `actor_stop(actor)` | Gracefully stop after draining the mailbox |
| `actor_restart(actor, new_state)` | Restart a failed or stopped actor with new state |
| `actor_state(actor)` | Read current state without sending a message |
| `actor_failed?(actor)` | Check whether the actor has failed |
| `actor_error(actor)` | Return `none` or `some(error_string)` |
| `actor_status(actor)` | Return `"ready"`, `"failed"`, or `"stopped"` |

Handler shape: `handler(state, msg, ctx) -> effect`

Effect protocol:

- `["ok", new_state]` — update state only (for `actor_send`; for `actor_call` the reply is `new_state`)
- `["reply", new_state, response]` — update state and deliver `response` to the caller
- `["stop", reason, new_state]` — commit final state and stop the actor (for `actor_call` the reply is `none("actor-stopped")`)
- all three shapes are accepted by both `actor_send` and `actor_call`
- any other return shape is rejected with a clear error showing the received value and expected shapes

### Current actor limitations

- actors are implemented on top of host-backed processes (cells with worker threads)
- actors are a thin prelude layer over cells
- no selective receive
- no timeouts in message receive
- no deterministic scheduling
- no supervision, links, or monitors
- failure semantics are inherited from cell fail-stop behavior
- `ctx` is `{}` for `actor_send`; `{reply_to: <ref>}` for `actor_call`
- if a handler throws during `actor_call`, the reply is `none("actor-error")` and the actor enters failed state
- the ants terminal UI actor mode is still an explicit blocking tick loop, not a scheduler, selective receive system, or real-time event loop
- the ants browser viewer actor mode uses ordinary HTTP requests and JSON snapshots over that same coordinator session; browser run/pause is implemented by repeated `/step` calls from JavaScript

### Actor demo: ants colony (`examples/ants_actor.genia`)

This demo runs the same colony simulation from `examples/ants.genia` using the actor model.
A coordinator actor owns the authoritative world state.
Ant workers request sense data and submit move intents through `actor_call`.
The terminal developer UI can select this execution structure with `--mode actor`.
The browser viewer can select it with reset config/UI mode `actor`.

Architecture:

- **Coordinator**: single actor holding the world map; processes `["sense", ant_id]`, `["move_intent", ant_id, move]`, `["tick"]`, `["snapshot"]`, and `["stop"]` messages
- **Tick loop**: explicit coordinator-driven ant ordering for deterministic reproducibility
- **Reuse**: imports and calls the pure scoring/movement logic from `ants.genia` via `import ants`

Minimal example:

```genia
import ants_actor
world = ants/new_world(7, 2, 5, 5)
w = ants_actor/run_actor_sim(world, 3)
ants/world_tick(w)
```

Expected behavior:

- creates a 5×5 world with 2 ants seeded at 7
- runs 3 actor-driven ticks (sense → intent → apply → evaporate per tick)
- returns the final world; `world_tick(w)` is `3`

This demo does **not** add new language syntax, does **not** introduce a scheduler, and does **not** require selective receive or timeouts.

### Browser viewer: ants colony (`examples/ants_web.genia`)

The browser viewer serves HTML, CSS, JavaScript, and JSON through the current host-backed HTTP helper.
It keeps one current simulation session in server memory and exposes small endpoints:

- `GET /state` returns a JSON snapshot of tick, seed, mode, grid size, ants, nest cells, food cells, pheromones, delivered food, remaining food, and stats
- `POST /reset` rebuilds the current pure or actor session from JSON config
- `POST /step` advances one tick and returns a fresh snapshot

The browser renders the grid with Canvas and implements run/pause by repeatedly calling `/step`.
This is a demo/viewer layer only: it does **not** add a browser-native Genia runtime, WebSockets, SSE, a language scheduler, or a generalized server event loop.

## Implementation status

### ✅ Implemented

- prelude-backed public ref/process helper surface with `help(...)` visibility
- host-backed process handles and message sending
- serialized handler execution per process
- fail-stop cell abstraction with cached error state
- restart semantics via `restart_cell`
- actor helpers: `actor`, `actor_send`, `actor_call`, `actor_alive?`, `actor_stop`, `actor_restart`, `actor_state`, `actor_failed?`, `actor_error`, `actor_status`
- standardized actor handler effect protocol: `["ok", ...]`, `["reply", ...]`, `["stop", ...]`
- clear error messages for invalid handler return shapes (shows received value)
- cell graceful stop via `cell_stop`
- restart semantics work after both failure and stop (worker thread relaunched if exited)

### ⚠️ Partial

- behavior depends on host-thread scheduling timing
- restart discards queued pre-restart updates in this phase instead of draining them
- cell errors are exposed as cached error strings (`some(error_string)`) rather than structured language error values
- actors are a thin prelude layer over cells

### ❌ Not implemented

- language-level scheduler
- selective receive
- timeouts in message receive syntax
- selective receive
- timeouts in message receive syntax
- deterministic scheduling
- supervision / links / monitors
- generalized flow runtime semantics (`|>` is expression-level composition only in Phase 1)
- lazy sequences
- multi-output flow stages
- backpressure and cancellation
