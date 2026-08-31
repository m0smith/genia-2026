# `awk_map`

**Category:** `awk` &nbsp;|&nbsp; **Arity:** 2

```genia
awk_map(fn, xs)
```

Map rows with AWK-style line numbering.

## Arguments
- `fn`: function receiving `(line_number, row)`
- `xs`: list of rows

## Returns
- list of mapped non-`nil` results

---

_Source: `std/prelude/awk.genia` &middot; category `awk`. Generated from canonical metadata by `tools/gen_function_docs.py`._

[<- Back to the Function Reference](../index.md)
