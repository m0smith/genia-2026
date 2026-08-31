# `json_decode`

**Category:** `json` &nbsp;|&nbsp; **Arity:** 1

```genia
json_decode(value)
```

Decode JSON text or UTF-8 bytes through the portable JSON representation boundary.

## Arguments
- `value`: JSON text or UTF-8 bytes

## Returns
- `some(represented_value, context)` on success
- `err(reason, context)` for recoverable JSON data failures

## Errors
- raises a type error when `value` is neither text nor bytes

---

_Source: `std/prelude/json.genia` &middot; category `json`. Generated from canonical metadata by `tools/gen_function_docs.py`._

[<- Back to the Function Reference](../index.md)
