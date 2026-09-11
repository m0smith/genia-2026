# R18 Portable Value Equality Contract

Status: **Approved, implemented, documented, and audited — E18-0 through E18-7 (#790–#797). The E18-7 skeptical release audit recorded a PASS verdict.** This document is a design aid and does not define current language truth on its own. `GENIA_STATE.md` remains final authority for implemented behavior, and `docs/releases/R18.md` is the release summary.

The "Later release slices" and "E18-0 gate" sections below are retained as the historical approved plan; they described work that has since landed.

Epic: #789  
E18-0 gate: #790

R18 follows the completed R17 numeric/ordered-map portability contract. R17 deliberately left map `==` unresolved; R18 defines the portable equality/key model before later portability work and a second host depend on Python behavior.

---

## Purpose

Genia has one semantic equality relation:

```genia
a == b
```

`==` is host-independent and permanently non-user-overloadable. `a != b` is exactly the logical negation of `a == b`.

Any Genia surface that asks whether two values are the same must use this relation unless it is an explicitly named domain-specific predicate. Literal patterns, duplicate pattern bindings, native `assert_eq`, and map-key identity do not get separate equality rules.

---

## Equality families

Every Genia value that participates in equality belongs to one of four operational families.

### Structural values

Structural values compare recursively by semantic contents. Current R18 structural families are:

- booleans, integers, floats, strings, symbols
- Lists and Pairs
- `some`, `none`, and `err` Outcomes
- maps
- represented values
- deterministic RNG state values
- Format values
- byte values and ZIP-entry values
- Sheets
- inert closed ordinary operation/data descriptors whose existing public contract defines them solely by immutable fields

Structural comparison names semantic fields explicitly; adding a Python dataclass field must not silently change Genia equality.

An identity-bearing, opaque-token, or protected value nested inside a structural value is a terminal leaf. Equality never follows runtime state behind such a leaf.

### Identity-bearing runtime values

Identity-bearing values compare only by logical runtime entity identity. Equivalent visible state/configuration does not imply equality.

This family includes current functions/function groups, host/native callables, named pattern/Template matcher values, model callables, modules, Refs, Cells, Processes, Seq/Flow values, promises, meta-environments, configuration providers, declassification authorities, model/retrieval providers, retrieval index handles, host/Python handles, IO source/sink handles, and lifecycle values that denote executable/runtime behavior.

Future live Store/execution/actor/job/subscription handles default to this family unless a later approved contract deliberately classifies a new value as an opaque semantic token.

Equality never dereferences or inspects the referenced runtime entity.

### Opaque semantic tokens

Opaque semantic tokens represent immutable semantic facts whose equality is meaningful but whose representation is not public.

Each token has three hidden equality components established before comparison:

1. **domain identity**
2. **provenance identity**
3. **semantic identity**

Two tokens are equal iff all three hidden components are equal.

Token comparison performs no provider/issuer callback, IO, parsing, ordering, user-defined computation, or exposure of those hidden components.

A future storage `Revision` is the motivating example, not a special equality case. Two independently materialized Revision carriers may compare equal when they were minted with the same hidden domain/provenance/semantic identity.

The same equality family is intentionally compatible with future undefined built-in token kinds and future user-defined token domains. That extensibility does **not** make equality extensible: future token facilities may establish the three hidden identities at mint time but may not register comparator code or overload `==`.

R18 adds no public token-domain declaration, token minting API, storage implementation, or `Revision` value.

### Protected carriers

Protected carriers compare by carrier identity only.

Aliases of the same carrier compare equal. Independently acquired carriers compare unequal even if they come from the same provider/purpose and carry equal payloads.

Ordinary equality never compares protected payloads. Payload comparison requires the existing explicit authorized declassification boundary first.

---

## Equality purity

Equality is a pure observation over already-present semantic value/identity data.

It must not:

- perform IO or network access
- acquire configuration, secrets, or resources
- declassify protected values
- invoke functions, Templates, matchers, models, providers, token issuers, or user callbacks
- consume/advance Seq or Flow values
- dereference Refs
- inspect Cell/Process/provider/handle state
- mutate either operand or reachable runtime state

Structural values are well-formed so equality does not need to follow cyclic structural containment. Runtime identity leaves may sit inside wider cyclic object graphs without equality traversing through them.

---

## Numeric equality

Booleans are a distinct semantic kind and never participate in numeric equality with integers/floats.

| Left | Right | Result |
|---|---|---|
| `1` | `1` | true |
| `1` | `2` | false |
| `1` | `1.0` | true when the float exactly denotes the same mathematical integer |
| `1` | `1.5` | false |
| `true` | `1` | false |
| `false` | `0` | false |
| `0.0` | `-0.0` | true |
| `+inf` | `+inf` | true where infinities are supported |
| `+inf` | `-inf` | false |
| `NaN` | anything, including itself | false |

An integer equals a float iff the float is finite, integral, and its exact mathematical integer value equals the Genia integer. A conforming host must not implement this by lossy conversion of an arbitrary-precision integer to a host float.

R17 arbitrary-precision integer semantics remain unchanged.

R18 defines no approximate equality.

---

## Structural rules

### Kind separation

Different semantic kinds are unequal except for the explicit integer/float numeric bridge.

Examples:

- symbol `quote(x)` is not string `"x"`
- represented value is not its unrepresented carried value
- List is not Pair
- boolean is not integer

### Lists and Pairs

Lists require equal length and equal corresponding elements.

Pairs require equal heads and equal tails.

### Outcomes

Outcomes require the same constructor plus equal constructor fields. `some`, `none`, and `err` are never equal across constructor kinds merely because their contents resemble one another.

### Represented values

Represented values require equal facet identity plus equal carried value. Representation layers remain ordered; nesting order and duplicate layers participate in equality. This preserves the existing R9 representation identity contract while replacing host equality of carried values with Genia equality.

### RNG, Format, bytes, ZIP entries, Sheets, inert data descriptors

These compare by their contract-defined immutable semantic contents:

- RNG → deterministic state
- Format → template/tag/composition structure
- bytes → byte sequence
- ZIP entry → name + byte contents
- Sheet → ordered semantic columns/cell values
- inert data descriptors → existing contract-defined fields

No callable/runtime leaf inside an ordinary descriptor is invoked during comparison.

---

## Map equality

Map equality is equality of mappings, not insertion history.

Two maps are equal iff they contain the same number of mappings and every mapping in one has an equal legal key in the other whose mapped value is Genia-equal.

Thus maps with the same mappings may compare equal even when they expose different R17 iteration orders.

R17 remains unchanged: replacement preserves position; removal preserves remaining order; remove-then-reinsert appends; map accessors expose deterministic order.

A map may contain NaN as a **value**. Such a map can therefore be non-reflexive because NaN itself is non-reflexive. R18 requires reflexivity specifically for legal map **keys**, not every possible Genia value.

---

## Legal map keys and key equivalence

R18 preserves the established public keyable surface; it does not promote Python-only internal accommodations into new language values.

Legal public key families are:

- booleans
- integers
- non-NaN floats, including infinities where supported
- strings
- symbols
- recursively legal Pairs
- recursively legal Lists
- represented values whose carried value is recursively legal

Other structural/runtime values are not made legal keys by R18. In particular maps, Outcomes, functions/Templates, providers, authorities, protected values, Refs/Cells/Processes/Seqs/Flows, modules, handles, Sheets, Formats, bytes, ZIP entries, RNG states, and opaque semantic tokens are not newly keyable.

Current Python `_freeze_map_key` support for host tuples/`None` is not authority to introduce a new public tuple/null key kind.

Every legal map key must satisfy:

```text
k == k
```

Therefore NaN is illegal as a key, and any otherwise-keyable structural key containing NaN in an equality-relevant position is illegal.

For legal keys, map key equivalence is exactly Genia `==`:

```text
a == b
=> same lookup entry
=> same replacement target
=> same removal target
=> same duplicate-key identity
```

Unequal legal keys must never collapse because of host-container coercion.

Required examples:

- integer `1` and exactly equal float `1.0` denote the same map key
- `true` and `1` denote different map keys
- `false` and `0` denote different map keys
- `0.0` and `-0.0` denote the same map key

Internal canonicalization/hash representation is private, but equal legal keys must have identical internal key-equivalence/hash treatment. R18 adds no public hash API.

---

## Equality-like surface reconciliation

### Operators

`==` is canonical. `!=` is its negation.

### Literal patterns

A literal pattern matches exactly when literal and candidate are Genia-equal.

### Duplicate bindings

Repeated bindings of the same pattern name are consistent exactly when their candidate values are Genia-equal.

Conceptually, a repeated-binding clause equivalent to `f(x, x)` therefore accepts `(1, 1.0)` and rejects `(true, 1)`.

### Named patterns/Templates

Named matcher invocation remains existing pattern behavior. Comparing matcher/Template values themselves uses identity-bearing equality and never invokes the matcher.

### `assert_eq`

`assert_eq(actual, expected)` succeeds iff `actual == expected`. Existing success/failure structure remains otherwise unchanged; R18 does not add deep-diff diagnostics.

### Map operations

Lookup, presence, insertion/duplicate detection, replacement, and removal all use the same legal-key relation as public `==`.

### Domain-specific equivalence

Programs may define separate ordinary predicates for approximate/case-insensitive/business-domain equivalence. Future open functions may make such predicates extensible, but they cannot redefine `==`, literal-pattern equality, duplicate binding consistency, or map-key identity.

---

## Protected-value non-interference

Code lacking matching declassification authority must not derive protected payload information through:

- equality/inequality
- recursive structural comparison
- hashing/key canonicalization
- ordering
- literal/duplicate-binding pattern matching
- serialization
- diagnostics/display/debug rendering
- map/container lookup or duplicate behavior

Protected carriers remain illegal map keys.

Carrier identity may be observed; payload equality may not.

---

## Failure boundary

For two well-formed Genia values, equality returns a boolean. Different kinds ordinarily produce `false`, not a new error.

Illegal map keys fail under the existing map-key misuse boundary. R18 requires deterministic rejection of NaN, recursively NaN-containing candidate keys, protected values, authorities, runtime handles, and other non-keyable families. Exact diagnostic text remains outside this release's portability redesign; R19 owns diagnostic hardening. No protected payload or opaque-token internal may appear in an equality/key diagnostic.

Opaque-token equality never fails because an issuer is unavailable: the hidden equality identity must already exist on the token.

---

## Implementation design

R18 should centralize semantics rather than patch each Python call site independently.

### Canonical equality module

Add a small internal semantic boundary, expected as `src/genia/equality.py`, with one conceptual operation:

```text
genia_equal(left, right) -> bool
```

This operation uses an explicit semantic-kind whitelist. It must not fall back to generic Python `left == right` for unknown host objects.

Each structural kind has an explicit semantic-field comparison; generic dataclass reflection is not semantic authority.

Identity-bearing values are intercepted and compared by logical identity regardless of Python dataclass equality.

Protected carriers are intercepted before host/structural equality. The current payload-comparing `GeniaProtected.__eq__` must be removed/narrowed during implementation so accidental internal Python equality cannot remain a protected-payload oracle.

### Numeric decision order

The equality engine handles booleans before integers so Python's bool/int relationship cannot leak. Numeric dispatch then handles exact int/int, float/float, and exact int/float bridge cases.

### Map-key canonicalization

The equality boundary (or a tightly coupled helper owned by it) provides one internal legal-key canonicalization operation.

The canonical identity is tagged by Genia semantic kind:

- bool distinct from numeric
- exactly equal int/integral-float collapse intentionally
- signed zero collapses intentionally
- NaN rejects
- string distinct from symbol
- Pair/List/represented recurse

`GeniaMap` may continue using a host dictionary only with these canonical identities as internal keys. Raw host value equality must not define map behavior.

Map equality compares mappings through canonical key identity plus Genia equality of mapped values and ignores entry order.

### Integration points

Later implementation routes these current semantic paths through the central equality boundary:

- evaluator EQEQ/NE
- `assert_eq`
- literal-pattern matching
- duplicate-binding merge
- `GeniaMap` operations
- semantic comparison call sites discovered in validation/representation/Sheet/data helpers

The audit is semantic-purpose-based; parser token/tag comparisons and other implementation-local Python equality remain ordinary host implementation details.

### No Core IR change

Existing equality operators and pattern IR are sufficient. R18 changes evaluator/runtime semantics only; no new parser/AST/Core IR node is added.

### Opaque-token future adapter

R18 does not add an unused public token class. A future opaque-token implementation must provide immutable hidden domain/provenance/semantic equality identities at creation time and adapt into the fixed equality engine without a comparator callback.

A private test fixture may exercise this architecture if needed, but it must not become source-visible language behavior.

---

## Later release slices

E18-0 ends after pre-flight, this contract/design, and explicit GO.

Planned implementation sequence under epic #789:

- E18-1 — structural and exact numeric equality
- E18-2 — map equality, legal keys, and key equivalence
- E18-3 — identity-bearing, opaque-token contract integration, and protected equality
- E18-4 — patterns/assertions/equality-like surface reconciliation
- E18-5 — multi-host conformance hardening
- E18-6 — authoritative documentation and release truth sync
- E18-7 — skeptical audit and distillation

Shared specs/tests belong to their TEST phases, not this contract document.

---

## Non-goals

- user-overloadable equality
- equality protocols/typeclasses
- approximate float comparison
- total ordering
- public hashing
- deep diff
- implicit dereference/state comparison
- token-domain/minting syntax or APIs
- storage/Revision implementation
- opaque-token map-key support
- R17 map-order redesign
- C++ host implementation
- R19 Unicode/float-display/diagnostic work

---

## E18-0 gate

The pre-flight, contract, and design resolve the prerequisites identified before R18 start:

- value inventory: resolved
- numeric matrix: resolved
- map-key relation: resolved
- protected-value security rule: resolved
- equality-like behavior reconciliation: resolved
- Revision generalization: resolved as the reusable opaque semantic-token family, compatible with future built-in and user-defined token domains without equality overloading

**GO for E18-1 failing-test phase after #790 is reviewed/approved and merged. No implementation is authorized inside E18-0.**
