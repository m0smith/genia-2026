# `diagnostic_field`

**Category:** `validation` &nbsp;|&nbsp; **Arity:** 1

```genia
diagnostic_field(diagnostic)
```

Return a diagnostic map's field.

## Arguments

* `diagnostic`: map that may contain `field`

## Returns

* the stored `field`, or missing-key absence when the key is absent

## Errors

* raises when `diagnostic` is not a map

---

_Source: `std/prelude/validation.genia` &middot; category `validation`. Generated from canonical metadata by `tools/gen_function_docs.py`._

[<- Back to the Function Reference](../index.md)
