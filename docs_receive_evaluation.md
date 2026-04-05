# `receive()` Evaluation (March 29, 2026)

## Recommendation
Do **not** add a `receive()` primitive yet. Keep the current `spawn(handler) + send(process, message)` model for now.

## Rationale

### 1. The runtime already implements an implicit receive loop
Today, `GeniaProcess` owns a mailbox queue and its worker thread runs:
- `message = mailbox.get()`
- `handler(message)`
- repeat forever

So the actor receive loop already exists in the host runtime. A user-facing `receive()` would duplicate that mechanism by moving part of the loop into Genia code, not removing it.

### 2. A real `receive()` would require new runtime surface area
To expose `receive()` safely, the runtime would need at least:
- process/thread-local "current mailbox" context
- behavior outside process threads (error vs nil vs block)
- clear blocking semantics and interrupt behavior
- likely timeout support soon after, to avoid deadlock-prone libraries

That is additional complexity in core runtime semantics compared with the current single-message handler contract.

### 3. Current libraries already cover the main stateful-worker use case
The prelude `cell` abstraction is already thin and effective:
- cell state is held in a `ref`
- worker is `spawn((update) -> ref_update(state, update))`
- `cell_send` and `cell_get` compose well

This means common serialized-state workflows are already solved without a new primitive.

### 4. `receive()` is more compelling after richer mailbox features exist
`receive()` becomes much more valuable when Genia can do things like:
- selective receive (pattern-based mailbox scanning)
- timeout/cancel semantics
- system messages/supervision patterns

Without those, `receive()` mainly shifts ergonomics while increasing core complexity.

## Rough implementation sketch (if revisited later)
If later prioritized for library ergonomics, use the smallest possible scope:

1. **Introduce thread-local current mailbox** in `GeniaProcess` worker entry.
2. **Add builtin `receive()`** with arity 0:
   - inside a process worker: block on mailbox `get()` and return message
   - outside a process worker: raise `TypeError("receive expected to be called from a process")`
3. **Keep `spawn(handler)` unchanged** for backward compatibility.
4. **Optionally add `spawn_loop(fn0)` in stdlib only** (not runtime):
   - `spawn_loop(loop_fn)` spawns a zero-arg thunk that repeatedly calls `loop_fn(receive())` via recursion/TCO.
5. **Add tests** for:
   - in-process blocking receive
   - FIFO delivery with receive loop
   - outside-process error behavior

This keeps the first version localized while avoiding immediate redesign of existing process APIs.
