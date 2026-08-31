# `cli_option`

**Category:** `cli` &nbsp;|&nbsp; **Arity:** 2

```genia
cli_option(opts, name)
```

Return a parsed option value when present.

## Arguments
- `opts`: parsed options map
- `name`: option name string

## Returns
- parsed option value when present
- `none("missing-key", {key: name})` when absent

---

_Source: `std/prelude/cli.genia` &middot; category `cli`. Generated from canonical metadata by `tools/gen_function_docs.py`._

[<- Back to the Function Reference](../index.md)
