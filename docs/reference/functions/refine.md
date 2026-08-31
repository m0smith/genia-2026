# `refine`

**Category:** `flow` &nbsp;|&nbsp; **Arity:** 0+

```genia
refine(..steps)
```

Apply step functions left-to-right to each incoming flow item.

## Arguments
- `steps`: variadic step functions, applied in order to each item; a Flow may be passed as the final argument to run immediately

## Returns
- a Flow stage `(flow) -> flow`, or the transformed Flow when a Flow is supplied as the last argument

## Notes
- preferred alias for `rules(..steps)`; see also `rules` (compatibility)
- lazy and pull-based

---

_Source: `std/prelude/flow.genia` &middot; category `flow`. Generated from `@doc`/`@meta` by `tools/gen_function_docs.py`._

[<- Back to the Function Reference](../index.md)
