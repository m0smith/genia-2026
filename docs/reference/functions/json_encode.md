# `json_encode`

**Category:** `json` &nbsp;|&nbsp; **Arity:** 1

```genia
json_encode(value)
```

Encode a supported ordinary or `json`-represented value as deterministic JSON.

## Arguments
- `value`: supported ordinary or `json`-represented value

## Returns
- `some(text, context)` on success
- `err(reason, context)` for unsupported or out-of-contract values

---

_Source: `std/prelude/json.genia` &middot; category `json`. Generated from canonical metadata by `tools/gen_function_docs.py`._

[<- Back to the Function Reference](../index.md)
