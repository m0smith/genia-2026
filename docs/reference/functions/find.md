# `find`

**Category:** `string` &nbsp;|&nbsp; **Arity:** 2

```genia
find(value, needle)
```

Find the first index of `needle` within `value`.

## Arguments
- `value`: string to search
- `needle`: substring to locate

## Returns
- `some(index)` with the zero-based index of the first match
- `none("not-found", ...)` when `needle` does not occur in `value`

---

_Source: `std/prelude/string.genia` &middot; category `string`. Generated from `@doc`/`@meta` by `tools/gen_function_docs.py`._

[<- Back to the Function Reference](../index.md)
