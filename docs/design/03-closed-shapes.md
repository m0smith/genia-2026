# Exact/Closed Shape Templates

Status: **Implemented, Experimental (R9 E9-4)**

Exact and closed are two descriptions of the same E9-4 compatibility rule.
Exact shapes structurally check ordinary maps through the existing Outcome
Template protocol; they do not create Struct values.

```genia
pattern Any(value) = some(value)
pattern Point(value) = exact_shape_match({x: Any, y: Any}, value)
Point({y: 2, x: 1})
```

`exact_shape_match(fields, value)` takes an ordinary map from string field
names to callable Templates. Candidate and specification key sets must be
equal, independent of insertion order. Success returns `some(original_map)`.

The specification is validated first. Missing fields are reported in
specification order, then extras in candidate order. Only an exact field set
causes field Templates to run in specification order. Nested `none` and `err`
Outcomes propagate unchanged; nested `some` payloads do not transform fields.

This helper adds no constructor, nominal identity, positional/labeled shape,
fixed/compact layout, special field access, coercion, inheritance, extension,
or performance guarantee. Open shapes remain distinct because they allow
extra fields.
