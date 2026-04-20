# Chapter 10: Concurrency

Genia provides host-backed concurrency primitives layered as:

1. **Refs** — synchronized mutable references
2. **Processes** — fire-and-forget mailbox workers
3. **Cells** — serialized stateful workers with fail-stop error handling
4. **Actors** — a thin prelude layer over cells adding a message/effect protocol

All concurrency is backed by Python host threads in this phase.
The actor surface here is public Python-reference-host behavior in this phase, not a shared cross-host portability contract.
There is no language-level scheduler, no deterministic timing, and no Erlang-style guarantees.

## Minimal example

```genia
counter = cell(0)
cell_send(counter, (n) -> n + 1)
cell_get(counter)
```

Expected behavior:

- update runs asynchronously on a worker thread
- after the mailbox drains, `cell_get(counter)` returns `1`

## Edge case example

```genia
state = ref(1)
a = cell_with_state(state)
cell_send(a, (x) -> x + 1)
cell_send(a, (_) -> map_get(1, "bad"))
```

Expected behavior:

- first update succeeds, state becomes `2`
- second update fails
- backing ref still holds `2`
- `cell_failed?(a)` becomes `true`
- `cell_error(a)` returns `some(error_string)`

## Failure case example

```genia
cell_send(cell(0), 42)
```

Expected behavior:

- raises `TypeError` because `cell_send` expects a callable update function

---

## Refs

Refs are synchronized mutable containers backed by a Python `threading.Condition`.

| Helper | Description |
| --- | --- |
| `ref()` | Create an unset ref |
| `ref(initial)` | Create a ref with an initial value |
| `ref_get(r)` | Read the current value; **blocks** until a value is set |
| `ref_set(r, value)` | Set the value and wake all waiters; returns `value` |
| `ref_is_set(r)` | Check whether the ref holds a value (non-blocking) |
| `ref_update(r, fn)` | Apply `fn` to the current value atomically; **blocks** until set |

### Real guarantees

- `ref_get` and `ref_update` on an unset ref **block the calling thread indefinitely** until another thread calls `ref_set`
- There is no timeout — a ref that is never set will block forever
- `ref_update` holds the internal lock while calling `fn`, so `fn` should be fast and must not re-enter the same ref
- `ref_set` wakes all blocked `ref_get` / `ref_update` waiters
- Reads and writes are serialized through a single condition variable per ref

### Minimal example

```genia
r = ref(0)
ref_update(r, (n) -> n + 1)
ref_get(r)
```

Result: `1`

### Edge case: blocking on unset ref

```genia
r = ref()
ref_is_set(r)
```

Result: `false`

Calling `ref_get(r)` here would block forever unless another thread calls `ref_set(r, value)`.

---

## Processes

Processes are fire-and-forget mailbox workers. Each process has a single handler function, a FIFO message queue, and one host daemon thread.

| Helper | Description |
| --- | --- |
| `spawn(handler)` | Create a process; `handler` is called once per message |
| `send(process, message)` | Enqueue a message (FIFO) |
| `process_alive?(process)` | Check whether the worker thread is alive |
| `process_failed?(process)` | Check whether the handler has thrown an exception |
| `process_error(process)` | Return `none` or `some(error_string)` |

### Real guarantees

- Messages are delivered in **FIFO order** (backed by Python `queue.Queue`)
- The handler is called **one message at a time** — no concurrent handler invocations per process
- If the handler throws an exception on any message:
  - The process enters **fail-stop** state
  - The error is cached as a string
  - The worker thread exits
  - Future `send` calls raise `RuntimeError`
  - `process_failed?` returns `true`
  - `process_error` returns `some(error_string)`
- There is **no restart mechanism** for processes (use cells/actors if you need restart)
- There is **no graceful shutdown** — the daemon thread runs until it fails or the program exits
- Handler exceptions that kill the thread do not propagate to the caller of `send`

### Minimal example: fire-and-forget logging

```genia
inbox = ref([])
p = spawn((msg) -> ref_update(inbox, (xs) -> append(xs, [msg])))
send(p, "hello")
send(p, "world")
```

After the mailbox drains, `ref_get(inbox)` returns `["hello", "world"]`.

### Failure example

```genia
p = spawn((_) -> 1 / 0)
send(p, "boom")
```

After the handler throws:

- `process_alive?(p)` returns `false`
- `process_failed?(p)` returns `true`
- `process_error(p)` returns `some("ZeroDivisionError: ...")`
- `send(p, "next")` raises `RuntimeError("Process has failed: ...")`

---

## Cells

Cells are serialized stateful workers with fail-stop error handling. They combine a ref (state) with a FIFO mailbox and one worker thread.

| Helper | Description |
| --- | --- |
| `cell(initial)` | Create a ready cell with initial state |
| `cell_with_state(ref)` | Create a cell backed by an existing ref |
| `cell_send(cell, update_fn)` | Enqueue `(state) -> new_state` for async processing |
| `cell_get(cell)` / `cell_state(cell)` | Read current state (raises if failed) |
| `cell_stop(cell)` | Drain mailbox then stop the worker |
| `restart_cell(cell, new_state)` | Clear failure/stop, reset state, relaunch worker |
| `cell_status(cell)` | Return `"ready"`, `"failed"`, or `"stopped"` |
| `cell_alive?(cell)` | Check whether the worker thread is alive |
| `cell_failed?(cell)` | Check whether the cell has failed |
| `cell_error(cell)` | Return `none` or `some(error_string)` |

### Real guarantees

- Updates are processed **one at a time in FIFO order**
- Each update function receives the current state and must return the new state
- **Successful updates** replace state immediately
- **Failed updates** (handler throws):
  - Do not change the state — last successful state is preserved
  - Put the cell in failed state with a cached error string
  - All subsequent queued updates for the current generation are discarded
  - Future `cell_send` and `cell_get` raise `RuntimeError`
- **Nested `cell_send`** calls made during an update are staged and committed only if that update succeeds
- **`cell_stop`** sets stopped state immediately, then sends a sentinel that the worker drains to before exiting
  - Queued updates already in the mailbox are processed before the worker exits
  - `cell_get` still returns the last state after stop
  - `cell_send` raises after stop
- **`restart_cell(cell, new_state)`**:
  - Increments a generation counter (discards stale queued updates)
  - Clears failure/stopped state and error
  - Sets state to `new_state`
  - Relaunches the worker thread if it has exited
  - Works after both failure and stop
- **`cell_stop` on a stopped or failed cell is a no-op**

### Failure and restart example

```genia
a = cell(1)
cell_send(a, (x) -> x + 1)
cell_send(a, (_) -> 1 / 0)
```

After the second update fails:

- `cell_get(a)` raises `RuntimeError`
- `cell_failed?(a)` returns `true`
- `cell_error(a)` returns `some("ZeroDivisionError: ...")`

Restart:

```genia
restart_cell(a, 10)
cell_send(a, (x) -> x + 1)
```

After restart, `cell_get(a)` returns `11`.

---

## Actors

Actors are a **thin prelude layer over cells**. An actor is a map with `_cell` and `_handler` keys — not a BEAM-style actor, not a language primitive.

| Helper | Description |
| --- | --- |
| `actor(initial_state, handler)` | Create an actor backed by a cell |
| `actor_send(actor, msg)` | Fire-and-forget message processing |
| `actor_call(actor, msg)` | Send a message and **block** for the reply |
| `actor_alive?(actor)` | Check whether the worker thread is alive |
| `actor_stop(actor)` | Drain mailbox then stop |
| `actor_restart(actor, new_state)` | Restart with new state (preserves handler) |
| `actor_state(actor)` | Read current state without sending a message |
| `actor_failed?(actor)` | Check whether the actor has failed |
| `actor_error(actor)` | Return `none` or `some(error_string)` |
| `actor_status(actor)` | Return `"ready"`, `"failed"`, or `"stopped"` |

### Handler shape

```genia
handler(state, msg, ctx) -> effect
```

### Effect protocol

| Effect | Meaning |
| --- | --- |
| `["ok", new_state]` | Update state only |
| `["reply", new_state, response]` | Update state and deliver `response` to caller |
| `["stop", reason, new_state]` | Commit final state and stop the actor |

- All three shapes are accepted by both `actor_send` and `actor_call`
- For `actor_send`, any response in `["reply", ...]` is discarded
- For `actor_call` with `["ok", new_state]`, the reply is `new_state`
- For `actor_call` with `["stop", ...]`, the reply is `none("actor-stopped")`
- Any other return shape marks the actor as failed with a clear error

### Real guarantees

- Messages are processed **one at a time in FIFO order** (inherited from cell)
- `actor_call` creates a one-shot reply ref and **blocks** on `ref_get` until the handler finishes
  - If the handler throws, the reply is `none("actor-error")` — `actor_call` does not block forever
  - If the handler returns `["stop", ...]`, the reply is `none("actor-stopped")`
- `ctx` is `{}` for `actor_send`; `{reply_to: <ref>}` for `actor_call`
- Failure semantics are inherited from the backing cell:
  - Handler exceptions or invalid effect shapes mark the actor as failed
  - Subsequent sends raise `RuntimeError`
- `actor_restart` clears failure and relaunches the worker; the handler is preserved
- `actor_stop` drains the mailbox before the worker exits

### Minimal example: fire-and-forget

```genia
handler(state, msg, _ctx) = ["ok", state + msg]
a = actor(0, handler)
actor_send(a, 5)
actor_send(a, 10)
```

After both messages drain, `actor_state(a)` returns `15`.

### Synchronous request-reply

```genia
handler(state, msg, _ctx) = ["reply", state + msg, state + msg]
a = actor(0, handler)
actor_call(a, 5)
```

Returns `5`. Subsequent `actor_call(a, 10)` returns `15`.

### actor_call with `["ok", new_state]`

```genia
handler(state, msg, _ctx) = ["ok", state + msg]
a = actor(0, handler)
actor_call(a, 3)
```

Returns `3`. The same handler works with both `actor_send` and `actor_call`.

### Handler-initiated stop

```genia
handler(state, msg, _ctx) = ["stop", "done", state + msg]
a = actor(0, handler)
actor_send(a, 42)
```

After the worker exits:

- `actor_status(a)` returns `"stopped"`
- Subsequent `actor_send` raises `RuntimeError`

When `actor_call` receives a `["stop", ...]` effect, the reply is `none("actor-stopped")`.

### Failure: invalid effect shape

```genia
bad_handler(state, msg, _ctx) = "not-a-valid-effect"
a = actor(0, bad_handler)
actor_send(a, 1)
```

The actor enters failed state with an error showing the received value and expected shapes.

### actor_call failure

```genia
failing(state, msg, _ctx) = 1 / 0
a = actor(0, failing)
actor_call(a, 1)
```

Returns `none("actor-error")` instead of blocking forever.

### Current actor limitations

- Actors are a thin prelude layer over cells, not a language primitive
- No selective receive
- No timeouts in message receive
- No deterministic scheduling — behavior depends on host-thread timing
- No supervision, links, or monitors
- `ctx` is a plain map, not a capability envelope
- The ants terminal UI actor mode uses an explicit blocking tick loop, not a scheduler or event loop
- The ants browser viewer uses ordinary HTTP requests and JSON snapshots

---

## Canonical Concurrency Patterns

These patterns use only what is actually implemented today.

### Pattern 1: Authoritative world ref + coordinator

Use a single ref or cell as the authoritative state holder. All updates go through one serialization point.

```genia
world = cell({score: 0, items: []})
cell_send(world, (w) -> map_put(w, "score", w("score") + 10))
cell_get(world)
```

This is the simplest safe pattern for shared mutable state.

---

## Simulation Pattern: Pure Tick First

For simulations, the canonical Genia pattern today is:

1. model the world as an ordinary value
2. write deterministic `step(world) -> next_world` logic
3. keep seeded RNG state inside that world when randomness matters
4. render from snapshots of the world
5. add refs/cells/actors only as an outer coordination layer

The ants demos use this split:

- `examples/ants.genia` is the pure simulation core
- `examples/ants_terminal.genia` is the blocking terminal render/timing shell
- `examples/ants_actor.genia` is the optional actor/coordinator comparison
- `examples/ants_web.genia` is an HTTP/browser snapshot viewer

Minimal shape:

```genia
import ants

world0 = ants/new_world(7, 3, 7, 7)
world1 = ants/step(world0)
ants/world_tick(world1)
```

Expected behavior:

- the world value is replaced by a new world value
- RNG state is threaded through the world
- same seed plus same config gives the same progression for the same mode
- no scheduler, transaction system, or hidden mutable simulation state is introduced

### Rendering shell

Rendering should consume a snapshot and produce output. In the terminal ants demo,
`draw_frame_config(world, steps_left, config)` reads the world and renders rows;
`simulate_session(...)` owns the blocking `sleep(...)` delay and repeated stepping.

This keeps simulation behavior testable without terminal timing.

### Coordinator layer

The actor ants demo keeps a single coordinator actor as the authoritative world owner.
Ant workers request sense data and submit move intents, but the coordinator serializes
the actual world update order.

This is a comparison layer over the pure model, not a new concurrency guarantee.

### Browser snapshot layer

The browser ants demo keeps one current session in a server-side `ref` and serves JSON
snapshots. `POST /step` advances one tick and returns a fresh snapshot.

The browser run/pause control is repeated HTTP requests from JavaScript. It is not a
browser-native Genia runtime, WebSocket loop, or language scheduler.

### Pattern 2: Fire-and-forget process messaging

Use processes for side effects that don't need acknowledgment.

```genia
log_ref = ref([])
logger = spawn((msg) -> ref_update(log_ref, (xs) -> append(xs, [msg])))
send(logger, "started")
send(logger, "finished")
```

After the mailbox drains, `ref_get(log_ref)` returns `["started", "finished"]`.

### Pattern 3: Request-reply via actors

Use `actor_call` when you need a response from the state owner.

```genia
handler(state, ["get"], _ctx) = ["reply", state, state]
handler(state, ["inc", n], _ctx) = ["reply", state + n, state + n]

counter = actor(0, handler)
actor_call(counter, ["inc", 5])
actor_call(counter, ["get"])
```

Returns `5` then `5`.

### Pattern 4: Fail-stop cell with recovery

```genia
a = cell(0)
cell_send(a, (x) -> x + 1)
cell_send(a, (_) -> 1 / 0)
```

After failure: `cell_failed?(a)` is `true`. Recover with:

```genia
restart_cell(a, 0)
cell_send(a, (x) -> x + 100)
```

After restart, `cell_get(a)` returns `100`.

---

## Actor demo: ants colony (`examples/ants_actor.genia`)

This demo runs the same colony simulation from `examples/ants.genia` using the actor model.
A coordinator actor owns the authoritative world state.
Ant workers request sense data and submit move intents through `actor_call`.
The terminal developer UI can select this execution structure with `--mode actor`.
The browser viewer can select it with reset config/UI mode `actor`.

Architecture:

- **Coordinator**: single actor holding the world map; processes `["sense", ant_id]`, `["move_intent", ant_id, move]`, `["tick"]`, `["snapshot"]`, and `["stop"]` messages
- **Tick loop**: explicit coordinator-driven ant ordering for deterministic reproducibility
- **Reuse**: imports and calls the pure scoring/movement logic from `ants.genia` via `import ants`

This demo does **not** add new language syntax, does **not** introduce a scheduler, and does **not** require selective receive or timeouts.

---

## Implementation status

### ✅ Implemented

- prelude-backed public ref/process/cell/actor helper surface with `help(...)` visibility
- host-backed refs with blocking get/update semantics
- host-backed process handles with FIFO mailbox and fail-stop error handling
- serialized handler execution per process and per cell
- fail-stop cell abstraction with cached error state
- restart semantics via `restart_cell`
- graceful stop via `cell_stop` (drains mailbox before exit)
- actor helpers as a thin prelude layer over cells
- standardized actor handler effect protocol: `["ok", ...]`, `["reply", ...]`, `["stop", ...]`
- clear error messages for invalid handler return shapes
- `actor_call` blocks on a one-shot reply ref (does not block forever on handler failure)
- nested `cell_send` staged and committed only on success

### ⚠️ Partial

- all timing depends on host-thread scheduling — no deterministic ordering across concurrent actors
- restart discards queued pre-restart updates in this phase instead of draining them
- cell and process errors are exposed as cached error strings rather than structured language error values
- actors are a prelude convention, not a language primitive — internal cell state is accessible through the actor map
- `ref_get` / `ref_update` on an unset ref blocks the calling thread indefinitely

### ❌ Not implemented

- language-level scheduler
- selective receive
- timeouts in message receive
- deterministic scheduling
- supervision / links / monitors
- backpressure and cancellation
- process restart (use cells/actors for restartable workers)

---

## Concurrency invariants (canonical)

These are the exact guarantees the current Python host provides.
They are locked by tests in `tests/test_invariant_concurrency.py`.

### What we guarantee

| Primitive | Guarantee |
|-----------|-----------|
| **Ref** | `ref_set` makes a value visible to all threads; `ref_update` serializes through a lock; `ref_get` blocks until a value is set |
| **Process** | Messages are handled in FIFO order; handlers run one at a time (serialized); a handler exception causes permanent fail-stop |
| **Cell** | Updates are applied in FIFO order; failure preserves the last successfully committed state; `restart_cell` clears the failure and discards stale queued updates; nested `cell_send` rolls back on failure |
| **Actor** | Messages are ordered (cells underneath); `actor_call` blocks until a reply arrives; `["ok", state]` returns state to caller; `["stop", state]` rejects subsequent sends; invalid handler return marks the actor failed |

### What we do NOT guarantee

- **No cross-actor ordering.** Two actors that each send to a third provide no interleaving guarantee.
- **No timeout on `ref_get`.** An unset ref blocks the calling thread indefinitely.
- **No deterministic scheduling.** Thread scheduling is host-dependent; tests must not rely on precise timing.
- **No supervision.** A failed process/cell stays failed until explicit `restart_cell`. There are no links, monitors, or supervisors.
- **No selective receive.** Every message is handled in arrival order. There is no pattern-based mailbox scan.
- **No backpressure.** Senders are never blocked by a slow consumer.
