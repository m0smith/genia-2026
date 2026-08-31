# `eval`

**Category:** `eval` &nbsp;|&nbsp; **Arity:** 2

```genia
eval(expr, env)
```

Evaluate a quoted Genia expression in a metacircular environment.

## Arguments
- `expr`: quoted Genia expression
- `env`: metacircular environment

## Returns
- evaluated value

## Notes
- implemented forms are self-evaluating literals, symbols, quoted expressions, assignment, lambda, match/case, application, and blocks

---

_Source: `std/prelude/eval.genia` &middot; category `eval`. Generated from canonical metadata by `tools/gen_function_docs.py`._

[<- Back to the Function Reference](../index.md)
