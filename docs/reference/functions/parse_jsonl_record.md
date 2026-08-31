# `parse_jsonl_record`

**Category:** `json` &nbsp;|&nbsp; **Arity:** 1

```genia
parse_jsonl_record(line)
```

Parse one JSONL object record into an Outcome.

## Arguments
- `line`: one JSONL text line

## Returns
- `some(record, context)` for a JSON object
- `none(context)` for a blank line
- `err(reason, context)` for malformed JSON or a non-object JSON value

---

_Source: `std/prelude/json.genia` &middot; category `json`. Generated from canonical metadata by `tools/gen_function_docs.py`._

[<- Back to the Function Reference](../index.md)
