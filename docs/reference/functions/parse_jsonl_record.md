# `parse_jsonl_record`

**Category:** `json` &nbsp;|&nbsp; **Arity:** 1

```genia
parse_jsonl_record(line)
```

Parse one JSONL object record into an Outcome.

Returns `some(record, context)` for JSON objects.
Returns `none(context)` for blank lines.
Returns `err(reason, context)` for malformed JSON or non-object JSON values.

---

_Source: `std/prelude/json.genia` &middot; category `json`. Generated from canonical metadata by `tools/gen_function_docs.py`._

[<- Back to the Function Reference](../index.md)
