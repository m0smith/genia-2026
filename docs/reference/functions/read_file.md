# `read_file`

**Category:** `file` &nbsp;|&nbsp; **Arity:** 1

```genia
read_file(path)
```

Read a UTF-8 text file from `path`.

Returns file content on success.
Returns `none("file-not-found", context)` or `none("file-read-error", context)` on failure.

---

_Source: `std/prelude/file.genia` &middot; category `file`. Generated from `@doc`/`@meta` by `tools/gen_function_docs.py`._

[<- Back to the Function Reference](../index.md)
