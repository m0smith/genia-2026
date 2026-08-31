# `diagnostic_error`

**Category:** `validation` &nbsp;|&nbsp; **Arity:** 4

```genia
diagnostic_error(index, field, reason, context)
```

Create a field/index-aware error diagnostic map.

## Arguments

* `index`: caller-provided source position metadata
* `field`: caller-provided field metadata
* `reason`: caller-provided failure reason
* `context`: caller-provided diagnostic context

## Returns

* an error diagnostic map with `index`, `field`, `kind`, `reason`, and `context`

---

_Source: `std/prelude/validation.genia` &middot; category `validation`. Generated from `@doc`/`@meta` by `tools/gen_function_docs.py`._

[<- Back to the Function Reference](../index.md)
