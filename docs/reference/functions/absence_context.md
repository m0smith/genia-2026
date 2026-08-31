# `absence_context`

**Category:** `option` &nbsp;|&nbsp; **Arity:** 1

```genia
absence_context(opt)
```

Read the optional context metadata of a structured `none(...)` value.

## Arguments
- `opt`: a `none(...)` value to inspect

## Returns
- `some(context)` when the none value carries context metadata
- `none(...)` when the none value has no context

## Errors
- raises when `opt` is not a `none(...)` value

---

_Source: `std/prelude/option.genia` &middot; category `option`. Generated from `@doc`/`@meta` by `tools/gen_function_docs.py`._

[<- Back to the Function Reference](../index.md)
