# Open Shape Templates (Flexible Structure)

Status: **Implemented, Experimental (R9 E9-3)**

Open shapes structurally check ordinary maps through the existing Outcome
Template protocol.

```genia
pattern Present(value) = refinement_match((x) -> x != "", value)
pattern Person(value) = open_shape_match({name: Present}, value)
Person({name: "Ada", source: "csv"})
```

`open_shape_match(fields, value)` takes an ordinary map from string field names
to callable Templates. Every listed field is required; extra fields are allowed
and preserved. Success returns `some(original_map)`.

Specifications and fields are checked in specification insertion order. A
non-map or missing field is an ordinary mismatch. Nested Template `none` and
`err` Outcomes propagate unchanged; a nested `some` payload establishes
compatibility without transforming the record.

Open shapes add no declaration syntax, nominal identity, fixed layout,
coercion, exact/closed matching, or validation-error aggregation.
