# `keep_some_else`

**Category:** `flow` &nbsp;|&nbsp; **Arity:** 2, 3

```genia
keep_some_else(stage, dead_handler)
keep_some_else(stage, dead_handler, flow)
```

Apply an Option-returning `stage` to each flow item, routing failures to `dead_handler`.

## Arguments
- `stage`: Option-returning function; it receives the original raw flow item
- `dead_handler`: called with the original item whenever `stage` returns `none(...)`
- `flow`: the input Flow (omit to get a reusable stage)

## Returns
- with `flow`: a lazy Flow of the values from each `some(value)`
- without `flow`: a stage `(flow) -> flow`

## Notes
- `some(value)` continues on the main Flow as `value`; `none(...)` drops the item and invokes `dead_handler`
- explicit dead-letter routing; it does not change ordinary `|>` semantics outside this helper
- lazy and pull-based

---

_Source: `std/prelude/flow.genia` &middot; category `flow`. Generated from canonical metadata by `tools/gen_function_docs.py`._

[<- Back to the Function Reference](../index.md)
