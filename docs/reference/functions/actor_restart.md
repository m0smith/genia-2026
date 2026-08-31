# `actor_restart`

**Category:** `actor` &nbsp;|&nbsp; **Arity:** 2

```genia
actor_restart(a, new_state)
```

Restart a failed or stopped actor with a new initial state.

Clears failure, resets state, and resumes message processing.
Works after both failure and `actor_stop`.
The handler is preserved.

## Arguments

- `a` — the actor
- `new_state` — the new initial state value

## Returns

The actor (unchanged reference).

---

_Source: `std/prelude/actor.genia` &middot; category `actor`. Generated from canonical metadata by `tools/gen_function_docs.py`._

[<- Back to the Function Reference](../index.md)
