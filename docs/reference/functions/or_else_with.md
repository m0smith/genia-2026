# `or_else_with`

**Category:** `option` &nbsp;|&nbsp; **Arity:** 2

```genia
or_else_with(opt, thunk)
```

Unwrap `some(...)`, calling `thunk()` for `none(...)`.

Accepts the Option and thunk in either order so it can wrap a whole `|>`
pipeline result at the recovery point.

## Arguments
- `opt`: the Option to unwrap
- `thunk`: zero-argument function called only when `opt` is `none(...)`

## Returns
- the wrapped value when `opt` is `some(value)`
- the result of `thunk()` when `opt` is `none(...)`

## Errors
- raises when `opt` is neither `some(...)` nor `none(...)`

---

_Source: `std/prelude/option.genia` &middot; category `option`. Generated from `@doc`/`@meta` by `tools/gen_function_docs.py`._

[<- Back to the Function Reference](../index.md)
