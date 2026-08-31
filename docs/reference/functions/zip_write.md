# `zip_write`

**Category:** `file` &nbsp;|&nbsp; **Arity:** 1, 2

```genia
zip_write(path)
zip_write(path, items)
```

Write zip items to `path` from a Flow or list.

Accepted item forms are `[filename, bytes]`, `[filename, string]`, or zip entries.
Returns `path` on success or `none("zip-write-error", context)` on failure.

---

_Source: `std/prelude/file.genia` &middot; category `file`. Generated from `@doc`/`@meta` by `tools/gen_function_docs.py`._

[<- Back to the Function Reference](../index.md)
