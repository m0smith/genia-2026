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

### 1. Defaults and explicit normalization

Define how missing fields may receive explicit defaults and how normalization may be composed with validation without turning Template matching into implicit coercion.

Required direction:

- missing-only defaults are explicit and deterministic
- present invalid values do not silently fall back to defaults
- normalization/conversion remains an ordinary explicit transformation
- Template matching itself remains non-coercive
- original-value preservation rules are explicit when validation-only matching is used

### 2. Rich validation diagnostics and accumulation

Add a principled way to report more than the first structural validation failure when the caller requests accumulated diagnostics.

Candidate capabilities:

- field/index/path-aware validation diagnostics
- nested diagnostic paths
- multiple independent validation errors from one value
- preservation of the `some` / `none` / `err` distinction
- deterministic diagnostic ordering
- composition with existing Outcome-aware pipeline diagnostics

This must not replace ordinary first-match pattern semantics. Accumulating validation is an explicit validation operation, not a hidden change to pattern matching.

### 3. Template → JSON Schema generation

Complement R9's implemented JSON Schema → Template direction with a deliberately bounded reverse mapping for Templates that have a faithful JSON Schema representation.

Goals:

- generate JSON Schema from supported structural/refinement Templates
- reject or explicitly mark Template behavior that cannot be represented faithfully
- preserve the distinction between Genia Templates and JSON Schema
- support HTTP/API contracts, AI structured-output contracts, tooling, and external integration without making JSON Schema the language's type system

Round-tripping must only be claimed for the explicitly supported subset.

### 4. Closed variants / discriminated alternatives

Promote the later-release variant work deferred from R9 into an R15 candidate, but only as a coherent extension of Templates and patterns.

Goals:

- closed named alternatives
- ordinary value payloads
- pattern-matchable variant identity
- deterministic validation of discriminated structured alternatives
- JSON Schema interoperability where representable

This should absorb/reclassify the intent behind issue #92 rather than creating a competing variant mechanism.

### 5. Recursive Templates

Design and implement safe recursive validation for self-referential and mutually recursive data structures where practical.

Examples include trees, nested document structures, recursive API payloads, and recursive JSON Schema definitions within the approved subset.

Requirements:

- explicit recursion semantics
- cycle/recursion guards where needed
- clear failure diagnostics
- no hidden nominal object graph model
- no requirement that ordinary recursive data become model instances

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

3. **Closed alternative**
   - validate and pattern-match a discriminated union such as success/error or event variants

4. **Recursive data**
   - validate a bounded recursive tree/document shape with useful path diagnostics

## Critical acceptance criterion

A real Genia application can validate complex external structured data with explicit defaults/normalization, rich path-aware diagnostics, closed alternatives, and recursive structures; expose a faithful JSON Schema when the Template is representable; and do all of this while retaining ordinary Genia values, Outcomes, Templates, and patterns rather than introducing model classes or implicit coercion.

## Recommended release slices

1. **E15-0 — contract and roadmap alignment**
2. **E15-1 — explicit defaults and normalization composition**
3. **E15-2 — accumulated path-aware validation diagnostics**
4. **E15-3 — supported Template → JSON Schema generation**
5. **E15-4 — closed variant identity and discriminated alternatives**
6. **E15-5 — recursive Template support**
7. **E15-6 — composed validated-data proving case**
8. **E15-7 — cross-mode/shared-conformance hardening**
9. **E15-8 — documentation, release examples, and composability sync**
10. **E15-9 — final truth audit and distillation**

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
- closed variant work deferred from R9 / issue #92
- recursive Template validation
- richer validation diagnostics when explicit accumulation is requested
- Template → JSON Schema interchange

Broad contracts, a general validation DSL, nominal structs/classes, and unrelated type-system work remain outside R15 unless separately approved.