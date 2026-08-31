# `format_compose`

**Category:** `string` &nbsp;|&nbsp; **Arity:** 1

```genia
format_compose(parts)
```

Compose string templates and Format values into one reusable Format.

## Arguments
- `parts`: list of string templates and/or Format values, rendered in order

## Returns
- a Format value that renders each part in sequence when later formatted

## Errors
- rejects a non-list `parts`, or any element that is not a string or Format

---

_Source: `std/prelude/string.genia` &middot; category `string`. Generated from canonical metadata by `tools/gen_function_docs.py`._

[<- Back to the Function Reference](../index.md)
