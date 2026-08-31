# `err`

**Category:** `option` &nbsp;|&nbsp; **Arity:** 0+

```genia
err(..args)
```

Construct a recoverable Outcome failure value `err(reason)`.

## Arguments
- `reason`: the failure reason value
- `context`: optional metadata describing the failure

## Returns
- `err(reason)`, carrying `context` when it is supplied

## Notes
- Distinct from `none(...)`; both `none?` and `some?` report `false` for an `err` value

## Errors
- raises when called with other than one or two arguments

---

_Source: `std/prelude/option.genia` &middot; category `option`. Generated from `@doc`/`@meta` by `tools/gen_function_docs.py`._

[<- Back to the Function Reference](../index.md)
