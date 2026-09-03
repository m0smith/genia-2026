# R15 — Validated Value Modeling

Status: Planned roadmap addendum — non-authoritative. This document does not define implemented language behavior.

`GENIA_STATE.md` remains final authority for implemented behavior. This release must follow the normal contract, design, failing-test, implementation, documentation, audit, and distillation gates before any candidate behavior is described as implemented.

## Theme

> Extend R9 Value Templates into a practical, Pydantic-class validation toolset for Genia's Outcome-aware validated data pipelines without introducing model classes, implicit coercion, or a second type/validation system.

R15 is a direct continuation of the completed R9 Value Templates & Representations foundation. It is motivated by the observation that Genia already covers much of the validation core commonly associated with Pydantic through refinements, open/exact structural Templates, nested matching, JSON decoding, JSON Schema-derived Templates, Outcomes, and strict/no-coercion semantics.

The goal is not Pydantic compatibility. The goal is to close the remaining high-value gaps for real validated-data workflows while preserving Genia's value-first, pattern-first model.

## Product fit

R15 directly strengthens Genia's first killer workflow:

```text
messy records in
  → decode / normalize
  → validate with Templates
  → accumulate useful diagnostics
  → produce ordinary validated values
  → emit / serialize / expose schema
```

## Candidate scope

### 1. Inert, inspectable Template descriptions

Implement the descriptive foundation that R9 deliberately left optional. The
supported structural Template constructors may carry immutable, inert metadata
describing their validation structure while remaining ordinary one-argument
Outcome callables.

Required direction:

- metadata does not affect Template callability, identity, matching, or
  original-subject preservation
- only Templates built from explicitly supported constructors are inspectable;
  arbitrary callable Templates remain valid but opaque
- operations that require inspection reject or report an unsupported opaque
  Template explicitly rather than guessing
- descriptions use existing values/callables where practical and require no new
  Core IR node unless a later preflight proves that impossible
- descriptions provide one shared foundation for accumulated diagnostics,
  defaults, JSON Schema generation, alternatives, and recursive references

This slice is foundational. Generating schema or traversing validation structure
directly from opaque host closures would leak semantics into the reference host
and make future hosts reverse-engineer implementation details.

### 2. Defaults and explicit normalization

Define how missing fields may receive explicit defaults and how normalization may be composed with validation without turning Template matching into implicit coercion.

Required direction:

- missing-only defaults are explicit and deterministic
- present invalid values do not silently fall back to defaults
- normalization/conversion remains an ordinary explicit transformation
- Template matching itself remains non-coercive
- original-value preservation rules are explicit when validation-only matching is used

### 3. Rich validation diagnostics and accumulation

Add a principled way to report more than the first structural validation failure when the caller requests accumulated diagnostics.

Candidate capabilities:

- field/index/path-aware validation diagnostics
- nested diagnostic paths
- multiple independent validation errors from one value
- preservation of the `some` / `none` / `err` distinction
- deterministic diagnostic ordering
- composition with existing Outcome-aware pipeline diagnostics

This must not replace ordinary first-match pattern semantics. Accumulating validation is an explicit validation operation, not a hidden change to pattern matching.

### 4. Template → JSON Schema generation

Complement R9's implemented JSON Schema → Template direction with a deliberately bounded reverse mapping for Templates that have a faithful JSON Schema representation.

Goals:

- generate JSON Schema from supported structural/refinement Templates
- reject or explicitly mark Template behavior that cannot be represented faithfully
- preserve the distinction between Genia Templates and JSON Schema
- support HTTP/API contracts, AI structured-output contracts, tooling, and external integration without making JSON Schema the language's type system

Round-tripping must only be claimed for the explicitly supported subset.
Callable refinements, transformations, and opaque Templates that cannot be
represented faithfully must fail schema generation explicitly; R15 must not
emit an approximation that accepts different values from the source Template.

### 5. Structural discriminated alternatives

Promote only the validation-oriented part of the later-release variant work
deferred from R9. R15 alternatives are structurally discriminated ordinary
values, not a new nominal value category.

Goals:

- closed named alternatives selected by an explicit discriminator field
- ordinary value payloads
- pattern-matchable alternative Templates over the unchanged ordinary value
- deterministic validation of discriminated structured alternatives
- JSON Schema interoperability where representable

General nominal variant identity, constructors, and exhaustiveness checking
remain deferred. R15 should reclassify only the structural-validation portion
of issue #92 rather than silently absorbing that issue's broader language-design
questions.

### 6. Bounded recursive Template references

Design and implement safe named Template references for recursive tree-shaped
ordinary data where practical.

Examples include trees, nested document structures, recursive API payloads, and recursive JSON Schema definitions within the approved subset.

Requirements:

- explicit named-reference resolution semantics
- deterministic unresolved-reference diagnostics
- bounded recursion with deterministic limit diagnostics
- clear failure diagnostics
- no hidden nominal object graph model
- no requirement that ordinary recursive data become model instances

R15 does not promise arbitrary cyclic runtime object graphs or unrestricted
mutual recursion. Those capabilities require separate evidence and approval if
the bounded proving cases do not require them.

## Architectural rules

- R15 extends R9; it does not create a second validation framework.
- Values remain ordinary Genia values after validation unless an existing representation boundary explicitly says otherwise.
- Templates remain ordinary callable Outcome matchers/validators according to the approved contract.
- Pattern matching remains the core conditional model.
- Validation does not imply mutation or allocation of model-wrapper objects.
- No implicit broad coercion. Any conversion/normalization must be explicit and composable.
- Outcome remains the failure/absence carrier; do not invent a parallel validation-result hierarchy.
- JSON Schema is an interoperability representation/contract source, not Genia's semantic authority.
- New behavior must update and preserve `docs/design/composability-matrix.md` where Template/representation composition changes.
- Template descriptions are inert structure, not a second Template identity or
  an authority that may execute effects.

## Explicit non-goals

- a `BaseModel` equivalent
- Python/Pydantic API compatibility
- nominal class-based models
- inheritance or a nominal type hierarchy
- broad automatic coercion such as string-to-number conversion during matching
- mutable model instances
- decorator-heavy validator lifecycle machinery
- Python-specific dataclass integration
- a full static type system
- support for every JSON Schema keyword
- arbitrary code generation from schemas
- approximate or best-effort Template-to-schema generation
- nominal variant objects, constructors, or exhaustiveness checking
- arbitrary cyclic object-graph validation
- unrestricted mutual recursion
- replacing R9 Templates, Outcomes, representations, or patterns

## Proving cases

R15 should prove the release through a small set of end-to-end cases rather than a broad compatibility matrix.

Recommended proving cases:

1. **Messy external record**
   - decode JSON
   - apply explicit normalization/defaults
   - validate nested structure
   - collect multiple field diagnostics
   - preserve an ordinary Genia value on success

2. **Schema interchange**
   - define a supported Genia Template
   - generate JSON Schema
   - use that schema at an external/AI/API boundary
   - validate returned data with the original Template

3. **Structural alternative**
   - validate and pattern-match an ordinary map discriminated by a field such as
     `"kind"`, without constructing a nominal variant value

4. **Recursive data**
   - validate a tree/document through bounded named Template references with
     useful path diagnostics

## Critical acceptance criterion

A real Genia application can take a messy nested external value, explicitly
normalize it, apply missing-only defaults, report every independent validation
problem through deterministic paths, and retain an ordinary Genia value on
success. It can expose a faithful JSON Schema when its inspectable Template is
representable, validate structurally discriminated alternatives, and validate a
bounded recursive tree through named Template references—all without model
instances, implicit coercion, nominal variants, or a second validation-result
system.

## Recommended release slices

1. **E15-0 — contract, roadmap reconciliation, and capability inventory**
2. **E15-1 — inert inspectable Template descriptions**
3. **E15-2 — explicit missing-field defaults and normalization composition**
4. **E15-3 — accumulated path-aware validation diagnostics**
5. **E15-4 — faithful supported Template → JSON Schema generation**
6. **E15-5 — structural discriminated alternatives**
7. **E15-6 — bounded named recursive Template references**
8. **E15-7 — composed messy-record validated-data proving case**
9. **E15-8 — cross-mode/shared-conformance and portability hardening**
10. **E15-9 — documentation, release examples, composability sync, final
    truth audit, and distillation**

The exact issue breakdown must be created through `docs/process/08-roadmap-ticketing.md` when R15 ticketing is explicitly requested.

## Dependency / sequencing note

R15 depends semantically on the completed R9 Template/representation foundation. It may also consume later R11/R14 capabilities in proving examples, but those are not required to define R15's validation semantics.

Recommended roadmap placement:

```text
R14 — Composable HTTP Lifecycles
 |
 v
R15 — Validated Value Modeling
```

This sequence is planning order, not a claim that R15 technically depends on all of R10–R14.

## Parking-lot promotion

R15 promotes the following previously deferred directions into planned release scope:

- value-template work outside R9 that is specifically needed for richer validation
- the structural-discrimination portion of variant work deferred from R9 /
  issue #92; nominal variants and exhaustiveness remain deferred
- bounded named recursive Template validation
- richer validation diagnostics when explicit accumulation is requested
- Template → JSON Schema interchange

Broad contracts, a general validation DSL, nominal structs/classes, and unrelated type-system work remain outside R15 unless separately approved.
