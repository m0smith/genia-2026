# `apply`

**Category:** `fn` &nbsp;|&nbsp; **Arity:** 2

```genia
apply(proc, args)
```

Call `proc` with a list of positional arguments.

This applies ordinary callable values directly.

If `proc` is a metacircular compound procedure produced by `eval`, this also evaluates its body in the captured lexical environment.

---

_Source: `std/prelude/fn.genia` &middot; category `fn`. Generated from `@doc`/`@meta` by `tools/gen_function_docs.py`._

[<- Back to the Function Reference](../index.md)
