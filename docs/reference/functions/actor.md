# `actor`

**Category:** `actor` &nbsp;|&nbsp; **Arity:** 2

```genia
actor(initial_state, handler)
```

Create an actor with initial state and a message handler.

The handler shape is `handler(state, msg, ctx) -> effect`.
The actor processes messages one at a time via a backing cell.

## Arguments

- `initial_state` — the starting state value
- `handler` — a function `(state, msg, ctx) -> effect`

## Returns

An actor value (a map with internal `_cell` and `_handler` keys).

## Notes

Supported effect shapes:
- `["ok", new_state]` — update state only
- `["reply", new_state, response]` — update state and deliver response
- `["stop", reason, new_state]` — commit final state and stop the actor

Handler failures or invalid return shapes mark the actor as failed.

---

_Source: `std/prelude/actor.genia` &middot; category `actor`. Generated from `@doc`/`@meta` by `tools/gen_function_docs.py`._

[<- Back to the Function Reference](../index.md)
