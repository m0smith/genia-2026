# `map_get`

**Category:** `map` &nbsp;|&nbsp; **Arity:** 2

```genia
map_get(map, key)
```

Return the stored value for `key`, or `none("missing-key", {key: key})` when absent.

Prefer `get(key, map)` for maybe-aware lookup in new code.

## Arguments
- `map`: the map to look up in
- `key`: the key to find

## Returns
- the stored value when `key` is present
- `none("missing-key", {key: key})` when `key` is absent

---

_Source: `std/prelude/map.genia` &middot; category `map`. Generated from canonical metadata by `tools/gen_function_docs.py`._

[<- Back to the Function Reference](../index.md)
