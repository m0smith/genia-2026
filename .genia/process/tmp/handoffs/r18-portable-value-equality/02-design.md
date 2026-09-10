# R18 Portable Value Equality — Design

ISSUE: #790
PARENT: #789
STATUS: E18-0 design gate

This design translates `.genia/process/tmp/handoffs/r18-portable-value-equality/01-contract.md` into implementation structure. It adds no behavior and authorizes no TEST/implementation work beyond an explicit later GO.

---

## 0. BRANCH CHECK

Working branch: `issue-790-r18-portable-value-equality`
Base: `main`
Pre-flight and contract exist on this branch.

---

## 1. PURPOSE

Organize R18 around one semantic equality authority rather than patching Python `==` call sites independently.

The design has two central responsibilities:

1. **semantic equality dispatch** — classify values and compare them according to the four contract families
2. **map-key canonical equivalence** — validate legal keys and create an internal key identity that is exactly consistent with semantic equality

Everything else delegates to those responsibilities.

---

## 2. SCOPE LOCK

### Contract includes

- structural, identity-bearing, opaque-token, and protected equality families
- exact bool/int/float rules
- structural map equality
- legal-key reflexivity and equality-aligned map operations
- equality purity
- `==`/`!=`, literal-pattern, duplicate-binding, and `assert_eq` reconciliation

### Contract excludes

- equality overloading
- approximate floats or ordering
- public hash APIs
- token-domain/minting syntax or public opaque-token constructor
- storage/Revision implementation
- opaque-token map-key support
- C++ implementation
- R17 map-order changes

No excluded item is introduced by this design.

---

## 3. ARCHITECTURE

### 3.1 One semantic equality boundary

Add one small runtime semantic module responsible for Genia equality. Proposed file:

- `src/genia/equality.py`

The module owns the host-independent decision structure for:

- semantic kind/family classification needed by equality
- recursive structural equality
- exact numeric cross-kind comparison
- identity-leaf comparison
- protected-carrier comparison
- opaque-token comparison when a token type exists
- legal map-key validation/canonicalization

No evaluator, pattern matcher, assertion helper, or map operation may reimplement equality rules.

The public language does not gain a new function. Existing `==`/`!=` operators are routed through this internal semantic boundary.

### 3.2 Explicit whitelist, no fallback-to-host equality

The equality dispatcher must classify supported Genia semantic value kinds explicitly.

It must not end with a generic Python `a == b` fallback for arbitrary runtime objects. Unknown host objects reaching the semantic equality boundary are host leakage/misuse, not an invitation to make Python object equality part of the language.

This prevents future dataclasses/classes from silently becoming structural or identity values solely because of Python defaults.

### 3.3 Structural recursion

Structural comparison dispatches by semantic kind, then compares only contract-defined semantic fields recursively.

Examples of field plans:

- Symbol → name
- List → length + corresponding items
- Pair → head/tail
- Outcome → constructor + value/reason/context fields as applicable
- represented value → facet + carried value
- RNG → semantic state
- Format → template/tag/composed pieces
- bytes → byte sequence
- ZIP entry → name + bytes
- Sheet → semantic ordered columns + cell values
- inert HTTP operation/data descriptor → its contract-defined ordinary fields
- Map → dedicated mapping comparison path

Identity-bearing/protected/opaque leaves terminate recursion.

### 3.4 Numeric comparator

The semantic equality module owns numeric comparison before generic kind comparison so bool/int host-subtyping cannot leak.

Decision order:

1. detect booleans first and compare only bool-to-bool
2. int-to-int exact integer equality
3. float-to-float exact numeric equality with explicit NaN and signed-zero rules
4. int-to-float / float-to-int exact mathematical-integral comparison
5. otherwise kinds differ

The Python host implementation should use an exact representation check for integral floats rather than converting arbitrary-precision integers to float. The specific Python mechanism is implementation-local; the observable rule is the contract's mathematical equality.

### 3.5 Identity-bearing values

The central dispatcher has an explicit set of identity-bearing semantic classes/kinds. Python may use object/logical-handle identity as its implementation technique, but no fields/state are compared.

This deliberately overrides Python dataclass-generated `__eq__` where those objects are identity-bearing (for example function groups/modules if host equality would otherwise recurse into contents).

No need exists to make every runtime class implement custom Python `__eq__`; language equality is centralized. Security-sensitive classes may still narrow their Python equality defensively where host-internal accidental comparison itself could leak protected information.

### 3.6 Protected carrier

`GeniaProtected` is intercepted before any structural/host equality path.

Language equality compares carrier identity only.

Because the current class has a payload-comparing Python `__eq__`, the Python implementation phase should also remove that payload-oracle behavior defensively so an internal accidental Python comparison cannot bypass the intended non-interference boundary. This is an implementation hardening step that matches, rather than expands, the contract.

Protected carriers remain unkeyable.

### 3.7 Opaque semantic-token extension point

R18 defines the semantic interface but does **not** add a public token value or minting API merely to exercise it.

When a future token value is introduced, its runtime representation must expose to the equality engine only an internal immutable equality identity equivalent to:

- domain identity
- provenance identity
- semantic identity

The equality engine compares those pre-established components directly. It never calls a token-supplied equality method, provider, issuer, user function, or callback.

The design should reserve a narrow internal protocol/shape in documentation rather than adding an unused public class now. If a later R18 implementation slice needs a private test fixture to verify the dispatcher architecture, that fixture must remain test/internal-only and must not become source-visible Genia behavior.

A future user-defined token-domain facility must adapt into this fixed shape at mint time; it cannot register comparator code.

### 3.8 Map-key canonical identity

Move key legality/equivalence away from Python's implicit dict equality and into the equality module (or a tightly coupled internal helper owned by it).

The internal canonical key representation must be tagged by Genia semantic kind so host coercions cannot merge unequal keys.

Required canonical-equivalence design properties:

- bool gets a distinct kind tag from numeric values
- equal int/integral-float values canonicalize to the same numeric key identity
- `0.0` and `-0.0` canonicalize together
- NaN is rejected before canonicalization
- non-integral finite floats preserve exact float identity under the approved numeric relation
- infinities canonicalize deterministically by sign
- string and symbol have distinct tags
- Pair/List canonicalize recursively
- represented keys include facet identity plus recursively canonicalized carried key
- recursively encountered NaN rejects the entire key
- unsupported families reject before touching the host map

This is an internal key token, not a public hash API.

### 3.9 GeniaMap integration

`GeniaMap` remains the ordered persistent-associative value established by prior releases.

Its internal entry storage may continue using a host dictionary if the dictionary is keyed only by R18 canonical key identities. The host dictionary then stores canonical tokens whose equality/hash behavior has already been normalized to Genia semantics, rather than raw user values whose Python equality can leak.

Map operations route through the same key canonicalizer:

- get
- has
- put/new-key detection
- replacement
- remove
- literal duplicate-key association

Map equality does not compare `_entries` dictionaries directly. It compares semantic mappings by canonical legal-key identity and Genia equality of mapped values, ignoring insertion order.

R17 entry order remains stored separately by the existing ordered dictionary insertion behavior and is not altered by equality.

### 3.10 Evaluator integration

Existing binary operator nodes remain unchanged.

Evaluator behavior changes only at the EQEQ/NE dispatch point:

- EQEQ delegates to canonical Genia equality
- NE negates that result

No parser or Core IR change.

### 3.11 Pattern integration

`pattern_match.py` imports/uses canonical Genia equality for:

- `IrPatLiteral`
- `_merge_bindings` duplicate-name reconciliation

Other pattern mechanisms retain their existing behavior. Named matchers remain user-executed pattern operations when explicitly invoked as patterns; comparing matcher/Template values themselves is identity-only and never invokes them.

### 3.12 Native assertion integration

`assert_eq` uses canonical Genia equality for pass/fail only.

Existing NativeTestFailure shape and safe rendering remain unchanged except where protected-value security requires existing rendering guarantees to remain non-leaking.

### 3.13 Other semantic-equality call-site audit

Before implementation completes, mechanically inspect Python `==`/`!=` uses that answer a Genia semantic sameness question rather than an implementation-local question.

Likely categories:

- validation/representation helpers
- duplicate or dedup logic over Genia values
- Sheet/data helpers
- configuration/protected tests and helpers
- any map-literal association logic outside `GeniaMap`

Implementation-local comparisons such as parser token kinds, enum/tag strings, internal counters, test framework metadata, and host protocol fields do not need routing through Genia equality.

The rule is semantic purpose, not textual replacement of every Python `==`.

---

## 4. FILE PLAN

### New files

- `src/genia/equality.py` — canonical semantic equality and legal-key canonicalization boundary
- shared spec files under `spec/eval/` / `spec/error/` in later TEST slices, names chosen per slice rather than E18-0
- `docs/design/r18-portable-value-equality-contract.md` — durable E18 contract/design record
- `docs/releases/R18.md` — only during E18-6 completion documentation

### Modified files in later slices

- `src/genia/evaluator.py`
- `src/genia/values.py`
- `src/genia/pattern_match.py`
- `src/genia/builtins.py`
- other runtime modules only where the equality-call-site audit finds a genuine semantic comparison or explicit family classification need
- focused unit/native tests
- `GENIA_STATE.md`
- `GENIA_RULES.md`
- `GENIA_REPL_README.md` / `README.md` only where warranted
- `docs/contract/semantic_facts.json` / `tests/doc/test_semantic_doc_sync.py` if durable equality facts require cross-doc guards
- R18 roadmap status files at release completion

### Removed files

None planned.

Temporary `.genia/process/tmp/handoffs/r18-portable-value-equality/*` artifacts are subject to the normal Doc Distillation decision at E18-7; they are not durable semantic truth.

---

## 5. DATA / INTERFACE DESIGN

### 5.1 Internal semantic equality function

One internal operation accepts two runtime Genia values and returns bool.

Contract-level interface:

```text
genia_equal(left, right) -> bool
```

Name is implementation-internal and may change; there is no new public callable.

Responsibilities:

- explicit family/kind dispatch
- exact numeric handling
- structural recursion
- identity/protected/opaque terminal handling
- no side effects/capabilities

### 5.2 Internal legal-key operation

One internal operation accepts a candidate key and returns an internal canonical key identity or rejects it under the existing map-key error boundary.

Conceptual interface:

```text
canonical_map_key(value) -> opaque internal key identity
```

This is not Genia-visible and creates no public hashing surface.

The returned identity must satisfy equality/key consistency from the contract.

### 5.3 Structural semantic-field table

The equality module should maintain a deliberate semantic mapping rather than using generic dataclass field reflection. Reflection would make adding a Python field accidentally change Genia equality.

Each structural runtime kind gets an explicit comparison branch naming only its semantic fields.

### 5.4 Identity-kind table

Identity-bearing kinds are likewise explicit. No generic `callable => compare Python object` fallback should silently classify unknown future values. New runtime value kinds must make an explicit equality-family decision when added.

### 5.5 Opaque-token adapter shape

Future opaque token types provide immutable internal equality components at construction/minting time. The semantic equality boundary reads only those components.

No comparator function pointer/callback is part of the shape.

R18 itself need not expose or construct such a token from Genia source.

---

## 6. CONTROL / ERROR FLOW

### 6.1 Equality execution

1. identify protected/opaque/identity terminal categories that must not be structurally traversed
2. handle bool/numeric special cases before host-subtyping can collapse kinds
3. if semantic kinds differ outside approved numeric bridge, return false
4. for structural same-kind values, compare contract-defined semantic fields recursively
5. for map, use mapping comparison independent of iteration order
6. return bool

No callback or capability boundary is crossed.

### 6.2 Map operation

1. receive candidate key
2. validate/canonicalize recursively
3. reject NaN/unsupported/protected/runtime key before accessing host storage
4. use canonical key identity for lookup/presence/put/remove
5. preserve existing R17 order behavior for new versus replacement entries

### 6.3 Pattern execution

Existing pattern dispatch remains unchanged except literal equality and duplicate binding consistency call the canonical equality operation.

Pattern mismatch remains mismatch; equality does not turn kind differences into errors.

### 6.4 Assertion execution

`assert_eq` calls canonical equality. False produces the existing NativeTestFailure path; true returns existing success value.

### 6.5 Protected handling

Protected carriers are recognized before any recursive/host equality. Only carrier identity is observed. No declassification authority is requested or consulted.

### 6.6 Unknown host objects

No generic host equality fallback is allowed. If a non-Genia host object reaches a boundary that requires Genia equality, it is treated according to existing host-leakage/misuse rules rather than silently adopting its Python `__eq__` semantics. Exact diagnostic wording is not an R18 redesign.

---

## 7. TEST PLAN INPUT

Tests belong to later TEST phases; this section supplies targets only.

### Invariants to test

- one relation across `==`, `!=`, `assert_eq`, literal patterns, duplicate bindings
- exact numeric matrix including large integer/float boundary cases
- structural List/Pair/Outcome/represented/Format/bytes/Sheet cases as reachable from public source
- map equality independent of insertion history
- map key `1`/`1.0`, `true`/`1`, signed zero, infinity, NaN
- nested NaN key rejection in List/Pair/represented keys
- replacement/removal through equal cross-kind numeric keys preserves R17 order
- identity alias versus separately created equivalent-state runtime values
- protected alias versus independently acquired same-payload carriers
- protected nested inside structural values does not leak payload equality
- no Flow consumption / Ref dereference / provider/model/token callback during equality
- no parse/Core IR shape change

### Edge cases

- empty structures/maps
- deeply nested structural values within existing recursion limits/ordinary runtime constraints
- maps containing NaN as values (allowed; may be non-reflexive)
- maps with represented versus unrepresented keys
- structural values containing identity-bearing leaves
- float values just below/above exactly representable integer boundaries
- infinities where supported

### Regression risks

- Python bool/int dictionary-key collapse
- Python dataclass-generated equality on identity-bearing runtime values
- current `GeniaProtected.__eq__` payload comparison
- map insertion-order damage while changing key canonicalization
- pattern dispatch changes beyond equality
- protected diagnostics leaking sentinel values
- host-only tuple/None map key accommodations accidentally becoming public contract
- tests asserting Python object equality directly instead of Genia-language equality

### Likely locations

- `spec/eval/r18-*.yaml`
- `spec/error/r18-*.yaml`
- `tests/unit/test_*equality*.py`
- focused map, pattern, protected-configuration, native-test, Sheet/representation regression files

---

## 8. DOC IMPACT

Required after implementation:

- `GENIA_STATE.md` — final implemented R18 semantics
- `GENIA_RULES.md` — single-relation/non-overloadable equality, duplicate-binding rule, durable map-key invariants where appropriate
- `GENIA_REPL_README.md` — user-facing behavior only if needed
- `README.md` — concise language snapshot/reference link if needed
- `docs/releases/R18.md` — required release page at completion
- `docs/strategy/roadmap/r16-r20.md` and canonical roadmap status — completion status only after audit
- semantic facts/guard tests if needed to prevent cross-doc equality drift

The durable design/contract file is:

- `docs/design/r18-portable-value-equality-contract.md`

It must remain below `GENIA_STATE.md` in authority and must not claim unimplemented behavior as current.

---

## 9. COMPLEXITY CHECK

- [ ] Minimal
- [x] Necessary
- [ ] Over-engineered

A dedicated equality module adds one explicit semantic boundary but removes multiple implicit host-language equality paths. A separate public abstraction, protocol/typeclass, registry, or user comparator system would be over-engineered and is explicitly excluded.

---

## 10. FINAL CHECK

- matches contract exactly: YES
- no new behavior added by design: YES
- no host-specific semantic assumptions: YES
- no parser/Core IR expansion: YES
- no user-overloadable equality: YES
- no public token constructor/minting API: YES
- opaque semantic-token family remains future-extensible through fixed hidden identities, not callbacks: YES
- preserves R17 ordered-map semantics: YES
- keeps protected payload opaque: YES
- implementation/test work remains gated: YES

**DESIGN GATE: GO for E18-1 failing-test phase only after #790 is reviewed/approved and closed as the completed E18-0 gate.**
