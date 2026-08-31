# `get`

**Category:** `option` &nbsp;|&nbsp; **Arity:** 2

```genia
get(key, target)
```

Look up `key` in a map target, returning an absence-aware Option.

Unwraps a `some(map)` target and propagates a `none(...)` target unchanged, so
it composes over nested Option results.

## Arguments
- `key`: the map key to look up
- `target`: a map, `some(map)`, or `none(...)`

## Returns
- `some(value)` when `key` is present in the map
- `none("missing-key", ...)` with the key in context when `key` is absent
- the incoming `none(...)` unchanged when `target` is already `none(...)`

## Errors
- raises when `target` is not a map, `some(map)`, or `none(...)`

---

_Source: `std/prelude/option.genia` &middot; category `option`. Generated from canonical metadata by `tools/gen_function_docs.py`._

[<- Back to the Function Reference](../index.md)
