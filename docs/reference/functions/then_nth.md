# `then_nth`

**Category:** `option` &nbsp;|&nbsp; **Arity:** 2

```genia
then_nth(index, target)
```

Take the element at `index` of a list target within a pipeline, as an Option.

Accepts its arguments in either order so it composes in `|>` chains.

## Arguments
- `index`: zero-based integer position to read
- `target`: a list, `some(list)`, or `none(...)`

## Returns
- `some(value)` for the element at `index`
- `none("index-out-of-bounds", ...)` with `index` and `length` in context when out of range
- the incoming `none(...)` unchanged when `target` is already `none(...)`

## Errors
- raises when `index` is not an integer
- raises when `target` is not a list, `some(list)`, or `none(...)`

---

_Source: `std/prelude/option.genia` &middot; category `option`. Generated from `@doc`/`@meta` by `tools/gen_function_docs.py`._

[<- Back to the Function Reference](../index.md)
