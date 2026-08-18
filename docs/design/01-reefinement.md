# Refinement Templates (Value Constraints)

Status: **Implemented, Experimental (R9 E9-3)**

Refinements reuse the ordinary one-argument Outcome Template protocol. They do
not create a nominal type or new declaration syntax.

```genia
pattern NaturalNumber(value) = refinement_match((n) -> n >= 0, value)
NaturalNumber(3)
```

`refinement_match(predicate, value)` invokes the predicate once. `true` returns
`some(value)` with the original subject; `false` returns
`none("refinement-mismatch")`. A non-callable predicate or non-boolean result is
runtime misuse.

Named refinement Templates compose through existing direct calls,
`Name(inner)`, `@?`, `@!`, and `&` behavior. There is no coercion, implicit
conversion, compile-time enforcement, or `when` syntax.
