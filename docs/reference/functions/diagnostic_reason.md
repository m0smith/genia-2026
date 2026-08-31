# `diagnostic_reason`

**Category:** `validation` &nbsp;|&nbsp; **Arity:** 1

```genia
diagnostic_reason(diagnostic)
```

Return a diagnostic map's reason.

## Arguments

* `diagnostic`: map that may contain `reason`

## Returns

* the stored `reason`, or missing-key absence when the key is absent

## Errors

* raises when `diagnostic` is not a map

---

_Source: `std/prelude/validation.genia` &middot; category `validation`. Generated from `@doc`/`@meta` by `tools/gen_function_docs.py`._

[<- Back to the Function Reference](../index.md)
