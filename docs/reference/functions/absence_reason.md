# `absence_reason`

**Category:** `option` &nbsp;|&nbsp; **Arity:** 1

```genia
absence_reason(opt)
```

Read the reason label of a structured `none(...)` value.

## Arguments
- `opt`: a `none(...)` value to inspect

## Returns
- `some(reason)` wrapping the none value's reason string

## Errors
- raises when `opt` is not a `none(...)` value

---

_Source: `std/prelude/option.genia` &middot; category `option`. Generated from canonical metadata by `tools/gen_function_docs.py`._

[<- Back to the Function Reference](../index.md)
