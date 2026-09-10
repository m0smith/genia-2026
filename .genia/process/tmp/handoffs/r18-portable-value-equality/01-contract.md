# R18 Portable Value Equality — Contract

ISSUE: #790
PARENT: #789
STATUS: E18-0 contract gate
MATURITY: Experimental

`GENIA_STATE.md` remains final authority for implemented behavior. This contract defines the behavior R18 is approved to implement; until the implementation and documentation phases land, these rules are not claims about current runtime behavior.

---

## 0. BRANCH CHECK

Working branch: `issue-790-r18-portable-value-equality`
Base: `main`
Pre-flight: `.genia/process/tmp/handoffs/r18-portable-value-equality/00-preflight.md`

Branch is not `main` and matches the E18-0 pre-flight.

---

## 1. PURPOSE

Define one host-independent equality relation for Genia values so public equality, patterns, assertions, maps, protected values, and future hosts do not inherit accidental host-language equality behavior.

The public relation is `==`. It is permanently non-user-overloadable.

`!=` is exactly the logical negation of `==`.

Every Genia operation that needs semantic value sameness must either use this relation or explicitly define a different domain-specific predicate with a different name. Pattern duplicate bindings and map-key identity are not allowed to define a second equality relation.

---

## 2. SCOPE

### Included

- structural equality
- identity-bearing runtime equality
- opaque semantic-token equality
- protected-carrier equality
- exact numeric cross-kind equality
- structural map equality
- legal map-key equivalence and reflexivity
- equality purity/non-effect guarantees
- reconciliation of `==`, `!=`, `assert_eq`, literal patterns, duplicate pattern bindings, and map operations

### Excluded

- user-overloadable `==`
- approximate floating-point equality
- total ordering/comparison
- public hash APIs
- deep-diff diagnostics
- token-domain declaration or minting syntax/API
- storage or `Revision` implementation
- deciding opaque semantic tokens are legal map keys
- C++ host implementation
- changing R17 deterministic map order

---

## 3. BEHAVIOR

### 3.1 Canonical relation

For any two well-formed Genia values `a` and `b`, evaluating:

```genia
a == b
```

returns exactly one boolean.

Evaluating:

```genia
a != b
```

returns `!(a == b)`.

Equality itself does not return an Outcome and does not mutate either operand.

### 3.2 Equality families

Every equality-relevant Genia value belongs to exactly one operational equality family:

1. structural value
2. identity-bearing runtime value
3. opaque semantic token
4. protected carrier

Internal AST/IR/parser/debug/trampoline/transport implementation objects that are not Genia values are outside this language contract.

### 3.3 Structural values

Structural values compare by semantic kind and semantic contents, recursively using this same equality relation for contained Genia values.

Current structural families covered by R18 are:

- booleans
- integers
- floats
- strings
- quoted symbols
- Lists
- Pairs
- Outcomes: `some`, `none`, `err`
- maps
- represented values
- deterministic RNG state values
- first-class Format values
- byte values
- ZIP-entry values
- Sheets
- inert closed ordinary operation/data descriptors whose existing public contract defines them solely by immutable contained values, including the current inert HTTP operation value and ordinary HTTP/data response records

For structural constructors, constructor/kind differences are unequal even when visible payloads happen to resemble one another.

A structural value containing an identity-bearing, opaque-token, or protected value treats that value as a terminal leaf and applies that leaf's equality rule. Structural equality never traverses referenced runtime state behind such a leaf.

### 3.4 Identity-bearing runtime values

Identity-bearing values compare by logical runtime entity identity only.

Two references/handles to the same logical runtime entity compare equal. Two separately created runtime entities compare unequal even if their visible state, configuration, closure, or behavior is currently indistinguishable.

R18 identity-bearing families include:

- functions and function groups
- host/native callable values exposed as functions
- named reusable pattern / first-class Template matcher values
- model callable values
- module values
- Refs
- Cells
- Processes
- Seq/Flow runtime values, including lazy/fused forms
- promises
- meta-environment handles
- configuration providers
- declassification authorities
- model/embedding/reranking provider capabilities
- retrieval index handles
- Python/host interop handles
- output sinks and stdin/source handles
- lifecycle scope/definition/attachment values that denote or contain executable runtime behavior
- future live Store/execution/actor/job/subscription-like handles unless a later approved contract explicitly classifies a particular new type as an opaque semantic token

Identity equality never compares the referenced entity's state or contents.

Identity is scoped to the logical entity represented by the runtime value. R18 does not require identity-bearing values to serialize or preserve identity across independent runtime executions.

### 3.5 Opaque semantic tokens

Opaque semantic tokens represent immutable semantic facts whose public meaning includes equality but not inspectable representation.

Each token has three hidden equality components established before comparison:

1. **domain identity** — identifies the token domain/kind
2. **provenance identity** — identifies the canonical issuing/provenance context relevant to equality
3. **semantic identity** — identifies the immutable fact within that domain/provenance

The components are opaque to ordinary Genia code. Implementations may represent them however they choose, but their equality meaning must be host-independent.

Two opaque semantic tokens are equal iff all three hidden equality components are equal.

Token comparison:

- performs no callback to the issuer/provider
- performs no IO
- executes no user-defined code
- does not parse, expose, serialize, order, or otherwise reveal the hidden components

A future storage `Revision` is the motivating example. A provider observing the same resource revision at two different times may issue two distinct token carrier objects whose hidden equality components are the same; those tokens compare equal. Equal-looking provider strings such as an ETag do not make revisions equal unless the token's canonical hidden domain/provenance/semantic identities are equal.

The opaque-token family is extensible to future built-in token kinds and future user-defined token domains. That extensibility does not make equality extensible: users may not supply an equality callback or overload `==`. Any future token-minting facility must establish the fixed hidden equality components when the token is created.

R18 does not add such a minting facility.

### 3.6 Protected carriers

Protected carriers compare by carrier identity only.

For protected carriers `p1` and `p2`:

- `p1 == p1` is true
- aliases of the same carrier compare equal
- independently created carriers compare unequal even when they originate from the same provider, have the same purpose, and carry equal payload values

Ordinary equality never compares protected payloads.

To compare protected payloads, code must first cross the existing explicit authorized declassification boundary and then compare the resulting ordinary values.

### 3.7 Equality purity

Evaluating equality must not:

- perform IO or network access
- acquire configuration/secrets/resources
- declassify a protected value
- invoke a function, Template, matcher, model, provider, token issuer, or user callback
- consume or advance a Seq/Flow
- dereference a Ref
- inspect Cell/Process/handle/provider state
- mutate either operand or any reachable runtime state

Structural equality traverses only already-present structural contents. Identity-bearing, opaque-token, and protected values terminate traversal.

Well-formed ordinary structural Genia values must not require following cyclic structural containment. A runtime identity leaf may participate in a wider cyclic object graph without equality traversing through it.

---

## 4. SEMANTICS

### 4.1 Type/kind compatibility

Except for the explicitly defined integer/float numeric bridge, values from different semantic kinds/families are unequal.

Examples:

- symbol `quote(x)` is unequal to string `"x"`
- represented value is unequal to its unrepresented carried value
- boolean is unequal to integer/float even when the host language would coerce them
- List is unequal to Pair even if they could encode similar contents
- identity-bearing value is unequal to an ordinary structural value

### 4.2 Boolean equality

Booleans compare only with booleans.

- `true == true` → true
- `false == false` → true
- `true == false` → false
- `true == 1` → false
- `false == 0` → false

### 4.3 Integer equality

Integers compare by exact mathematical integer value with no range narrowing.

R17 arbitrary-precision integer semantics remain unchanged.

### 4.4 Float equality

Finite non-NaN floats compare by exact represented numeric value.

- `0.0 == -0.0` → true
- positive infinity equals positive infinity where infinities are supported
- negative infinity equals negative infinity where infinities are supported
- positive and negative infinity are unequal
- NaN is unequal to every value, including itself

R18 adds no approximate/tolerance equality.

### 4.5 Integer/float cross-kind equality

An integer `n` equals a float `f` iff:

1. `f` is finite,
2. `f` is mathematically integral, and
3. the exact mathematical integer denoted by `f` is `n`.

An implementation must not decide this by lossy conversion of arbitrary-precision `n` to host float.

Therefore exactly representable integer-valued floats may equal integers across kinds, while rounded/non-representable neighboring integers remain unequal.

### 4.6 Strings and symbols

Strings compare by their existing semantic string contents.

Symbols compare by symbol name/content.

Strings and symbols remain different kinds and are unequal to one another.

Unicode normalization/canonical-equivalence changes are outside R18; R19 owns string/Unicode portability hardening. R18 compares whatever string values the currently approved string model says are the same sequence of semantic string contents and does not introduce normalization.

### 4.7 Lists and Pairs

Lists are equal iff they have the same length and each corresponding element is equal.

Pairs are equal iff both heads are equal and both tails are equal.

List and Pair are distinct kinds.

### 4.8 Outcomes

Outcomes are equal only when they have the same constructor and corresponding semantic fields are equal.

- `some(v, c)` compares value and context under the existing constructor semantics
- `none(reason, context)` compares reason and context
- `err(reason, context)` compares reason and context

Different constructors are unequal regardless of contained values.

### 4.9 Represented values

Represented values are equal iff:

1. their outer facet identifiers are equal, and
2. their carried values are equal.

Representation layers are ordered. Nesting order and duplicate layers participate in equality. A represented value is unequal to its unrepresented carried value.

This preserves the already documented R9 representation identity rule while routing carried-value comparison through the canonical R18 relation.

### 4.10 RNG, Format, bytes, ZIP entries, Sheets, and inert data descriptors

- RNG state values are equal iff their deterministic semantic RNG states are equal.
- Format values are equal iff their semantic template/tag/composition structure is equal.
- byte values are equal iff their byte sequences are equal.
- ZIP-entry values are equal iff their semantic entry names and byte contents are equal.
- Sheets are equal iff their immutable semantic column structure and contained values are equal. Valid Sheet construction guarantees row-count consistency; equality does not create an independent hidden row-count identity.
- inert closed ordinary operation/data descriptors are equal iff their existing contract-defined semantic fields are equal recursively.

No equality rule invokes behavior embedded behind callable/runtime leaves contained by these structures.

### 4.11 Map equality

Map equality is mapping equality, not iteration-order equality.

Two maps `a` and `b` are equal iff:

1. they contain the same number of mappings, and
2. for every legal key/value mapping `(ka, va)` in `a`, `b` contains a key `kb` such that `ka == kb`, and the corresponding value `vb` satisfies `va == vb`.

Because legal map-key equality is a proper reflexive key relation, each mapping has at most one equal-key counterpart.

Different insertion histories do not make equal mappings unequal.

R17 deterministic map order remains unchanged and separately observable through iteration/accessor/display behavior already covered by R17.

A map may contain NaN or another non-reflexive value as a **value**; such contents can make the enclosing structural value non-reflexive. R18 requires reflexivity only for legal **keys**, not for every possible Genia value.

### 4.12 Legal map keys

R18 preserves the established public keyable surface and does not promote host-only accommodations into new public kinds.

The legal public key families are:

- booleans
- integers
- non-NaN floats, including infinities where supported
- strings
- symbols
- Pairs whose head/tail are recursively legal keys
- Lists whose elements are recursively legal keys
- represented values whose carried value is recursively a legal key and whose facet identity is valid under the existing representation contract

Maps, Outcomes, functions/Templates, providers, authorities, protected carriers, Refs/Cells/Processes/Flows/Seqs, handles, modules, Sheets, Formats, bytes, ZIP entries, RNG states, opaque semantic tokens, and other runtime values are not made legal keys by R18 unless they were already an established public key family above.

Python-internal tuple and `None` handling in the current `_freeze_map_key` implementation is not promoted into a new public Genia key kind.

A legal key must be reflexive under public equality:

```text
k == k  => true
```

Therefore:

- NaN is illegal as a map key
- a Pair/List/represented key containing NaN in an equality-relevant structural position is illegal

### 4.13 Map key equivalence

For legal keys, map key equivalence is exactly public Genia equality.

If `a == b` and both are legal keys, then they denote the same map entry for:

- lookup
- presence tests
- insertion/duplicate detection
- replacement
- removal

Equal-key replacement preserves the existing R17 key position. Removing an equal key removes that mapping. Removing and then reinserting remains governed by R17's append rule.

No host container rule may silently collapse unequal Genia keys. In particular:

- `true` and `1` are different keys
- `false` and `0` are different keys
- integer `1` and exactly equal float `1.0` are the same key
- `0.0` and `-0.0` are the same key

Any internal canonicalization/hash/equivalence mechanism is implementation-private, but for legal keys it must satisfy:

```text
a == b  => identical internal key equivalence/hash treatment
```

and it must not merge unequal legal keys.

### 4.14 Literal patterns

A literal pattern matches a candidate value iff the literal value is equal to the candidate under canonical Genia equality.

No separate pattern-literal equality exists.

### 4.15 Duplicate pattern bindings

When one pattern binds the same variable name more than once, all bindings for that name must be equal under canonical Genia equality.

Therefore a pattern equivalent to `f(x, x)` accepts `f(1, 1.0)` but rejects `f(true, 1)` under the approved numeric rules.

No separate duplicate-binding equality exists.

### 4.16 Named patterns/Templates

Invoking a named matcher remains existing pattern behavior and is not itself an equality operation.

When equality compares Template/named-pattern values as values, it uses identity-bearing equality and never invokes the matcher.

### 4.17 `assert_eq`

`assert_eq(actual, expected)` succeeds iff `actual == expected` is true under canonical Genia equality.

It must not define an independent comparison rule.

Existing assertion return/failure-shape behavior remains otherwise unchanged. R18 does not add deep-diff diagnostics.

### 4.18 Domain-specific equivalence

Programs may use ordinary named predicates for domain-specific notions such as approximate numeric comparison, case-insensitive text comparison, business-key equivalence, or future open-function-dispatched equivalence.

Those predicates are not `==` and must not redefine:

- public equality
- duplicate pattern bindings
- literal pattern equality
- map-key equivalence

---

## 5. FAILURE

### 5.1 Equality itself

For well-formed Genia values, `==` returns a boolean rather than failing because the values have different kinds. Different kinds are ordinarily unequal.

Equality must fail only when an operand is not a well-formed Genia value at a boundary that already rejects such host leakage; R18 does not create a new public host-object comparison facility.

### 5.2 Illegal map keys

Attempting to construct/use a map operation with an illegal key fails under the existing map-key misuse/error boundary.

R18 requires deterministic rejection for:

- NaN
- recursively key-shaped structural values containing NaN
- protected carriers
- declassification authorities
- index/host/runtime handles and other non-keyable families

The exact diagnostic wording is not redesigned by this contract; R19 owns diagnostic portability hardening. R18 requires the failure category/reason to remain deterministic and must never leak protected payloads or opaque-token internals.

### 5.3 Protected values

Comparing protected carriers never fails merely because declassification authority is absent. It compares carrier identity and does not inspect payloads.

No implicit declassification occurs.

### 5.4 Opaque tokens

Comparing opaque tokens never calls their issuer and never fails because the issuer is unavailable. Their hidden equality components were established before comparison.

Tokens from different domains/provenance compare unequal; equality does not attempt conversion or cross-domain negotiation.

---

## 6. INVARIANTS

1. **Single relation:** every equality-like semantic surface named in R18 agrees with public `==` for the same values.
2. **Negation:** `a != b` is exactly `!(a == b)`.
3. **Non-overloadable:** user code cannot redefine `==`.
4. **Purity:** equality performs no IO, acquisition, declassification, callback, Flow/Seq consumption, Ref dereference, mutation, or runtime-state traversal.
5. **Structural recursion:** structural values compare recursively by semantic contents.
6. **Terminal leaves:** identity-bearing, opaque-token, and protected values terminate structural traversal.
7. **Boolean separation:** booleans are never numerically equal to integers/floats.
8. **Exact numeric bridge:** int/float equality is mathematical and exact, not lossy coercion.
9. **NaN:** NaN is unequal to itself.
10. **Signed zero:** `0.0 == -0.0`.
11. **Map order separation:** map equality ignores insertion history while R17 iteration order remains unchanged.
12. **Key reflexivity:** every legal map key equals itself.
13. **Key consistency:** equal legal keys are interchangeable for all map operations.
14. **No hidden key relation:** unequal legal keys are not merged by host container semantics.
15. **Protected non-interference:** code without declassification authority cannot infer protected payload equality through equality, keying, matching, diagnostics, serialization, or container behavior.
16. **Opaque-token closure:** token equality is fixed by hidden domain/provenance/semantic identity and never invokes user/issuer logic.
17. **Future token compatibility:** future built-in/user-defined token domains may use the opaque-token family without adding a new equality algorithm.
18. **No Core IR expansion:** R18 changes semantics behind existing equality/pattern IR, not parse/IR shape.

---

## 7. EXAMPLES

Examples below define intended R18 behavior; they are not claims that current `main` already implements it.

### 7.1 Numeric

```genia
1 == 1.0        # true
true == 1       # false
false == 0      # false
0.0 == -0.0     # true
```

NaN, where constructed through an existing supported float path:

```text
NaN == NaN      # false
```

### 7.2 Structural

```genia
[1, 2] == [1.0, 2.0]   # true
[1, true] == [1.0, 1]  # false
Pair(1, 2) == Pair(1.0, 2.0)  # true, expressed through the existing Pair surface
```

### 7.3 Maps

Conceptually:

```text
map built as a→1 then b→2
==
map built as b→2 then a→1

true
```

The two maps may still expose different R17 iteration orders.

A map key inserted with integer `1` is found/replaced/removed by exactly equal float `1.0`; key `true` is distinct.

### 7.4 Duplicate pattern binding

```genia
same(x, x) = true
same(_, _) = false

same(1, 1.0)   # true
same(true, 1)  # false
```

Exact surface remains whatever current repeated-binding syntax already supports; R18 adds no syntax.

### 7.5 Protected carrier

```text
p = one protected carrier
p == p          => true

p1 = independently acquired protection of payload "secret"
p2 = independently acquired protection of payload "secret"
p1 == p2        => false
```

Payload equality is observable only after explicit authorized declassification.

### 7.6 Future opaque token

A future provider observes the same resource revision twice and mints two `Revision` token carriers with identical hidden domain/provenance/semantic identity. They compare equal without equality contacting the provider.

A future user-defined token domain may mint tokens under the same fixed equality family, but cannot provide a custom `==` implementation.

---

## 8. NON-GOALS

R18 does not:

- add user-defined equality methods/operators
- add typeclasses/protocols for equality
- add approximate floats
- add ordering
- add a public hash function
- define deep diff output
- serialize runtime identity values
- dereference runtime handles during equality
- add token-domain or token-minting syntax
- implement `Revision` or storage
- make opaque tokens map keys
- alter R17 map ordering
- implement any C++ runtime
- redefine Unicode normalization or exact float display formatting owned by R19

---

## 9. DOC NOTES

When implementation lands, `GENIA_STATE.md` should describe R18 as the portable Experimental equality/key contract and clearly distinguish:

- structural values
- identity-bearing runtime values
- opaque semantic tokens
- protected carriers
- exact numeric cross-kind rules
- mapping-based map equality versus R17 map order
- legal-key reflexivity/equivalence
- pattern/assertion reconciliation
- equality purity/non-interference

`GENIA_RULES.md` should carry only durable compiler/runtime invariants needed to prevent semantic drift, especially duplicate binding equality and the non-overloadable/single-relation rules.

`GENIA_REPL_README.md` / `README.md` should be updated only where public user-facing equality behavior needs explanation; they must not claim future token-minting/storage functionality.

Mark R18 equality behavior **Experimental** unless a later release explicitly promotes maturity.

---

## 10. FINAL CHECK

- Precise and testable: YES
- No implementation: YES
- No tests/specs embedded as contract artifacts: YES
- No scope expansion beyond pre-flight: YES
- Host-independent: YES
- Preserves R17 order contract: YES
- Keeps `GENIA_STATE.md` as implemented-truth authority: YES
- User-defined token domains future-compatible without user-overloadable equality: YES

**CONTRACT GATE: GO for design only.**
