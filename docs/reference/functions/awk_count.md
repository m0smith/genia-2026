# `awk_count`

**Category:** `awk` &nbsp;|&nbsp; **Arity:** 2

```genia
awk_count(predicate, xs)
```

Count rows that satisfy an AWK-style predicate.

## Arguments
- `predicate`: function receiving `(line_number, row)`
- `xs`: list of rows

## Returns
- number of rows for which `predicate` returns `true`

---

_Source: `std/prelude/awk.genia` &middot; category `awk`. Generated from canonical metadata by `tools/gen_function_docs.py`._

[<- Back to the Function Reference](../index.md)
