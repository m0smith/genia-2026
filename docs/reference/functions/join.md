# `join`

**Category:** `string` &nbsp;|&nbsp; **Arity:** 2

```genia
join(sep, xs)
```

Join the strings in `xs` with `sep` between elements.

## Arguments
- `sep`: separator placed between adjacent elements
- `xs`: list of strings to join

## Returns
- a single string of the elements joined by `sep`

## Errors
- rejects a non-list `xs`, or a list containing any non-string element

---

_Source: `std/prelude/string.genia` &middot; category `string`. Generated from `@doc`/`@meta` by `tools/gen_function_docs.py`._

[<- Back to the Function Reference](../index.md)
