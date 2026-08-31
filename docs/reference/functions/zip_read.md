# `zip_read`

**Category:** `file` &nbsp;|&nbsp; **Arity:** 1

```genia
zip_read(path)
```

Create a lazy Flow of zip entries from `path`.

## Arguments
- `path`: zip archive path string

## Returns
- lazy Flow of `[filename, bytes]` entries
- `none("file-not-found", context)` or `none("zip-read-error", context)` on failure

## Notes
- `bytes` is the opaque bytes runtime value

---

_Source: `std/prelude/file.genia` &middot; category `file`. Generated from canonical metadata by `tools/gen_function_docs.py`._

[<- Back to the Function Reference](../index.md)
