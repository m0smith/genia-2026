# `extend`

**Category:** `eval` &nbsp;|&nbsp; **Arity:** 3

```genia
extend(env, params, args)
```

Create a child metacircular environment with lambda parameters bound to argument values.

## Arguments
- `env`: parent metacircular environment
- `params`: quoted lambda parameter representation
- `args`: list of evaluated argument values

## Returns
- child metacircular environment

## Notes
- `params` uses the quoted lambda parameter representation
- `args` must be an ordinary list of evaluated argument values

---

_Source: `std/prelude/eval.genia` &middot; category `eval`. Generated from canonical metadata by `tools/gen_function_docs.py`._

[<- Back to the Function Reference](../index.md)
