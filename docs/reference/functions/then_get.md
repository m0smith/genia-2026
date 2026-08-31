# `then_get`

**Category:** `option` &nbsp;|&nbsp; **Arity:** 2

```genia
then_get(key, target)
```

Look up `key` in a map target within a pipeline, returning an Option.

Accepts its arguments in either order so it composes in `|>` chains where the
target arrives as the piped value.

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
