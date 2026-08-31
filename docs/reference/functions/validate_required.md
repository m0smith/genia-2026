# `validate_required`

**Category:** `validation` &nbsp;|&nbsp; **Arity:** 2

```genia
validate_required(field, record)
```

Require a record field and return an Outcome.

## Arguments

* `field`: flat field name or simple dot-joined nested field path to require
* `record`: map record that may include `row`

## Returns

* `some(record)` when the field is present
* `err("missing required field", context)` when the field is absent

---

_Source: `std/prelude/validation.genia` &middot; category `validation`. Generated from `@doc`/`@meta` by `tools/gen_function_docs.py`._

[<- Back to the Function Reference](../index.md)
