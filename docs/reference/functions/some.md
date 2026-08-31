# `some`

**Category:** `option` &nbsp;|&nbsp; **Arity:** 0+

```genia
some(..args)
```

Wrap a present value in the Option success form `some(value)`.

## Arguments
- `value`: the value to wrap as present
- `context`: optional metadata carried alongside the value

## Returns
- `some(value)`, carrying `context` when it is supplied

## Errors
- raises when called with other than one or two arguments

---

_Source: `std/prelude/option.genia` &middot; category `option`. Generated from canonical metadata by `tools/gen_function_docs.py`._

[<- Back to the Function Reference](../index.md)
