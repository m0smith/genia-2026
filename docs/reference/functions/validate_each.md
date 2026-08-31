# `validate_each`

**Category:** `validation` &nbsp;|&nbsp; **Arity:** 2

```genia
validate_each(source, validator)
```

Apply a validator to each item in a list or Flow and return Outcomes.

## Arguments

* `source`: list or Flow of items to validate
* `validator`: callable that receives each item and must return an Outcome

## Returns

* a list of Outcome values in source order when `source` is a list
* a lazy Flow of Outcome values when `source` is a Flow
* one Outcome per input item: `some(...)`, `none(...)`, or `err(...)`

## Errors

* raises when `source` is not a list or Flow
* raises when `validator` is not callable
* raises when `validator` returns a non-Outcome value; for Flow input this occurs when the returned Flow is consumed

## Notes

* `validate_each` does not aggregate; use `collect_validated` for aggregation
* `validate_each/3` is not implemented

---

_Source: `std/prelude/validation.genia` &middot; category `validation`. Generated from `@doc`/`@meta` by `tools/gen_function_docs.py`._

[<- Back to the Function Reference](../index.md)
