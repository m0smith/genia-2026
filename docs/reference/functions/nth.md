# `nth`

**Category:** `list` &nbsp;|&nbsp; **Arity:** 2

```genia
nth(n, xs)
```

Return the element at zero-based index `n` as structured absence-aware Option.

## Arguments

* `n`: zero-based index
* `xs`: list value

## Returns

* `some(value)` when the index exists
* `none("index-out-of-bounds")` when the index is missing

---

_Source: `std/prelude/list.genia` &middot; category `list`. Generated from canonical metadata by `tools/gen_function_docs.py`._

[<- Back to the Function Reference](../index.md)
