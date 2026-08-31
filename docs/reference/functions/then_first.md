# `then_first`

**Category:** `option` &nbsp;|&nbsp; **Arity:** 1

```genia
then_first(target)
```

Take the first element of a list target within a pipeline, as an Option.

## Arguments
- `target`: a list, `some(list)`, or `none(...)`

## Returns
- `some(value)` for the first element of a non-empty list
- `none("empty-list")` when the list is empty
- the incoming `none(...)` unchanged when `target` is already `none(...)`

## Errors
- raises when `target` is not a list, `some(list)`, or `none(...)`

---

_Source: `std/prelude/option.genia` &middot; category `option`. Generated from `@doc`/`@meta` by `tools/gen_function_docs.py`._

[<- Back to the Function Reference](../index.md)
