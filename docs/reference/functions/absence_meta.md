# `absence_meta`

**Category:** `option` &nbsp;|&nbsp; **Arity:** 1

```genia
absence_meta(opt)
```

Read the full metadata of a structured `none(...)` value as a map.

## Arguments
- `opt`: a `none(...)` value to inspect

## Returns
- `some(map)` whose map always includes `reason`, and includes `context` when present

## Errors
- raises when `opt` is not a `none(...)` value

---

_Source: `std/prelude/option.genia` &middot; category `option`. Generated from canonical metadata by `tools/gen_function_docs.py`._

[<- Back to the Function Reference](../index.md)
