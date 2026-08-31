# `evolve`

**Category:** `flow` &nbsp;|&nbsp; **Arity:** 2

```genia
evolve(init, step)
```

Create a Flow by repeatedly applying `step` to the previous value.

The first emitted item is `init`; each later item is `step(previous_value)`.

## Arguments
- `init`: the first item emitted by the Flow
- `step`: function mapping the previous value to the next value

## Returns
- a lazy Flow of successive values starting at `init`

## Notes
- the Flow is unbounded; bound it with `take`/`head`
- lazy and pull-based, computing one step at a time as items are demanded

---

_Source: `std/prelude/flow.genia` &middot; category `flow`. Generated from canonical metadata by `tools/gen_function_docs.py`._

[<- Back to the Function Reference](../index.md)
