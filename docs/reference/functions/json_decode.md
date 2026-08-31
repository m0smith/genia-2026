# `json_decode`

**Category:** `json` &nbsp;|&nbsp; **Arity:** 1

```genia
json_decode(value)
```

Decode JSON text or UTF-8 bytes through the portable JSON representation boundary.

Returns `some(represented_value, context)` on success.
Returns `err(reason, context)` for recoverable JSON data failures.

---

_Source: `std/prelude/json.genia` &middot; category `json`. Generated from `@doc`/`@meta` by `tools/gen_function_docs.py`._

[<- Back to the Function Reference](../index.md)
