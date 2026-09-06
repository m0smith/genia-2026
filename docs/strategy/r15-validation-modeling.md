# R15 — Validated Value Modeling

Status: **Active release planning — E15-0 contract gate is in review.** This document is non-authoritative and does not define implemented language behavior.

`GENIA_STATE.md` remains final authority for implemented behavior. No R15 runtime behavior is implemented merely because this strategy, the roadmap, issues, or the E15-0 contract exist.

Tracking:

- Epic: #725
- E15-0 contract/roadmap/capability gate: #726
- Contract candidate: `docs/design/r15-validated-value-modeling-contract.md`
- Kickoff guidance: `docs/strategy/r15-kickoff.md`

## Theme

> Extend R9 Value Templates into a practical, Pydantic-class validation toolset for Genia's Outcome-aware validated data pipelines without introducing model classes, implicit coercion, or a second type/validation system.

R15 directly continues the completed R9 Value Templates & Representations foundation. Genia already has much of the validation core commonly associated with Pydantic through refinements, open/exact structural Templates, nested matching, strict JSON, JSON Schema-derived Templates, Outcomes, and strict/no-coercion semantics.

The goal is not Pydantic compatibility. The goal is to close the highest-value gaps for real validated-data workflows while preserving Genia's value-first, pattern-first model.

## Product fit

R15 directly strengthens Genia's first killer workflow:

```text
messy records in
  → decode / explicitly normalize
  → apply explicit missing-only defaults
  → validate with Templates
  → explicitly accumulate useful diagnostics when requested
  → produce ordinary validated values
  → emit / serialize / expose faithful schema when representable
```

## Inherited boundaries

R15 must preserve the completed releases it builds on:

- **R9:** Templates remain ordinary one-argument Outcome callables; named patterns, `@?`, `@!`, `&`, open/exact shape matching, representations, strict JSON, and JSON Schema → Template semantics remain authoritative.
- **R10:** missing/default/converter behavior at the configuration boundary and protected-value opacity/sinks/declassification remain authoritative. R15 must not reveal protected payloads through descriptions, defaults, diagnostics, or schema.
- **R13:** configuration/provider acquisition remains explicit. Template inspection, validation, and recursive-reference resolution must not become ambient configuration lookup or dependency injection.
- **R14:** lifecycle context remains explicit scoped execution state rather than mutable lexical/application state. Validation metadata and recursive references must not use lifecycle state, and lazy Flow callers must preserve bounded demand, no-over-pull, single-use, and finalization behavior.

## Approved E15-0 direction

The E15-0 contract candidate resolves the future-regret questions as follows. These are constraints on later work, not implemented behavior.

### 1. Inert, inspectable Template descriptions

Supported R15 Template builders and the existing R9 `json_schema` compiler may produce immutable host-independent description data. Arbitrary callable Templates remain valid but opaque. Callable refinements may only appear as explicit opaque leaves; inspection never introspects or executes their predicates.

Descriptions do not affect callability, identity, equality, matching, dispatch, or original-subject behavior. Inspection performs no IO, config/lifecycle lookup, process-state acquisition, or import-time activation.

### 2. Defaults and explicit normalization

Defaults are explicit and missing-only. Present invalid values do not silently fall back to defaults. Default application is an ordinary value transformation and normalization/conversion remains an explicit ordinary transformation before validation; Template matching itself stays non-coercive.

Defaults may be ordinary, represented, or protected values where otherwise legal, but no protected payload may be copied into plain metadata, diagnostics, or emitted schema.

Because JSON Schema `default` is an annotation rather than an insertion transform, Templates whose semantics materially include default insertion or normalization are outside the initial faithful Template → JSON Schema subset.

### 3. Rich accumulated diagnostics

Accumulation is a separate explicit validation operation over one finite value. It does not change named-pattern, `@?`, `@!`, `&`, case-arm, or first-match semantics.

Diagnostics use deterministic field/index paths and deterministic structural traversal order, preserve whether a child observation was `none` versus `err`, and return through the existing Outcome vocabulary rather than a new validation-result hierarchy.

Accumulation is per validated value. It must not implicitly consume or buffer an enclosing Flow. Dataset-wide aggregation remains ordinary explicit pipeline composition.

### 4. Template → JSON Schema generation

Generation is faithful for a declared closed subset or fails explicitly. It never executes arbitrary callable refinements or transformations. Opaque Templates, unrepresentable refinements/transforms/default insertion, host metadata, and any constraint requiring protected data are unsupported rather than approximated.

Round-trip claims apply only to the tested faithful subset and do not imply Template identity or preservation of non-schema metadata.

### 5. Structural discriminated alternatives

R15 promotes only the validation-oriented part of issue #92. Alternatives are ordinary structured values selected by one explicit discriminator field and a closed branch map. After reading the discriminator exactly once, validation chooses exactly one branch; it does not try every branch and pick a successful one or infer a branch from payload shape.

Nominal variant identity, constructors, sealed hierarchies, and exhaustiveness remain deferred beyond R15.

### 6. Bounded recursive Template references

Recursive references use an explicit immutable Template-construction/validation environment. Resolution never comes from a mutable global registry, configuration, lifecycle context, or ambient import state.

R15 initially targets self-recursive tree-shaped ordinary data with an explicit positive recursion/depth bound. Unresolved names and bound exhaustion fail deterministically with useful paths. Arbitrary cyclic runtime object graphs and unrestricted mutual recursion remain excluded.

## Architectural rules

- R15 extends R9; it does not create a second validation framework.
- Values remain ordinary Genia values after validation unless an existing representation boundary explicitly says otherwise.
- Templates remain ordinary callable Outcome matchers/validators.
- Pattern matching remains the core conditional model and its existing semantics remain unchanged.
- Validation does not imply mutation or allocation of model-wrapper objects.
- No implicit broad coercion. Conversion/normalization is explicit and composable.
- Outcome remains the failure/absence carrier; do not invent a parallel validation-result hierarchy.
- JSON Schema is an interoperability representation/contract, not Genia's semantic authority.
- Template descriptions are inert structure, not a second Template identity or executable authority.
- Protected values remain opaque through every R15 metadata/diagnostic/schema path.
- Validation state is neither configuration state nor lifecycle state.
- No new parser/AST/Core IR node is approved by E15-0; any proposal for one is a separate hard stop.
- `docs/design/composability-matrix.md` must be updated as each implemented R15 slice changes proven composition.

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
- a mutable/global Template registry
- lifecycle-owned or configuration-owned validation state
- replacing R9 Templates, Outcomes, representations, or patterns

## Proving cases

1. **Messy external record** — decode JSON, explicitly normalize, apply missing-only defaults, validate nested structure, collect multiple field diagnostics, and retain an ordinary value on success.
2. **Schema interchange** — define a supported inspectable Template, generate faithful JSON Schema, use it at an external/API/AI boundary, and validate returned data with the original Template.
3. **Structural alternative** — validate and pattern-match an ordinary map discriminated by a field such as `"kind"`, without constructing a nominal variant.
4. **Recursive data** — validate a tree/document through bounded named Template references with useful path diagnostics.

## Critical acceptance criterion

A real Genia application can take a messy nested external value, explicitly normalize it, apply missing-only defaults, report every independent validation problem through deterministic paths, and retain an ordinary Genia value on success. It can expose faithful JSON Schema when its inspectable Template is representable, validate structurally discriminated alternatives, and validate a bounded recursive tree through named Template references—all without model instances, implicit coercion, nominal variants, ambient state, or a second validation-result system.

## Approved issue sequence

E15-0 defines the contract and creates the ordered release slices. Existence of a later ticket does not authorize skipping its own process gates.

1. **#726 — E15-0:** contract, roadmap reconciliation, and capability inventory
2. **#728 — E15-1:** inert inspectable Template descriptions
3. **#729 — E15-2:** explicit missing-field defaults and normalization composition
4. **#730 — E15-3:** accumulated path-aware validation diagnostics
5. **#731 — E15-4:** faithful supported Template → JSON Schema generation
6. **#732 — E15-5:** structural discriminated alternatives
7. **#733 — E15-6:** bounded named recursive Template references
8. **#734 — E15-7:** composed messy-record validated-data proving case
9. **#735 — E15-8:** cross-mode/shared-conformance and portability hardening
10. **#736 — E15-9:** documentation, release examples, composability sync, final truth audit, and distillation

Recommended dependency shape:

```text
#726 → #728 → #729 → #730 → #731 → #732 → #733 → #734 → #735 → #736
```

This deliberately favors a simple release spine. If a later preflight proves two slices can safely proceed independently, that may optimize scheduling but must not weaken their dependency on the semantics they consume.

## Dependency / sequencing note

R15 depends semantically on the completed R9 Template/representation foundation. It also must preserve R10 protected-value rules and the explicit state boundaries proven by R13/R14. It may consume R11/R14 capabilities in proving examples but does not define its validation semantics in terms of AI, HTTP, or lifecycle execution.

Recommended roadmap placement remains:

```text
R14 — Composable Lifecycles ✓ COMPLETE
 |
 v
R15 — Validated Value Modeling ← ACTIVE CONTRACT GATE
 |
 v
R16 — Multi-Host Spec Runner
```

## Issue #92 disposition

R15 reclassifies only structural discriminator-directed validation into #732. Issue #92's nominal ADT identity, constructors, sealed/closed nominal hierarchy questions, and exhaustiveness remain deferred and must not be closed as fully delivered by R15.

## E15-0 stop condition

E15-0 adds no runtime behavior. Once #726 is reviewed and merged, the next authorized work item is **#728 / E15-1 preflight only**. Every subsequent issue runs its own normal preflight, contract/design reconciliation where needed, failing-test, implementation, documentation, audit, and distillation gates.
