# `awk_filter`

**Category:** `awk` &nbsp;|&nbsp; **Arity:** 2

```genia
awk_filter(predicate, xs)
```

Filter rows with an AWK-style predicate.

## Arguments
- `predicate`: function receiving `(line_number, row)`
- `xs`: list of rows

## Returns
- list of rows for which `predicate` returns `true`

---

_Source: `std/prelude/awk.genia` &middot; category `awk`. Generated from canonical metadata by `tools/gen_function_docs.py`._

[<- Back to the Function Reference](../index.md)
