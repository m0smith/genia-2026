# `validate_field`

**Category:** `validation` &nbsp;|&nbsp; **Arity:** 4

```genia
validate_field(field, predicate, expected, record)
```

Validate a record field with a predicate and return an Outcome.

## Arguments

* `field`: flat field name or simple dot-joined nested field path to validate
* `predicate`: callable checked with the field value
* `expected`: description of the expected condition
* `record`: map record that may include `row`

## Returns

* `some(record)` when the field is present and the predicate returns `true`
* `err("missing required field", context)` when the field is absent
* `err("invalid field", context)` when the predicate does not return `true`

## Errors

* raises when `predicate` is not callable

---

_Source: `std/prelude/validation.genia` &middot; category `validation`. Generated from canonical metadata by `tools/gen_function_docs.py`._

[<- Back to the Function Reference](../index.md)
