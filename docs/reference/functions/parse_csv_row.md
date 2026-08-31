# `parse_csv_row`

**Category:** `json` &nbsp;|&nbsp; **Arity:** 1, 2

```genia
parse_csv_row(line)
parse_csv_row(headers, line)
```

Parse one CSV row into an Outcome.

## Arguments
- `line`: one CSV text row
- `headers`: optional list of unique non-empty string field names

## Returns
- `some(fields, context)` for a valid row without headers
- `some(record, context)` for a valid row with headers
- `none("blank_line", context)` for a blank line
- `err(reason, context)` for a malformed row or header-count mismatch

## Errors
- raises a type or value error for invalid `line` or `headers` arguments

---

_Source: `std/prelude/json.genia` &middot; category `json`. Generated from canonical metadata by `tools/gen_function_docs.py`._

[<- Back to the Function Reference](../index.md)
