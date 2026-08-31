# `awkify`

**Category:** `awk` &nbsp;|&nbsp; **Arity:** 2

```genia
awkify(fn, xs)
```

Apply an AWK-style row function over a list of rows.

`fn` receives `(line_number, row)` and returns the row to keep or `nil` to drop it.
Line numbers start at 1.

## Arguments
- `fn`: function `(n, row) -> value | nil`
- `xs`: list of rows

## Returns
- list of non-nil results

## Examples
```genia
odd(n, row) = n % 2 == 1 -> row | _ -> nil
awkify(odd, ["a", "b", "c"]) -> ["a", "c"]
```

---

_Source: `std/prelude/awk.genia` &middot; category `awk`. Generated from `@doc`/`@meta` by `tools/gen_function_docs.py`._

[<- Back to the Function Reference](../index.md)
