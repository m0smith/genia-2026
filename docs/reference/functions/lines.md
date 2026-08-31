# `lines`

**Category:** `flow` &nbsp;|&nbsp; **Arity:** 1

```genia
lines(source)
```

Create a Flow from `stdin`, an incoming Flow, or a list of strings.

## Arguments
- `source`: `stdin`, an existing Flow, or a list of strings to read lines from

## Returns
- a Flow of the source lines

## Notes
- the Flow is lazy and pull-based, consumed once as items are demanded

---

_Source: `std/prelude/flow.genia` &middot; category `flow`. Generated from `@doc`/`@meta` by `tools/gen_function_docs.py`._

[<- Back to the Function Reference](../index.md)
