# `cell_stop`

**Category:** `cell` &nbsp;|&nbsp; **Arity:** 1

```genia
cell_stop(cell)
```

Gracefully stop a cell after draining its mailbox.

Queued updates are processed before the worker exits.
After stop, `cell_send` raises and `cell_status` returns `"stopped"`.
`cell_get` still returns the last state.

---

_Source: `std/prelude/cell.genia` &middot; category `cell`. Generated from canonical metadata by `tools/gen_function_docs.py`._

[<- Back to the Function Reference](../index.md)
