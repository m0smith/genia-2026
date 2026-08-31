# `then_find`

**Category:** `option` &nbsp;|&nbsp; **Arity:** 2

```genia
then_find(needle, target)
```

Find `needle` in a string target within a pipeline, returning its index as an Option.

Accepts its arguments in either order so it composes in `|>` chains.

## Arguments
- `needle`: the substring to search for
- `target`: a string, `some(string)`, or `none(...)`

## Returns
- `some(index)` with the index where `needle` first occurs
- `none("not-found", ...)` with the needle in context when it does not occur
- the incoming `none(...)` unchanged when `target` is already `none(...)`

## Errors
- raises when `needle` is not a string
- raises when `target` is not a string, `some(string)`, or `none(...)`

---

_Source: `std/prelude/option.genia` &middot; category `option`. Generated from `@doc`/`@meta` by `tools/gen_function_docs.py`._

[<- Back to the Function Reference](../index.md)
