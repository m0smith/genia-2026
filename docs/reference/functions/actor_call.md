# `actor_call`

**Category:** `actor` &nbsp;|&nbsp; **Arity:** 2

```genia
actor_call(a, msg)
```

Send a message and wait for a reply (synchronous request-reply).

The handler receives `ctx` with a `reply_to` ref.
Return `["reply", new_state, response]` to deliver a response.
Return `["ok", new_state]` to reply with the new state as the response.
Return `["stop", reason, new_state]` to stop the actor; the reply is `none("actor-stopped")`.

If the handler fails, `actor_call` returns `none("actor-error")` and the
actor enters failed state.

## Arguments

- `a` — the actor
- `msg` — the message value

## Returns

The response value from the handler's `["reply", new_state, response]` effect,
or the new state from `["ok", new_state]`.

---

_Source: `std/prelude/actor.genia` &middot; category `actor`. Generated from `@doc`/`@meta` by `tools/gen_function_docs.py`._

[<- Back to the Function Reference](../index.md)
