# `zip_write`

**Category:** `file` &nbsp;|&nbsp; **Arity:** 1, 2

```genia
zip_write(path)
zip_write(path, items)
```

Write zip items to `path` from a Flow or list.

## Arguments
- `path`: destination zip archive path string
- `items`: Flow or list of zip items

## Returns
- `path` on success
- `none("zip-write-error", context)` on failure

## Notes
- accepted item forms are `[filename, bytes]`, `[filename, string]`, or zip entries

---

_Source: `std/prelude/file.genia` &middot; category `file`. Generated from canonical metadata by `tools/gen_function_docs.py`._

[<- Back to the Function Reference](../index.md)
