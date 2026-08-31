# `tee`

**Category:** `flow` &nbsp;|&nbsp; **Arity:** 1

```genia
tee(flow)
```

Split one input flow into two lazy branch flows.

## Arguments
- `flow`: the source Flow to split

## Returns
- a pair of two lazy branch Flows over the same source items

## Notes
- the source Flow is consumed once, buffered only as needed when one branch lags behind the other
- both branches are lazy and pull-based

---

_Source: `std/prelude/flow.genia` &middot; category `flow`. Generated from canonical metadata by `tools/gen_function_docs.py`._

[<- Back to the Function Reference](../index.md)
