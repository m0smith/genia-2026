# `json_stringify`

**Category:** `json` &nbsp;|&nbsp; **Arity:** 1

```genia
json_stringify(value)
```

Render a Genia value as deterministic pretty JSON.

Object keys are sorted and output uses 2-space indentation.
Returns `none("json-stringify-error", context)` when the value is not JSON-compatible.

---

_Source: `std/prelude/json.genia` &middot; category `json`. Generated from canonical metadata by `tools/gen_function_docs.py`._

[<- Back to the Function Reference](../index.md)
