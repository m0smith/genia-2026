# `parse_int`

**Category:** `string` &nbsp;|&nbsp; **Arity:** 1, 2

```genia
parse_int(value)
parse_int(value, base)
```

Parse an integer from a string, with optional explicit base.

Returns `some(int)` on success and `none("parse-error", context)` for invalid integer text.

---

_Source: `std/prelude/string.genia` &middot; category `string`. Generated from `@doc`/`@meta` by `tools/gen_function_docs.py`._

[<- Back to the Function Reference](../index.md)
