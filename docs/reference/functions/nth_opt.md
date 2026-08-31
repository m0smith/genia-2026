# `nth_opt`

**Category:** `list` &nbsp;|&nbsp; **Arity:** 2

```genia
nth_opt(n, xs)
```

Compatibility alias for `nth(index, list)`.

## Arguments

* `n`: zero-based index
* `xs`: list value

## Returns

* `some(value)` when the index exists
* `none("index-out-of-bounds")` when the index is missing

---

_Source: `std/prelude/list.genia` &middot; category `list`. Generated from `@doc`/`@meta` by `tools/gen_function_docs.py`._

[<- Back to the Function Reference](../index.md)
