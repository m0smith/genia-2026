# `write_file`

**Category:** `file` &nbsp;|&nbsp; **Arity:** 2

```genia
write_file(path, text)
```

Write UTF-8 text content to `path`.

## Arguments
- `path`: filesystem path string
- `text`: UTF-8 text content

## Returns
- `path` on success
- `none("file-write-error", context)` on failure

---

_Source: `std/prelude/file.genia` &middot; category `file`. Generated from canonical metadata by `tools/gen_function_docs.py`._

[<- Back to the Function Reference](../index.md)
