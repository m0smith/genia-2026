# `validate_record`

**Category:** `validation` &nbsp;|&nbsp; **Arity:** 2, 3

```genia
validate_record(record, validators)
validate_record(record, validators, context)
```

Compose field validators over one record and return a record-level Outcome.

## Arguments

* `record`: map record to validate
* `validators`: map whose keys are field paths and whose values are validator callables; each callable receives the original `record` and must return an Outcome
* `context`: optional caller-provided context preserved in the returned record-level Outcome

## Returns

* `some(clean_record, context?)` when all validators return `some(...)` or `none(...)`
* `err(quote(record_validation_failed), context_with_diagnostics)` when any validator returns `err(...)`

## Errors

* raises when `record` is not a map, `validators` is not a map, a validator is not callable, or a validator returns a non-Outcome

---

_Source: `std/prelude/validation.genia` &middot; category `validation`. Generated from `@doc`/`@meta` by `tools/gen_function_docs.py`._

[<- Back to the Function Reference](../index.md)
