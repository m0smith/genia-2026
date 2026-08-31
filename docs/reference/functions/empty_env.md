# `empty_env`

**Category:** `eval` &nbsp;|&nbsp; **Arity:** 0

```genia
empty_env()
```

Create a fresh metacircular evaluation environment.

## Returns
- host-backed metacircular environment value

## Notes
- the fresh environment can see current builtins and autoloaded stdlib names
- ordinary lexical definitions remain local to that environment chain

---

_Source: `std/prelude/eval.genia` &middot; category `eval`. Generated from `@doc`/`@meta` by `tools/gen_function_docs.py`._

[<- Back to the Function Reference](../index.md)
