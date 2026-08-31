# `rules`

**Category:** `flow` &nbsp;|&nbsp; **Arity:** 0+

```genia
rules(..fns)
```

Apply rule functions left-to-right to each incoming flow item.

## Arguments
- `fns`: variadic rule functions, applied in order to each item; a Flow may be passed as the final argument to run immediately

## Returns
- a Flow stage `(flow) -> flow`, or the transformed Flow when a Flow is supplied as the last argument

## Notes
- rule orchestration, defaulting, and contract validation live in the prelude in this phase
- legacy/compatibility name; prefer `refine`
- lazy and pull-based

---

_Source: `std/prelude/flow.genia` &middot; category `flow`. Generated from `@doc`/`@meta` by `tools/gen_function_docs.py`._

[<- Back to the Function Reference](../index.md)
