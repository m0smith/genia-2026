# `parse_csv_row`

**Category:** `json` &nbsp;|&nbsp; **Arity:** 1, 2

```genia
parse_csv_row(line)
parse_csv_row(headers, line)
```

Parse one CSV row into an Outcome.

Returns `some(fields, context)` for a valid row.
Returns `some(record, context)` when headers are provided.
Returns `none("blank_line", context)` for blank lines.
Returns `err(reason, context)` for malformed rows or header mismatches.

---

_Source: `std/prelude/json.genia` &middot; category `json`. Generated from `@doc`/`@meta` by `tools/gen_function_docs.py`._

[<- Back to the Function Reference](../index.md)
