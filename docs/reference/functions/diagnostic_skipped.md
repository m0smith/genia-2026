# `diagnostic_skipped`

**Category:** `validation` &nbsp;|&nbsp; **Arity:** 4

```genia
diagnostic_skipped(index, field, reason, context)
```

Create a field/index-aware skipped diagnostic map.

## Arguments

* `index`: caller-provided source position metadata
* `field`: caller-provided field metadata
* `reason`: caller-provided skip reason
* `context`: caller-provided diagnostic context

## Returns

* a skipped diagnostic map with `index`, `field`, `kind`, `reason`, and `context`

---

_Source: `std/prelude/validation.genia` &middot; category `validation`. Generated from `@doc`/`@meta` by `tools/gen_function_docs.py`._

[<- Back to the Function Reference](../index.md)
