# `cli_option_or`

**Category:** `cli` &nbsp;|&nbsp; **Arity:** 3

```genia
cli_option_or(opts, name, default)
```

Return a parsed option value or `default` when the option is missing.

## Arguments
- `opts`: parsed options map
- `name`: option name string
- `default`: fallback value

## Returns
- parsed option value when present, otherwise `default`

---

_Source: `std/prelude/cli.genia` &middot; category `cli`. Generated from canonical metadata by `tools/gen_function_docs.py`._

[<- Back to the Function Reference](../index.md)
