# R15 Validated Value Modeling Contract

Status: **E15-0 contract candidate — no R15 runtime behavior is implemented by this document.**

Issue: #726
Parent epic: #725

`GENIA_STATE.md` remains final authority for implemented behavior. This contract
constrains later R15 slices only. It does not make any R15 behavior current merely
because the roadmap, issues, or this file exist.

## Purpose

R15 extends the completed R9 Value Template / representation model into a more
practical validated-value toolset for Genia's Outcome-aware validated data
pipelines while preserving the existing value-first and pattern-first model.

R15 must not create a second type system, a `BaseModel`-style object model, a
parallel validation result hierarchy, implicit broad coercion, nominal variants,
or ambient validation state.

The intended product path is:

```text
messy external values
  -> explicit decode / normalization
  -> explicit missing-only defaults
  -> Template validation
  -> optional accumulated diagnostics
  -> ordinary validated values
  -> faithful external schema when representable
```

## Existing capability inventory

R15 begins from these already-implemented boundaries.

### R9 — Templates, structural matching, representations, JSON, and schema input

R9 is authoritative for the Template and representation model:

- a Template is an ordinary one-argument callable matcher returning
  `some(...)`, `none(...)`, or `err(...)`;
- named Templates remain ordinary first-class callable values, not a nominal
  runtime category;
- `refinement_match(predicate, value)` lifts a boolean predicate into Outcome
  matching;
- `open_shape_match(fields, value)` requires listed fields, permits extras, and
  preserves the original complete map on success;
- `exact_shape_match(fields, value)` requires equal key sets and preserves the
  original map;
- `@?`, `@!`, and `&` retain their existing original-subject and left-to-right
  short-circuit semantics;
- represented values use ordered carrier facets; transport preserves the same
  represented value while derived values do not inherit facets implicitly;
- JSON decode/encode uses ordinary Genia values plus the `json` facet rather
  than a parallel JSON object model;
- the implemented `json_schema` direction compiles a deliberately closed JSON
  Schema structural subset into ordinary callable Outcome Templates and rejects
  unsupported keywords explicitly;
- R9 explicitly left Template metadata unimplemented but allowed future inert
  metadata that cannot affect callability, identity, matching, or composition.

R15 therefore extends the R9 Template model. It does not replace it.

### R10 — defaults/conversion boundary and protected values

R10 is authoritative for configuration-boundary missing/default/converter/
Template behavior and for protected values:

- configuration defaults are missing-only;
- conversion is explicit and precedes Template validation at that boundary;
- protected carriers cannot be generically stripped, matched, serialized, or
  rendered in a way that reveals their payload;
- protected sinks reject recursively unless explicitly authorized;
- declassification is authority-gated and is the only payload-revealing
  operation.

R15 field defaults and validation metadata must preserve these laws. R15 does
not create a second protected-value mechanism or a new route to declassification.

### R13 — explicit configuration resolution

R13 is authoritative for explicit provider/view construction and immutable
configuration snapshots. R15 descriptions, defaults, validators, schema
inspection, and recursive-reference resolution must not acquire configuration,
look up process state, or create dependency-injection behavior.

### R14 — explicit lifecycle context and bounded repeated work

R14 is authoritative for execution scopes, lifecycle context, repeated element
scopes, and Flow finalization. R15 validation state is not lifecycle state.
Template inspection and recursive-reference resolution must not consult
lifecycle context. Any R15 operation used over Flow must preserve existing lazy,
single-use, bounded-demand, no-over-pull, and finalization rules.

## Global invariants

Every R15 slice must preserve all of the following:

1. **Ordinary values remain ordinary values.** Successful validation does not
   allocate a model wrapper or nominal instance.
2. **Templates remain ordinary one-argument Outcome callables.** Metadata is not
   a new Template identity.
3. **Pattern semantics do not change.** Named patterns, `@?`, `@!`, `&`, case-arm
   ordering, and first-match dispatch retain their current behavior.
4. **No implicit broad coercion.** Conversion/normalization is explicit ordinary
   composition.
5. **Outcome remains the result vocabulary.** R15 adds no `ValidationResult`,
   exception hierarchy, or parallel failure family.
6. **Protected payloads remain opaque.** No R15 description, default metadata,
   diagnostic, schema, recursion context, or rendering path may reveal them.
7. **No ambient state.** Template descriptions, validation, defaults, schema
   generation, alternatives, and recursive references do not acquire config,
   lifecycle state, process state, network resources, or IO implicitly.
8. **No hidden eager Flow behavior.** Accumulation is bounded to the value being
   validated; R15 must not turn a Flow source into an implicit whole-stream
   validation buffer.
9. **Schema is interoperability, not authority.** JSON Schema never becomes the
   language's type system.
10. **Exact-or-fail interoperability.** R15 does not publish approximations that
    accept or transform a different set of values than the source Template.
11. **No Core IR expansion by default.** The approved direction uses existing
    values, calls, patterns, and portable data. Any proposed parser/AST/Core IR
    change is a separate hard stop requiring explicit approval.

## E15-1 — Inert inspectable Template descriptions

### Contract

R15 may attach an immutable, inert description to Templates produced by
explicitly supported Template-building facilities.

A description is ordinary, host-independent data describing only portable
validation structure. It must not contain Python closure internals, object IDs,
host class names, source-code reflection, live providers, lifecycle handles, or
other executable capability.

The initial inspectability boundary is:

- **inspectable:** Templates whose portable structure is known because they are
  constructed by an R15-supported structural Template builder or by the existing
  R9 `json_schema` compiler from the supported schema subset;
- **opaque leaf permitted:** a callable refinement may be represented only as an
  explicitly opaque refinement leaf. Its predicate is never introspected or
  executed by inspection;
- **opaque Template:** arbitrary one-argument Outcome callables and named
  patterns whose portable structure was not produced through a supported
  builder remain fully valid Templates but have no inspectable description.

Operations that require inspection must fail deterministically for an opaque
Template rather than guessing from host implementation details.

Descriptions do not participate in equality, hashing, callable identity,
pattern identity, matching, dispatch, or original-subject semantics. Two
Templates with equal descriptions are not thereby the same Template.

Description construction and inspection are effect-free. They perform no
validation of user data, no arbitrary callable execution, no config/lifecycle
lookup, no filesystem/network IO, and no import-time activation.

Exact public construction/inspection call shapes belong to E15-1 design and
must satisfy this boundary.

## E15-2 — Missing-only defaults and explicit normalization

### Contract

R15 field defaults are explicit and apply only when a supported structural
Template determines that the field is absent.

- A missing field may select its declared default exactly once.
- A present field, including `nil`, never selects a missing-field default merely
  because its value fails validation.
- A present invalid value is validated and fails normally.
- Default application precedes validation of the resulting field value.
- Applying a default produces an ordinary value transformation; the enclosing
  successful result remains an ordinary Genia value rather than a model.
- Normalization/conversion is an explicit ordinary callable/value pipeline step
  and is not performed implicitly by Template matching.

A default value may itself be any value otherwise legal at that point,
including a represented or protected value. Existing representation/protection
semantics remain authoritative. A Template description may record that a default
exists, and may retain the default as an ordinary value only without stripping
or declassifying it. Generic rendering/serialization remains subject to R10
protected-value rejection/opacity rules.

A protected payload must never be copied into a plain description field,
diagnostic string/context, or emitted schema.

### Schema consequence

A Template whose semantics materially include default insertion or an explicit
normalization/transformation is **not** faithfully representable by ordinary
JSON Schema validation alone. The initial R15 Template-to-schema direction must
therefore reject such behavior unless a later separately contracted mapping can
prove equivalent validation and output semantics. JSON Schema's `default`
annotation is not treated as an insertion operation.

## E15-3 — Explicit accumulated diagnostics

### Contract

Accumulation is a separate explicit validation operation over an inspectable
Template. It does not alter ordinary Template invocation or pattern dispatch.

The operation traverses only the finite structural value requested for that one
validation call. It does not implicitly enumerate an enclosing Flow or Seq.

On success it returns `some(original_or_explicitly_normalized_value)` according
to the preceding explicit composition. It never substitutes a model wrapper.

When independent validation failures are accumulated, the operation returns the
existing `err(...)` Outcome family with deterministic validation context. Each
diagnostic entry preserves whether the underlying observation was an ordinary
mismatch (`none`) or a recoverable matcher/validation error (`err`) rather than
collapsing the distinction into a new result type.

The portable diagnostic entry contains only contracted, non-sensitive data such
as:

- a path made of field-name and list-index segments;
- a stable validation category/kind;
- the underlying mismatch-versus-error classification;
- an approved stable reason identifier/message where the owning Template
  contract exposes one.

It must not include raw host exception text, arbitrary subject rendering,
protected payloads, configuration keys/source contents, lifecycle state, or
closure details.

### Deterministic order

Diagnostics are ordered by deterministic structural traversal:

1. map fields follow the Template specification/description order;
2. list elements follow increasing zero-based index order;
3. nested diagnostics appear depth-first within the field/index that owns them;
4. structural missing/extra-field diagnostics follow the ordering already
   contracted by the applicable R9 structural Template where that rule exists;
5. recoverable child `err(...)` observations occupy the same position the child
   validation occupies; they do not reorder later independent diagnostics.

E15-3 may tighten exact reason/category names in its own design, but it must not
change the ordering rules above.

### Flow boundary

R15 accumulation is per validated value. Using it in `map`, `validate_each`, or
other ordinary pipeline composition consumes only the elements demanded by the
existing caller. No R15 helper may pre-consume, cache, or buffer the remainder
of a lazy Flow merely to accumulate validation failures across records.

A separate whole-dataset diagnostic aggregation, if ever desired, remains
ordinary explicit pipeline reduction/collection and is outside the Template
matcher itself.

## E15-4 — Faithful Template to JSON Schema generation

### Contract

R15 may generate JSON Schema only from inspectable Template descriptions whose
validation semantics have an explicitly faithful JSON Schema representation.

Generation is pure inspection. It never invokes the Template against sample
values and never executes callable refinements or transformations.

The initial supported reverse-mapping subset may include only structural nodes
whose equivalence is proven by E15-4 tests. At minimum, the E15-4 design must
state a closed supported node/keyword table. Anything not in that table fails
with a deterministic unsupported result.

Explicitly unsupported unless a later contract proves an exact mapping:

- arbitrary/opaque callable Templates;
- callable refinement predicates whose semantics cannot be represented exactly;
- normalization or transformation steps;
- default insertion semantics;
- host-specific metadata;
- protected payload-bearing metadata;
- arbitrary custom diagnostic behavior;
- schema features outside the approved closed subset.

Emitted schema must never reveal a protected payload. If faithful generation
would require such a payload, generation fails rather than declassifying,
redacting into a semantically different schema, or silently dropping a
validation constraint.

Round-trip claims are limited to the tested faithful subset. A claim means the
original Template and the generated-schema-derived Template accept/mismatch/error
consistently for the contracted validation domain; it does not imply Template
identity or preservation of non-schema metadata.

## E15-5 — Structural discriminated alternatives

### Contract

R15 alternatives are ordinary structured values selected by an explicit
discriminator. They are not nominal variants.

A supported alternative description contains:

- one explicit discriminator field name;
- a closed mapping from allowed discriminator values to branch Templates;
- ordinary branch Templates governed by the same inspectable/opaque rules.

The E15-5 design must choose a closed portable discriminator-value domain. The
preferred initial domain is string discriminator values because it maps cleanly
to JSON object payloads and deterministic map lookup; broadening the domain
requires explicit justification.

Validation proceeds in this order:

1. validate that the subject has the structural form required to read the
   discriminator;
2. read the discriminator exactly once;
3. resolve exactly one branch from the closed alternatives map;
4. validate only that branch.

Missing, malformed, or unknown discriminator values produce deterministic
path-aware validation diagnostics in the explicit accumulated-validation path.
Ordinary Template invocation retains the R9 `some`/`none`/`err` and pattern
semantics defined by the final E15-5 design.

R15 does not try every branch and pick whichever happens to succeed. It does not
infer a branch from payload shape when the discriminator is absent or invalid.

Successful values remain the original ordinary map/value (subject to any
explicit normalization/default step that happened before validation).

JSON Schema interoperability is permitted only where E15-4 can express the
closed discriminator-directed alternatives faithfully. If it cannot, schema
generation fails explicitly.

### Issue #92 disposition

R15 absorbs only this structural-validation use case from #92. The following
remain deferred beyond R15:

- nominal variant identity;
- variant constructor objects/syntax;
- sealed/closed nominal hierarchies;
- exhaustiveness checking;
- changing `case` or pattern dispatch to know a nominal ADT universe.

## E15-6 — Bounded named recursive Template references

### Contract

R15 may support recursive validation of ordinary tree-shaped data through
explicit named Template references.

Reference resolution is owned by an explicit Template-construction or validation
boundary. It is never a mutable process-global registry and never comes from
configuration, lifecycle context, imports discovered at runtime, or dependency
injection.

The initial R15 recursive subset is deliberately narrow:

- a recursive Template environment is explicit and immutable for one constructed
  Template/validation boundary;
- named references resolve only within that environment;
- self-recursive tree definitions are supported when E15-6 lands;
- unrestricted mutual recursion is not promised by R15 and requires separate
  evidence/approval if later needed;
- ordinary runtime object cycles are outside scope; the subject is validated as
  tree-shaped ordinary data.

Every recursive environment has an explicit positive recursion/depth bound as
part of its construction/validation contract. R15 does not rely on Python's
recursion limit and does not silently choose an unbounded traversal.

An unresolved name fails deterministically before or at the first attempted
resolution according to the E15-6 design. Exceeding the explicit bound returns a
deterministic path-aware validation failure. Raw host recursion exceptions must
not cross the portable boundary.

Recursive inspection/schema generation follows the same exact-or-fail and
protected-value rules as all other R15 metadata.

## Portability posture

R15 semantics are intended to be host-independent. Python may choose host-local
storage for Template descriptions and efficient validation traversal, but the
following are portable observations:

- whether a Template is inspectable or opaque;
- the portable description structure for supported nodes;
- missing-only default selection;
- absence of implicit normalization/coercion;
- accumulated diagnostic paths/order/categories;
- discriminator-directed branch selection;
- recursive-reference resolution and explicit bound behavior;
- exact-or-fail schema support;
- protected-value opacity;
- preservation of ordinary Pattern/Outcome/Flow semantics.

Shared conformance belongs to the later E15-8 hardening slice where the current
spec runner can express the behavior. This contract itself adds no shared spec
case and no second host.

## Expected issue sequence

The approved dependency order after E15-0 is:

1. **#728 — E15-1:** inert inspectable Template descriptions
2. **#729 — E15-2:** explicit missing-field defaults and normalization composition
3. **#730 — E15-3:** accumulated path-aware validation diagnostics
4. **#731 — E15-4:** faithful supported Template to JSON Schema generation
5. **#732 — E15-5:** structural discriminated alternatives
6. **#733 — E15-6:** bounded named recursive Template references
7. **#734 — E15-7:** composed messy-record validated-data proving case
8. **#735 — E15-8:** cross-mode/shared-conformance and portability hardening
9. **#736 — E15-9:** documentation, release examples, composability sync, final truth audit, and distillation

Each issue must run its own repository process. An earlier issue being merged does
not waive the later issue's preflight/design/test/documentation/audit gates.

## Non-goals

R15 explicitly excludes:

- `BaseModel` or model-instance semantics;
- Python/Pydantic API compatibility;
- nominal classes/structs or inheritance;
- broad automatic coercion during matching;
- mutable validated models;
- decorator-driven validator lifecycle systems;
- a new static type system;
- a general validation DSL;
- a parallel validation-result hierarchy;
- complete JSON Schema support;
- approximate/best-effort schema generation;
- host closure introspection;
- ambient configuration lookup;
- lifecycle-owned validation/reference state;
- nominal ADT variants, constructors, or exhaustiveness;
- arbitrary cyclic object-graph validation;
- unrestricted mutual recursion;
- changing existing pattern dispatch, Outcome semantics, or Flow consumption.

## Documentation rule

E15-0 may update strategy/roadmap/design documentation to record R15 as the
active release and to constrain planned behavior. It must **not** update
`GENIA_STATE.md`, `GENIA_RULES.md`, `GENIA_REPL_README.md`, or `README.md` to
claim any new R15 runtime behavior.

As each later behavior slice lands, that issue is responsible for updating every
implemented-truth surface legitimately affected by its tested implementation,
including the composability matrix and release documentation when appropriate.

## E15-0 authorization boundary

If #726 is reviewed and approved, the next authorized work item is **#728 / E15-1
preflight only**.

No E15-2+ implementation is authorized merely because those issues exist.
