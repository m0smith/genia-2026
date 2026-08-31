# `json_schema`

**Category:** `json` &nbsp;|&nbsp; **Arity:** 1

```genia
json_schema(schema)
```

Compile the supported JSON Schema structural subset into a Template.

## Arguments
- `schema`: `json`-represented schema map

## Returns
- `some(template, context)` on success
- normalized schema `err(reason, context)` on validation failure

---

_Source: `std/prelude/json.genia` &middot; category `json`. Generated from canonical metadata by `tools/gen_function_docs.py`._

[<- Back to the Function Reference](../index.md)
