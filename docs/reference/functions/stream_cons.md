# `stream_cons`

**Category:** `stream` &nbsp;|&nbsp; **Arity:** 2

```genia
stream_cons(head, tail_fn)
```

Construct a stream node from a head value and delayed tail function.

## Arguments
- `head`: stream head value
- `tail_fn`: zero-argument function returning the next stream

## Returns
- pair whose tail is a delayed promise

---

_Source: `std/prelude/stream.genia` &middot; category `stream`. Generated from canonical metadata by `tools/gen_function_docs.py`._

[<- Back to the Function Reference](../index.md)
