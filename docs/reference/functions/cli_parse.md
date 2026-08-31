# `cli_parse`

**Category:** `cli` &nbsp;|&nbsp; **Arity:** 1, 2

```genia
cli_parse(args)
cli_parse(args, spec)
```

Parse raw CLI args into `[opts, positionals]`, optionally using a minimal `flags` / `options` / `aliases` spec map.

## Arguments
- `args`: list of raw argument strings
- `spec`: map containing optional `flags`, `options`, and `aliases`

## Returns
- `[opts, positionals]`, where `opts` is a map and `positionals` preserves input order

## Errors
- raises deterministic type or value errors for invalid inputs, malformed specs, ambiguous short-option groups, or missing option values

## Notes
- `argv()` remains the raw host-backed CLI primitive
- parsing semantics live in prelude in this phase

---

_Source: `std/prelude/cli.genia` &middot; category `cli`. Generated from canonical metadata by `tools/gen_function_docs.py`._

[<- Back to the Function Reference](../index.md)
