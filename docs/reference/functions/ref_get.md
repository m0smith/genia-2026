# `ref_get`

**Category:** `ref` &nbsp;|&nbsp; **Arity:** 1

```genia
ref_get(ref_value)
```

Read the current value from a ref.

## Arguments
- `ref_value`: synchronized ref

## Returns
- current stored value

## Notes
- reading an unset ref blocks until a value is set

---

_Source: `std/prelude/ref.genia` &middot; category `ref`. Generated from canonical metadata by `tools/gen_function_docs.py`._

[<- Back to the Function Reference](../index.md)
