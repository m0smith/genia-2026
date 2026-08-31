# `stream_take`

**Category:** `stream` &nbsp;|&nbsp; **Arity:** 2

```genia
stream_take(n, s)
```

Materialize the first `n` stream elements as an ordinary list.

## Arguments
- `n`: number of items to take
- `s`: stream value

## Returns
- list of the first `n` elements, or fewer if the stream ends at `nil`

---

_Source: `std/prelude/stream.genia` &middot; category `stream`. Generated from `@doc`/`@meta` by `tools/gen_function_docs.py`._

[<- Back to the Function Reference](../index.md)
