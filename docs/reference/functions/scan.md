# `scan`

**Category:** `flow` &nbsp;|&nbsp; **Arity:** 2, 3

```genia
scan(step, initial_state)
scan(step, initial_state, flow)
```

Stateful flow transform driven by `step`.

`step(state, item)` must return `[next_state, output]`.
Use this for running totals, buffering, and fixed-size windowing.

## Arguments
- `step`: function receiving the current state and an item, returning `[next_state, output]`
- `initial_state`: the state passed to `step` for the first item
- `flow`: the input Flow (omit to get a reusable stage)

## Returns
- with `flow`: a lazy Flow of the `output` values produced by `step`
- without `flow`: a stage `(flow) -> flow` that applies the transform when given a Flow

## Notes
- `next_state` stays internal to this operator and is not exposed externally
- lazy and pull-based

---

_Source: `std/prelude/flow.genia` &middot; category `flow`. Generated from canonical metadata by `tools/gen_function_docs.py`._

[<- Back to the Function Reference](../index.md)
