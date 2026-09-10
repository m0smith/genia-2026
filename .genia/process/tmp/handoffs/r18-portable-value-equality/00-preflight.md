# R18 Portable Value Equality — Pre-flight

CHANGE NAME: R18 Portable Value Equality
CHANGE SLUG: r18-portable-value-equality
ISSUE: #790
PARENT: #789

`GENIA_STATE.md` is final authority for implemented behavior. This pre-flight records current-state evidence and the approved direction to take into the contract phase; it does not make any R18 behavior implemented.

---

## 0. BRANCH

Branch required: YES
Branch type: feature
Branch slug: r18-portable-value-equality
Working branch: `issue-790-r18-portable-value-equality`
Base branch: `main`
Base revision observed at start: `674bf2bfe12af803b05a83d0a3e7129c6ee8b13b`

`docs/process/run-change.md` requires issue-scoped branches (`issue-<number>-<short-name>`), so the working branch follows that rule. No R18 work is performed on `main`.

---

## 1. SCOPE LOCK

### Includes

- one portable, non-user-overloadable Genia equality relation
- a complete equality-relevant value-family inventory
- structural-value equality
- identity-bearing runtime-value equality
- a general opaque semantic-token equality family
- `Revision` as a motivating future token example, not a Revision-specific equality exception
- compatibility with future built-in and user-defined opaque token domains without user-defined equality callbacks
- protected-carrier equality that cannot act as a protected-payload oracle
- exact numeric cross-kind equality semantics
- structural map equality independent of R17 deterministic iteration order
- one map-key equivalence relation aligned with public `==` for legal keys
- legal-key reflexivity and NaN restrictions
- reconciliation of `==`, `!=`, `assert_eq`, literal patterns, duplicate pattern bindings, map operations, and recursive structural comparison
- a purity boundary for equality: no IO, capability use, acquisition, declassification, user code, Flow/Seq consumption, Ref dereference, mutation, or referenced runtime-state traversal
- design targets for later shared specs and implementation, without creating those specs or implementation in E18-0

### Excludes

- runtime implementation changes in this pre-flight/contract/design gate
- shared semantic-spec or test additions in this gate
- user-overloadable `==`
- approximate floating-point equality
- total ordering or comparison operators
- public hash APIs
- deep-diff diagnostics
- new token-domain declaration or token-minting syntax/API
- storage or `Revision` implementation
- making opaque semantic tokens legal map keys
- C++ host implementation
- changing R17 deterministic map construction/iteration order
- adding a second equality mechanism for patterns, maps, assertions, or future open functions

---

## 2. SOURCE OF TRUTH

### Authoritative

1. `GENIA_STATE.md` — final authority for implemented behavior
2. `GENIA_RULES.md`
3. `GENIA_REPL_README.md`
4. `README.md`
5. `spec/*`
6. `docs/host-interop/*`
7. `docs/architecture/*`
8. implementation under `src/*` / `hosts/*`

### Additional relevant

- `AGENTS.md`
- `docs/strategy/killer-workflow.md`
- `docs/strategy/release-roadmap.md`
- `docs/strategy/roadmap/r16-r20.md`
- `docs/releases/R17.md`
- `docs/process/run-change.md`
- `docs/process/00-preflight.md`
- `docs/process/extensions/portability-analysis.md`
- `docs/process/01-contract.md`
- `docs/process/02-design.md`
- `docs/process/08-roadmap-ticketing.md`
- `docs/design/r9-value-template-representation-contract.md`
- completed R10 configuration/protected-value contract material

### Current-state notes

- R17 explicitly leaves map equality unresolved. Its portable contract covers deterministic map order while documenting that separately created maps currently exhibit Python-host identity-based `==` behavior.
- Public binary `==` and `!=` currently delegate to Python equality/inequality in `src/genia/evaluator.py`.
- `assert_eq` currently performs an independent Python `actual != expected` check in `src/genia/builtins.py`.
- literal-pattern matching currently uses Python `==`; duplicate binding merge currently uses Python `!=` in `src/genia/pattern_match.py`.
- `GeniaProtected.__eq__` currently compares provider identity, purpose, and carried payload equality, making equality capable of observing protected-payload sameness without declassification.
- `GeniaMap` currently defines key behavior through `_freeze_map_key(...)` plus a Python dict rather than through a written Genia key-equivalence contract.
- current host implementation behavior is evidence to reconcile, not automatic portable truth.

---

## 3. FEATURE MATURITY

Stage:
- [x] Experimental
- [ ] Partial
- [ ] Stable

Doc wording:

R18 is a planned foundational portability release until all gates complete. During E18-0, its equality rules are proposed/approved contract material only. Implemented-behavior docs must continue to describe current Python reference-host behavior until the implementation and documentation phases land.

---

## 3a. PORTABILITY ANALYSIS

### Portability zone

Portable language/runtime semantics crossing evaluator values, structural containers, map key equivalence, pattern matching, assertion semantics, and protected-value behavior. This is a core cross-host semantic contract, not a Python host capability.

### Core IR impact

`none`.

R18 does not require a new `Ir*` node family. Existing binary equality/inequality lowering and existing pattern IR remain sufficient. The semantic meaning of equality during evaluation changes behind the existing IR surface; parse and lowering shapes remain unchanged.

### Capability categories affected

- `eval`: directly affected because `==`, `!=`, values, maps, and pattern dispatch are evaluated semantics.
- `error`: affected only where equality/key rejection or existing assertion failure is surfaced through deterministic observable diagnostics; R18 does not redesign error categories.
- `parse`: no semantic/syntax expansion.
- `ir`: no node-shape expansion.
- `cli`: no CLI-specific equality mechanism; CLI observations may transitively exercise eval behavior.
- `flow`: no Flow equality traversal or consumption; Flow remains an identity-bearing leaf if compared.
- host capabilities: none added or changed.

### Shared spec impact

Later TEST/implementation slices must add host-independent eval/error evidence for approved structural, numeric, map/key, protected, identity/token, pattern-binding, and assertion semantics. Existing R16 subprocess adapter/protocol and categories are sufficient; no shared-spec schema or runner protocol change is needed for R18 itself.

No shared spec is added in E18-0 because `AGENTS.md` requires contracts to define behavior only and reserves shared YAML/pytest work for the TEST phase.

### Python reference host impact

Later implementation will replace host-language equality as the semantic authority in at least:

- `src/genia/evaluator.py`
- `src/genia/values.py`
- `src/genia/pattern_match.py`
- `src/genia/builtins.py`

It will also require focused review of runtime value definitions in callable/model/retrieval/sheet/lifecycle/HTTP modules so they are classified deliberately rather than inheriting Python dataclass/object equality accidentally.

### Host adapter impact

No adapter protocol change. Existing `eval` and `error` execution paths can carry R18 conformance cases. Capability discovery does not need a new host capability because equality is language semantics, not an optional external capability.

### Future host impact

A future conforming host, including the planned C++ host, must implement the written Genia equality/key contract rather than its native language/container equality. In particular it must reproduce exact integer/float equality, boolean separation, NaN behavior, structural map equality, legal-key equivalence, identity leaves, opaque semantic-token equality, and protected non-oracle behavior without consulting Python implementation source.

---

## 4. CONTRACT vs IMPLEMENTATION

### Portable contract direction to formalize

One public `==` relation is the semantic authority. `!=` is its logical negation. Other equality-like surfaces consume that same relation rather than defining competing notions of sameness.

The relation has four operational families:

1. **Structural values** — equality recursively compares semantic contents.
2. **Identity-bearing runtime values** — equality compares logical runtime identity and never traverses referenced state/configuration.
3. **Opaque semantic tokens** — equality compares immutable hidden token domain + compatible provenance/authority + opaque semantic identity. Token comparison executes no issuer or user code. `Revision` is a future motivating example, not a special case.
4. **Protected carriers** — equality compares carrier identity only; it never compares protected payload contents.

The opaque-token family is open to future built-in and user-defined token domains, but the equality algorithm is closed. Users may eventually define/mint token domains only through separately approved future functionality; they do not supply an equality callback or overload `==`.

### Resolved equality-relevant value inventory

The inventory below classifies semantic values, not every Python helper class. Internal AST/IR nodes, debug hooks, source spans, exceptions, parser glob tokens, TCO `TailCall`, and other evaluator implementation artifacts are not Genia value families and do not acquire public equality semantics merely because Python can compare them.

#### Structural value family

These compare by their approved semantic contents, recursively through the same Genia equality relation:

- ordinary nil/absence representation at the semantic boundary where applicable
- `bool` — value equality, but never numeric equality
- `int`
- `float`
- `string`
- `GeniaSymbol` / quoted symbols
- Lists
- `GeniaPair`
- Outcomes: `GeniaOptionSome`, `GeniaOptionNone`, `GeniaOptionErr` by constructor plus their semantic fields
- `GeniaMap` by mappings, independent of deterministic insertion/iteration order
- `GeniaRepresented` by ordered facet layer plus carried-value equality; representation nesting/order/duplicates remain semantically significant
- `GeniaRng` by explicit RNG state; it is deterministic immutable state data, not a live capability
- `GeniaFormat` by its semantic format structure (`template`, `tag`, composed pieces) rather than object allocation identity
- `GeniaBytes` by byte contents
- `GeniaZipEntry` by entry name plus byte-value contents
- `GeniaSheet` by its immutable semantic column/value contents (with valid construction preserving its row-count invariant)
- inert immutable closed operation/data descriptors exposed as ordinary values, including `HttpOperation` and ordinary response/data records where their existing contract defines them purely by contained values

A structural value containing an identity-bearing, opaque-token, or protected leaf treats that leaf according to that leaf's equality rule; structural recursion does not pierce the leaf.

#### Identity-bearing runtime value family

These compare only by logical runtime entity identity. Equality never compares or dereferences their state, closure, provider configuration, queue contents, iterator progress, or host handle payload:

- `GeniaFunction`
- `GeniaFunctionGroup`
- native/host callables exposed as functions
- `GeniaNamedPattern` / first-class Template matcher values
- `GeniaModel` callable values
- `ModuleValue`
- `GeniaRef`
- `GeniaCell`
- `GeniaProcess`
- `GeniaSeq` and `GeniaFlow`, including fused/lazy flow forms
- `GeniaPromise`
- `GeniaMetaEnv`
- `GeniaConfigProvider`
- `GeniaDeclassificationAuthority`
- `GeniaModelProvider`
- `GeniaEmbedProvider` and other retrieval/model provider capabilities
- `GeniaIndexHandle`
- `GeniaPythonHandle`
- `GeniaOutputSink`
- `GeniaStdinSource`
- lifecycle scope/definition/attachment values that contain or denote executable/runtime behavior
- future `Store`, execution, actor, job, subscription, or similar live capability/handle values unless a later approved contract deliberately classifies a particular type as an opaque semantic token instead

Two separately created identity-bearing values are unequal even when their visible state/configuration happens to match. Aliases to the same logical entity compare equal.

#### Opaque semantic-token family

No general source-level user-defined token facility is implemented today. R18 nevertheless defines the reusable equality family so future features do not need to invent a new relation.

An opaque semantic token carries, conceptually but not necessarily inspectably:

- token domain
- provenance/issuing authority
- immutable opaque semantic identity

Two tokens compare equal only when their token domains are the same, their provenance/authority is compatible according to the token-domain contract, and their immutable opaque semantic identity denotes the same semantic fact. Comparison itself performs no IO or callback to the issuer.

Future storage `Revision` is the motivating example. Future undefined built-in token kinds and future user-defined token domains may use the same closed equality family. R18 does not define syntax, minting APIs, serialization, ordering, or map-key legality for such future tokens.

#### Protected-carrier family

`GeniaProtected` is a special opaque leaf whose ordinary equality is carrier identity only. Same provider, same purpose, and equal secret payload are insufficient to make independently acquired carriers equal. Payload comparison requires explicit authorized declassification followed by ordinary equality of the declassified values.

This is a security boundary, not merely a representation choice.

#### Explicitly internal / not promoted to public value equality

- AST and Core IR node objects
- parser/pattern compiler helper objects such as compiled glob tokens
- `Env`, debug hooks/controllers, source spans
- `TailCall` trampoline objects
- Python transport request/response helper objects that never cross the Genia value boundary
- Python tuple acceptance inside `_freeze_map_key` is implementation accommodation unless/until a public Genia tuple value is established; R18 must not promote host-internal tuples into a new public value family
- Python `None` acceptance in internal map freezing is not by itself authority to introduce a new source-visible map-key form distinct from Genia's established absence/Outcome semantics

### Exact numeric matrix to formalize

| Left | Right | R18 relation |
|---|---|---|
| `1` | `1` | equal |
| `1` | `2` | unequal |
| `1` | `1.0` | equal iff the float exactly denotes the same mathematical integer |
| `1` | `1.5` | unequal |
| `true` | `1` | unequal |
| `false` | `0` | unequal |
| `0.0` | `-0.0` | equal |
| `+inf` | `+inf` | equal where infinities are supported |
| `+inf` | `-inf` | unequal |
| `NaN` | any value, including itself | unequal |

For int/float comparison, no lossy conversion of an arbitrary-precision integer to float is permitted. A float equals an integer only when the float is finite, integral, and its exact mathematical value is that integer. This preserves the R17 arbitrary-precision integer boundary.

### Map-key relation to formalize

For every **legal public map key**, map equivalence is the same semantic relation as `==`:

- if `a == b`, lookup through either key addresses the same mapping
- replacement through an equal key replaces that mapping and preserves the R17 position rule
- removal through an equal key removes that mapping
- duplicate-key detection treats equal keys as one mapping
- unequal legal keys must not collapse due to host container semantics
- internal canonicalization/hash behavior is implementation detail, but equal legal keys must have identical internal key equivalence/hash treatment

Every legal map key must be reflexive (`k == k`). Therefore NaN is illegal as a key, and an otherwise-keyable structural key containing NaN in an equality-relevant position is illegal.

R18 does not expand the public keyable family. Current `_freeze_map_key` evidence shows primitive values, symbols, pairs, represented values, lists, and host tuples are handled by Python while protected values, declassification authorities, index handles, and unrecognized runtime objects are rejected. The portable contract will preserve established public key families while refusing to promote Python-only tuple/`None` accommodations into new public syntax or value categories.

Map equality itself compares mappings and is independent of insertion history. R17 deterministic order remains observable through map iteration/accessor/display surfaces exactly as already contracted.

### Protected-value security rule to formalize

Code without matching declassification authority must not derive protected payload information through:

- `==` / `!=`
- recursive structural equality
- hashing/canonicalization/keying
- ordering
- literal or duplicate-binding pattern matching
- serialization
- diagnostics/display/debug rendering
- container duplicate/lookup behavior

Protected carriers remain illegal map keys. Equality may reveal only carrier sameness, never carried-value sameness.

### Current equality-like behavior reconciliation

The contract phase must make the following one semantic relation:

- public `a == b`
- public `a != b`, defined as logical negation of `a == b`
- `assert_eq(actual, expected)` pass/fail condition
- literal-pattern matching
- duplicate-name pattern binding consistency (`f(x, x)` and equivalent nested cases)
- recursive equality within List, Pair, Outcome, represented values, Sheet/ordinary data values, and maps
- map lookup, replacement, removal, and duplicate-key detection for legal keys
- any validation/template/representation code that currently uses host equality to answer a semantic Genia sameness question

Domain-specific equivalence remains a separate ordinary predicate. Future R20 open functions may make such predicates extensible, but neither open functions nor user code may redefine `==`, duplicate-pattern binding semantics, or map-key identity.

### Python implementation today

Python reference-host behavior is mixed:

- scalar Python values often inherit Python equality, including Python's `True == 1` behavior
- dataclasses may accidentally gain field-structural equality
- ordinary classes without `__eq__` often gain allocation identity
- `GeniaProtected` has a custom payload-comparing `__eq__`
- `GeniaMap` has no portable structural `__eq__`; separately constructed maps compare by Python object identity
- map key equivalence is currently mediated by `_freeze_map_key` and Python dict semantics
- pattern and assertion paths call Python equality independently

R18 intentionally replaces this accidental mixture with written Genia semantics.

### Not implemented

- the portable equality primitive/dispatcher
- structural map `==`
- protected carrier-identity-only equality
- the NaN legal-key restriction
- general opaque semantic-token values or token-domain APIs
- a storage `Revision`
- user-defined token domains
- C++ implementation

---

## 5. TEST STRATEGY

No tests are created in E18-0. The following are targets for the later TEST phases.

### Core invariants

1. One Genia equality relation governs every equality-like semantic surface.
2. Equality is pure and capability-free.
3. Structural recursion terminates at identity, opaque-token, and protected leaves.
4. Numeric equality is exact and host-independent.
5. Map equality is mapping equality, not iteration-order equality.
6. Every legal map key is reflexive.
7. Equal legal map keys are interchangeable for every map operation.
8. Protected equality reveals no protected payload information.
9. Opaque-token equality is issuer-call-free and non-user-overloadable.
10. Existing parse/Core IR shapes remain unchanged.

### Expected behavior targets

- independently constructed equal Lists/Pairs/Outcomes/represented values compare equal
- independently constructed maps with equal mappings but different insertion histories compare equal
- `1 == 1.0`; large integer/float edge cases obey exact representability rather than lossy coercion
- `true != 1`, `false != 0`
- `0.0 == -0.0`
- `NaN != NaN`
- same runtime handle alias compares equal; separately created handles with equivalent state compare unequal
- same protected carrier alias compares equal; independently acquired carriers compare unequal regardless of payload equality
- duplicate pattern bindings use exactly the same equality results as public `==`
- `assert_eq(a,b)` succeeds iff `a == b`

### Failure cases

- NaN as a legal-key candidate is rejected deterministically
- structural legal-key candidate containing equality-relevant NaN is rejected
- unsupported/non-keyable runtime values remain rejected as keys
- no protected payload appears in equality-related diagnostics
- no equality attempt consumes Flow/Seq, dereferences Ref, invokes Template/function/provider/token issuer, performs IO, or mutates state

### Test approach

Later slices should use shared `eval`/`error` cases for portable observable behavior plus focused Python unit/native tests for non-leakage, no-callback/no-consumption guarantees, identity aliasing, and internal key consistency. Shared cases must be executable through the existing R16 generic external-host protocol without protocol changes.

---

## 6. EXAMPLES

These are pre-flight examples of the intended contract direction, not current implemented truth.

### Minimal

```genia
1 == 1.0       # intended R18: true
true == 1      # intended R18: false
[1, 2] == [1.0, 2.0]  # intended R18: true
```

### Real

Two maps built in different insertion histories but denoting the same mapping compare equal while preserving their independently observable R17 iteration orders.

A future storage provider can materialize two opaque `Revision` token values for the same semantic revision and have them compare equal using immutable hidden domain/provenance/identity data, without equality calling the provider. A future user-defined token domain may reuse that same token equality family, but may not supply an equality callback.

---

## 7. COMPLEXITY CHECK

- [ ] Adding gratuitous complexity
- [x] Revealing structure

Justification:

The current implementation already contains several implicit equality systems. R18 reduces conceptual complexity by naming one semantic relation and routing maps, patterns, assertions, structural values, identity values, protected values, and future opaque tokens through explicit fixed rules. The primary implementation complexity is unavoidable portability/security work that already exists implicitly in Python behavior.

---

## 8. CROSS-FILE IMPACT

Files likely to change in later phases:

- `src/genia/evaluator.py`
- `src/genia/values.py`
- `src/genia/pattern_match.py`
- `src/genia/builtins.py`
- runtime value modules such as `callable.py`, `model.py`, `retrieval.py`, `sheet.py`, lifecycle/HTTP modules where classification needs explicit support
- `spec/eval/*.yaml`
- `spec/error/*.yaml`
- focused unit/native tests
- `docs/design/r18-portable-value-equality-contract.md`
- `GENIA_STATE.md`
- `GENIA_RULES.md`
- `GENIA_REPL_README.md` / `README.md` only where public wording is affected
- `docs/contract/semantic_facts.json` and its sync tests if equality facts warrant protected cross-doc anchors
- `docs/releases/R18.md`
- R18 roadmap status files at completion

Risk of drift:
- [ ] Low
- [ ] Medium
- [x] High

Reason: equality crosses core evaluator semantics, container keying, pattern dispatch, assertions, security-sensitive protected values, and future host implementations.

---

## 9. DOC DISTILLATION CHECK

Creates process artifacts?
- [x] YES → run Doc Distillation
- [ ] NO

Adds docs/design or docs/architecture files?
- [x] YES → classify KEEP / EXTRACT / DELETE
- [ ] NO

Expected durable artifact: `docs/design/r18-portable-value-equality-contract.md` if approved through contract/design gates.

Doc drift risk:
- [ ] Low
- [ ] Medium
- [x] High

Temporary handoff artifacts must not become alternate semantic truth. `GENIA_STATE.md` remains final authority for implemented behavior.

---

## 10. PHILOSOPHY CHECK

- preserves minimalism? YES
- avoids hidden behavior? YES
- keeps semantics out of host? YES
- aligns with pattern-matching-first? YES

Notes:

- one fixed equality relation is simpler than host-specific or user-overloadable equality
- duplicate binding equality becomes explicit and consistent with public `==`
- map keys cease depending on undocumented Python dict behavior
- opaque semantic tokens provide a reusable future concept without adding token syntax now
- protected carrier identity closes an equality oracle rather than expanding authority

---

## KILLER WORKFLOW ALIGNMENT

Does this change directly strengthen Outcome-aware validated data pipelines?

- [ ] Yes
- [x] Indirectly
- [ ] No

R18 is portability infrastructure with direct semantic consequences for data workflows. Validated pipelines routinely compare scalar/structured values, use map records, pattern matching, Outcomes, Sheets, and assertions. A host-independent equality/key contract prevents the same pipeline from validating, matching, deduplicating, or looking up records differently when moved from the Python reference host to a future host. The protected-value rule also prevents equality from becoming an authority bypass in configuration-backed pipelines.

This work belongs now rather than the parking lot because R18 is the next planned release, R17 explicitly deferred map equality to it, and the planned minimal C++ host depends on an approved R18 contract.

---

## 11. PROMPT PLAN

Pipeline for E18-0:

1. Pre-flight — this artifact only
2. Contract — behavior only; no tests/specs
3. Design — implementation/spec touchpoints without implementation
4. explicit GO/NO-GO for E18-1

Release pipeline after E18-0 approval:

- E18-1 structural + numeric equality
- E18-2 map equality/key equivalence/legal keys
- E18-3 identity + opaque-token + protected equality
- E18-4 equality-like surface reconciliation
- E18-5 multi-host conformance hardening
- E18-6 authoritative docs/release truth sync
- E18-7 skeptical audit + distillation

Each implementation slice must still run its required failing-test-before-implementation workflow. Do not infer implementation authorization from this pre-flight.

---

## FINAL GO / NO-GO

Ready to proceed to the E18-0 CONTRACT phase?

**YES — GO for contract only.**

Missing:

- none for contract entry

Hard stop remains in force for this artifact: no runtime implementation, shared tests/specs, authoritative implemented-truth claims, storage/token APIs, or C++ work have been added here.
