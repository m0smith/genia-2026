# `format`

**Category:** `string` &nbsp;|&nbsp; **Arity:** 2

```genia
format(template, values)
```

Render `template` by substituting placeholders from `values`.

## Arguments
- `template`: a string template, or a Format value, containing named or positional placeholders
- `values`: a map supplying named placeholders, or a list supplying positional ones

## Returns
- the rendered string with every placeholder resolved from `values`

---

_Source: `std/prelude/string.genia` &middot; category `string`. Generated from `@doc`/`@meta` by `tools/gen_function_docs.py`._

[<- Back to the Function Reference](../index.md)
