# `validate_optional`

**Category:** `validation` &nbsp;|&nbsp; **Arity:** 2, 3

```genia
validate_optional(field, record)
validate_optional(field, record, validator)
```

Validate an optional record field and return an Outcome.

## Arguments

* `field`: optional flat field name or simple dot-joined nested field path to validate
* `record`: map record that may include the field
* `validator`: optional callable checked with the field value

## Returns

* `none({field: field, reason: quote(missing_optional_field)})` when the field is absent
* `some(value, {field: field})` when the field is present and no validator is supplied
* the validator's `some(...)` unchanged when supplied
* the validator's `err(...)` with the same meaning and full nested `field` context when applicable
* `err(quote(optional_field_validator_returned_none), context)` when a present field validator returns `none(...)`

---

_Source: `std/prelude/validation.genia` &middot; category `validation`. Generated from `@doc`/`@meta` by `tools/gen_function_docs.py`._

[<- Back to the Function Reference](../index.md)
