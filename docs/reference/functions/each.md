# `each`

**Category:** `flow` &nbsp;|&nbsp; **Arity:** 2

```genia
each(fn, source)
```

Run `fn` for each item of a list or Flow, passing the original items through.

## Arguments
- `fn`: function invoked for each item, for its side effects
- `source`: a list or Flow to traverse

## Returns
- a lazy Flow stage that yields the original items unchanged when consumed

## Notes
- `fn` runs for an item only when that item is consumed downstream
- lazy and pull-based

---

_Source: `std/prelude/flow.genia` &middot; category `flow`. Generated from canonical metadata by `tools/gen_function_docs.py`._

[<- Back to the Function Reference](../index.md)
