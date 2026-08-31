# `unwrap_or`

**Category:** `option` &nbsp;|&nbsp; **Arity:** 2

```genia
unwrap_or(default, opt)
```

Unwrap `some(...)`, returning `default` for `none(...)`.

The canonical recovery point for Option-aware pipelines; it unwraps only here.

## Arguments
- `default`: value returned when `opt` is `none(...)`
- `opt`: the Option to unwrap

## Returns
- the wrapped value when `opt` is `some(value)`
- `default` when `opt` is `none(...)`

## Errors
- raises when `opt` is neither `some(...)` nor `none(...)`

---

_Source: `std/prelude/option.genia` &middot; category `option`. Generated from canonical metadata by `tools/gen_function_docs.py`._

[<- Back to the Function Reference](../index.md)
