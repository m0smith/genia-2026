# `as_seq`

**Category:** `flow` &nbsp;|&nbsp; **Arity:** 1

```genia
as_seq(value)
```

Explicitly adapt a list or string into a Seq-compatible ordered source.

## Arguments
- `value`: a list or string to adapt

## Returns
- an ordered, Seq-compatible source over `value`

## Notes
- lists are yielded as ordered elements without flattening
- strings are decomposed into one-character strings only through this helper

---

_Source: `std/prelude/flow.genia` &middot; category `flow`. Generated from canonical metadata by `tools/gen_function_docs.py`._

[<- Back to the Function Reference](../index.md)
