# `actor_stop`

**Category:** `actor` &nbsp;|&nbsp; **Arity:** 1

```genia
actor_stop(a)
```

Gracefully stop an actor after draining its mailbox.

Queued messages are processed before the worker exits.
After stop, `actor_send` and `actor_call` raise.
`cell_get` on the backing cell still returns the last state.

---

_Source: `std/prelude/actor.genia` &middot; category `actor`. Generated from canonical metadata by `tools/gen_function_docs.py`._

[<- Back to the Function Reference](../index.md)
