# R9 Value Template and Representation Contract

Status: **Approved R9 design contract; not implemented.**

This document constrains later R9 design and implementation. Conceptual forms
shown here are not current syntax. `GENIA_STATE.md` remains final authority for
implemented behavior.

## Terms

- **Value** is ordinary Genia data and its observable value semantics.
- **Template** is an ordinary one-argument callable matcher, optionally carrying
  inert descriptive metadata, that returns `some(...)`, `none(...)`, or
  `err(...)`. It states structural or refinement compatibility without creating
  a nominal value category.
- **Representation** is an explicit, ordered carrier facet attached at a
  boundary to a value. It records how that value is carried, such as JSON. It is
  observable value data, not display text, a nominal wrapper class, or an
  implicit coercion.
- **Pattern** recognizes and destructures values. Representation-aware patterns
  remove only the facet they explicitly match before applying their nested
  pattern.
- **Rendering / Output Representation** is the existing `display`,
  `debug_repr`, `Format`, and `format` concern: producing strings for display,
  debugging, or output. It does not attach carrier facets.

The existing public APIs and documentation remain unchanged during R9. New
documentation should prefer **rendering** for the concern while retaining the
implemented names. Any future public terminology rename must introduce an
alias, migrate uses and tests incrementally, and remove the old name only in a
later change.

## Template boundary

A template is not a distinct runtime category. It uses the implemented matcher
contract:

1. It is an ordinary callable value and may be named, passed, stored, returned,
   imported, and composed.
2. It accepts one subject and returns an Outcome.
3. `some(...)` means compatibility, `none(...)` means ordinary mismatch, and
   `err(...)` means recoverable matching/validation failure.
4. Returning a non-Outcome or using a non-callable as a template is runtime
   misuse.
5. Template success metadata or a transformed payload does not replace the
   subject when used through `@?`, `@!`, or `&`; those operators keep their
   implemented original-subject semantics.

Template metadata, if later required for schema introspection or diagnostics,
is inert and does not affect callability, identity, matching, or composition.
E9-1 may add only the minimum metadata needed by a proving case.

Open structural templates require listed fields and allow extras. Exact/closed
structural templates require exactly the declared structure. Both match
ordinary maps/lists and do not promise nominal identity, constructor objects,
inheritance, fixed layout, or optimized storage. Concrete declaration syntax is
deferred to the relevant design tickets.

## Representation value model

A represented value consists semantically of:

```text
facet(name, carried_value)
```

The facet name is portable and registered by the language/library surface that
owns it. The carrier is an abstraction barrier: a host may choose any internal
layout, but Genia observes only the rules below.

- Construction is explicit at a boundary or through an explicit constructor.
- A represented value can be passed, returned, stored in maps/lists/Sheets, and
  carried through pipelines, Seq, and Flow as one ordinary value.
- Multiple facets are ordered nesting, not an unordered tag set. Constructing
  `a(b(value))` makes `a` outermost. Duplicate facets are permitted as distinct
  layers unless the owning facet contract rejects them.
- Matching `a(inner)` requires outer facet `a`, removes that layer for `inner`,
  and does not inspect or remove any other layer.
- A wildcard inside `a(_)` ignores the carried value; a binding inside `a(x)`
  receives the value after removal of the matched `a` layer.
- A representation mismatch is `none(...)`. Invalid boundary data is
  `err(...)`. Unknown facets, malformed carrier states, forbidden operations,
  and non-callable/non-Outcome matcher use are runtime misuse.

The general binding rule above permits `json(x)` to bind the ordinary decoded
value. A protection facet may strengthen it: future `secret(x)` must bind `x`
with secret protection still attached. Facet-specific strengthening may retain
or replace the matched layer, but may not weaken the general contract silently.

## Identity, equality, and keys

Portable semantics do not expose object/reference identity.

- A represented value is not equal to its unrepresented carried value.
- Two represented values are equal exactly when their ordered facet names and
  carried values are recursively equal.
- Facet order and duplicate layers participate in equality.
- A represented value is suitable as a map key exactly when its carried value
  and every facet name are suitable under the ordinary key/hash rules.
- Stripping the outer facet yields the carried value; reconstructing the same
  facet stack around an equal value yields an equal represented value.

Rendering must make represented values deterministic without exposing protected
payloads. Exact public rendering is owned by each facet's later implementation
contract.

## Preservation, derivation, and stripping

The default is deliberately non-propagating:

- Assignment, argument passing, return, collection insertion/removal, pipeline
  transport, and Seq/Flow transport preserve the represented value unchanged
  because they do not derive a new value.
- Destructuring preserves all facets not explicitly consumed by the pattern.
- Arithmetic, field access, indexing, map/filter callbacks, validation output,
  aggregation, Sheet transformations, encoding, and any other operation that
  derives a new value do not copy input facets automatically.
- An operation may preserve, replace, or add facets only when its public
  contract says so. That behavior must be explicit and testable.
- Stripping one facet is an explicit operation and removes only the named outer
  layer. Stripping all facets is not a generic implicit operation.

This avoids hidden taint propagation while providing a safe R10 foundation.
Protected facets such as `secret` may prohibit ordinary stripping and require a
separate authorized, auditable declassification operation. Matching or
destructuring alone must never declassify a protected value.

## Outcome and pattern interaction

- Representation-aware patterns use the existing named-pattern dispatch model.
- `@?` returns `some(original_subject)` on template success and propagates
  `none(...)` or `err(...)` unchanged.
- `@!` returns the original subject on success and raises its existing assertion
  error on `none(...)` or `err(...)`.
- `&` applies both matchers to the original represented subject and preserves
  its existing left-to-right short-circuit behavior.
- A nested representation pattern may intentionally pass an unwrapped carried
  value to its inner template; this local destructuring rule does not change the
  matcher operators' original-subject rule.
- No boolean template check, implicit template application, bare `@`, second
  validation pipeline, or alternate pattern namespace is introduced.

Conceptually:

```text
json(Person(x))
```

requires outer `json`, applies `Person` to the carried ordinary value, and binds
`x` according to `Person`. JSON mismatch or structural mismatch is `none`;
recoverable decode/schema validation failure is `err`; malformed matcher use is
a runtime error.

## JSON boundary required by R9

E9-5 must provide this minimum portable behavior:

- Decode one JSON text/byte input to ordinary Genia map, list, string, number,
  boolean, or `nil` values and attach one outer `json` facet to the decoded root.
- Encode a `json`-represented value, or an explicitly supported ordinary value,
  to deterministic JSON output without creating a parallel JSON object model.
- Preserve JSON object member names as strings and array order as list order.
- Reject malformed JSON as `err(...)` with normalized boundary diagnostics.
- Reject unsupported Genia values during encoding as `err(...)`; programmer
  misuse of the API remains a runtime error.
- Define numeric range/precision and duplicate-object-key policy in E9-5 before
  implementation; hosts must normalize their library behavior to that decision.
- Keep file/network/environment acquisition outside JSON value semantics.

JSON parsing/serialization may be supplied by a host capability. The value
mapping, facet application, matching, error categories, and normalized
observations are portable.

JSON Schema is not part of E9-5. E9-6 may translate only an explicitly listed
subset into ordinary templates. Unsupported keywords must fail clearly rather
than being ignored.

## Portability and Core IR

The preferred contract requires no new Core IR node. Representation
construction/observation and representation-aware matching must use existing
call, value, and pattern lowering unless a later preflight proves that
impossible. Any proposed Core IR change is a hard stop requiring separate
approval before implementation.

Future shared specs must cover:

- parse: any approved representation/template surface forms;
- IR: lowering through existing portable node families;
- eval: construction, observation, equality, nesting, matching, storage,
  passing, explicit preservation/replacement/strip, and JSON value mapping;
- flow: transport versus derivation behavior;
- error: normalized misuse, invalid-state, JSON, and forbidden-strip failures.

Python carrier classes, metadata storage, hashing implementation, and JSON
library exceptions remain reference-host details. Every future host must
preserve the portable observations above.

## Decision table

| Concern | Contract decision |
|---|---|
| Template | Ordinary one-argument Outcome matcher; optional inert metadata only |
| Identity | No portable reference identity; facet stack is observable value data |
| Equality | Recursive carried-value equality plus exact ordered facet equality |
| Matching | Match one explicit outer facet, then apply the nested pattern |
| Nesting | Ordered outer-to-inner layers; not a set |
| Transport | Passing/storage/pipeline/Seq/Flow preserve the same represented value |
| Derivation | New values receive no facets unless the operation explicitly says so |
| Stripping | Explicit, one outer facet at a time; protected facets may forbid it |
| Errors | mismatch=`none`; recoverable boundary failure=`err`; misuse=runtime error |
| Portability | Semantics and normalized observations portable; storage/adapters host-local |
| Core IR | No new node preferred or approved by this contract |
| Rendering | Existing display/debug/Format concern; separate from carrier facets |

## Release sequencing and issue disposition

Recommended order:

1. E9-1: prove ordinary Outcome matchers plus only necessary inert template
   metadata; settle open/exact structural matcher construction syntax.
2. E9-2: implement the carrier abstraction, ordered nesting, equality, explicit
   observation/strip operations, and representation-aware matching.
3. E9-3: implement refinement and open structural templates for validated maps.
4. E9-4: add exact/closed structural templates without layout or nominal claims.
5. E9-5: implement the minimum JSON boundary above.
6. E9-6: add the approved JSON Schema subset as template production.
7. E9-7: prove `json(Person(x))` in an Outcome-aware validated pipeline.
8. E9-8: perform release truth audit and distillation, including terminology and
   composability-matrix review.

E9-2 depends on the E9-1 matcher/template boundary. E9-3 may proceed after E9-1
in parallel with E9-2 only if it does not use representation syntax. E9-4
depends on E9-3 decisions. E9-5 depends on E9-2. E9-6 depends on E9-3 through
E9-5. E9-7 depends on all implementation slices. E9-8 is last.

- #89 should be rewritten as E9-3.
- #90 should be rewritten as E9-4 with nominal `Struct`, layout, and performance
  assumptions removed.
- #91 remains later/follow-up; R9 does not need general function contracts.
- #92 remains later/follow-up; variants and exhaustiveness are not required.
- #399 should be superseded by or narrowed into E9-1/E9-3 validated-record
  acceptance criteria; it is not a blocker in its current form.
- #166 remains the implemented rendering/Format history and future rendering
  follow-up, not the R9 carrier-representation contract.

## E9-1 gate

**GO**, subject to an E9-1 preflight that keeps the runtime model to ordinary
Outcome matchers and scopes any metadata to a demonstrated structural-template
need. E9-1 must not add representation carriers, JSON, contracts, variants,
bare `@`, implicit application, nominal types, or a new Core IR node.
