# `ref_update`

**Category:** `ref` &nbsp;|&nbsp; **Arity:** 2

```genia
ref_update(ref_value, updater)
```

Apply `updater` to the current ref value atomically and store the result.

## Arguments
- `ref_value`: synchronized ref
- `updater`: function from the current value to the replacement value

## Returns
- replacement value produced by `updater`

## Notes
- reading and updating occur under the ref's synchronization boundary

---

_Source: `std/prelude/ref.genia` &middot; category `ref`. Generated from canonical metadata by `tools/gen_function_docs.py`._

[<- Back to the Function Reference](../index.md)
