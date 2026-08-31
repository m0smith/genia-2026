# `find_opt`

**Category:** `list` &nbsp;|&nbsp; **Arity:** 2

```genia
find_opt(predicate, xs)
```

Canonical maybe-returning predicate-search helper for lists.

## Arguments

* `predicate`: function returning `true` for a match
* `xs`: list value

## Returns

* `some(value)` for the first matching element
* `none("no-match")` when no element matches

---

_Source: `std/prelude/list.genia` &middot; category `list`. Generated from canonical metadata by `tools/gen_function_docs.py`._

[<- Back to the Function Reference](../index.md)
