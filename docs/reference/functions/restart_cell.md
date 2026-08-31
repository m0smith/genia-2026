# `restart_cell`

**Category:** `cell` &nbsp;|&nbsp; **Arity:** 2

```genia
restart_cell(cell, new_state)
```

Replace the cell state, clear cached failure, and mark the cell ready again.

Phase 1 restart discards queued updates that were pending before restart.

---

_Source: `std/prelude/cell.genia` &middot; category `cell`. Generated from `@doc`/`@meta` by `tools/gen_function_docs.py`._

[<- Back to the Function Reference](../index.md)
