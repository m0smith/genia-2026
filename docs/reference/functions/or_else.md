# `or_else`

**Category:** `option` &nbsp;|&nbsp; **Arity:** 2

```genia
or_else(opt, fallback)
```

Unwrap `some(...)`, falling back to `fallback` for `none(...)`.

Accepts the Option and fallback in either order so it can wrap a whole `|>`
pipeline result at the recovery point.

## Arguments
- `opt`: the Option to unwrap
- `fallback`: value returned when `opt` is `none(...)`

## Returns
- the wrapped value when `opt` is `some(value)`
- `fallback` when `opt` is `none(...)`

## Errors
- raises when `opt` is neither `some(...)` nor `none(...)`

---

_Source: `std/prelude/option.genia` &middot; category `option`. Generated from canonical metadata by `tools/gen_function_docs.py`._

[<- Back to the Function Reference](../index.md)
