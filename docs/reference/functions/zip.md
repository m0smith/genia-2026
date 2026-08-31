# `zip`

**Category:** `flow` &nbsp;|&nbsp; **Arity:** 1, 2

```genia
zip(pair)
zip(flow1, flow2)
```

Combine two flows into a flow of pairs.

`zip(flow1, flow2)` pairs items from both flows at each step.
`zip(pair)` unpacks a `[flow1, flow2]` pair, e.g. from `tee`.

## Arguments
- `flow1`: Flow supplying the left element of each pair
- `flow2`: Flow supplying the right element of each pair
- `pair`: a `[flow1, flow2]` pair, as an alternative to passing the two flows separately

## Returns
- a lazy Flow whose items are `[left, right]`, preserving lockstep order

## Notes
- output stops as soon as either input Flow is exhausted
- lazy and pull-based

---

_Source: `std/prelude/flow.genia` &middot; category `flow`. Generated from `@doc`/`@meta` by `tools/gen_function_docs.py`._

[<- Back to the Function Reference](../index.md)
