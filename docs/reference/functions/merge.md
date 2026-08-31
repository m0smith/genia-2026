# `merge`

**Category:** `flow` &nbsp;|&nbsp; **Arity:** 1, 2

```genia
merge(pair)
merge(flow1, flow2)
```

Concatenate two flows into one output flow.

`merge(flow1, flow2)` emits items from `flow1` first, then `flow2`.
`merge(pair)` unpacks a `[flow1, flow2]` pair, e.g. from `tee`.

## Arguments
- `flow1`: Flow whose items are emitted first
- `flow2`: Flow whose items are emitted after `flow1` is exhausted
- `pair`: a `[flow1, flow2]` pair, as an alternative to passing the two flows separately

## Returns
- a lazy Flow emitting all of `flow1` followed by all of `flow2`

## Notes
- lazy and pull-based; `flow2` is not consumed until `flow1` is exhausted

---

_Source: `std/prelude/flow.genia` &middot; category `flow`. Generated from `@doc`/`@meta` by `tools/gen_function_docs.py`._

[<- Back to the Function Reference](../index.md)
