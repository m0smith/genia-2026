# `actor_send`

**Category:** `actor` &nbsp;|&nbsp; **Arity:** 2

```genia
actor_send(a, msg)
```

Send a message to an actor for asynchronous processing.

The message is enqueued and processed by the actor's handler.
The handler may return `["ok", new_state]`, `["reply", new_state, response]`,
or `["stop", reason, new_state]`.
For fire-and-forget sends, any reply value is discarded.

## Arguments

- `a` — the actor
- `msg` — the message value

## Errors

Raises if the actor has already failed or stopped.

---

_Source: `std/prelude/actor.genia` &middot; category `actor`. Generated from canonical metadata by `tools/gen_function_docs.py`._

[<- Back to the Function Reference](../index.md)
