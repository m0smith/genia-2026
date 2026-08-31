# `keep_some`

**Category:** `flow` &nbsp;|&nbsp; **Arity:** 1, 2

```genia
keep_some(flow)
keep_some(stage, flow)
```

Keep only successful Option values from a flow.

`keep_some(flow)` filters a Flow that already holds Option items.
`keep_some(stage, flow)` applies an Option-returning `stage` to each item inline.

## Arguments
- `stage`: optional Option-returning function applied to each item before filtering
- `flow`: the input Flow

## Returns
- a lazy Flow of the values inside each `some(value)`

## Notes
- `some(value)` is unwrapped to `value`; `none(...)` items are dropped
- equivalent to `keep_some_else(stage, (_) -> nil, flow)`
- lazy and pull-based

---

_Source: `std/prelude/flow.genia` &middot; category `flow`. Generated from `@doc`/`@meta` by `tools/gen_function_docs.py`._

[<- Back to the Function Reference](../index.md)
