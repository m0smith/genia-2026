# Genia Provider Composition — Stage 0 Retrospective and Work Ledger

Status: **Analysis / architecture preflight input — non-authoritative and not implemented.**

`GENIA_STATE.md` remains final authority for implemented Genia behavior. This file records evidence, settled conclusions, unresolved design questions, and an ordered work ledger so provider/component work can proceed methodically without reopening the same architectural ground.

## Why this file exists

A review of Genia's current FFI direction against WebAssembly Interface Types (WIT) initially suggested a new component/interface/provider architecture. Independent review of the repository showed that this framing was too external-first: Genia has already implemented and audited much of the provider pattern in R11, R12, R14, R16, and R18.

The working conclusion is therefore:

> Genia should first extract and generalize the provider architecture it already has, then design only the missing whole-program composition, resource-lifetime, cross-language-boundary, and failure-layer semantics. WIT is a comparison target and potential interoperability target, not the semantic authority for Genia.

This file is intentionally not a contract, syntax proposal, roadmap release, or authorization to implement new runtime behavior.

The focused architecture preflight in
`docs/analysis/provider-composition-preflight.md` resolves work-ledger rows P0,
P1, P2, P5, P6, and P7. Those resolutions remain non-authoritative
architecture analysis: they add no implemented behavior and do not block
R24-R31.

## Source-of-truth and evidence basis

Read these before changing the conclusions in this file:

- `AGENTS.md`
- `GENIA_STATE.md`
- `GENIA_RULES.md`
- `GENIA_REPL_README.md`
- `README.md`
- `docs/strategy/killer-workflow.md`
- `docs/strategy/release-roadmap.md`
- `docs/design/r9-value-template-representation-contract.md`
- `docs/design/r10-configuration-protected-value-contract.md`
- `docs/design/r11-ai-composition-contract.md`
- `docs/design/r12-retrieval-grounding-contract.md`
- `docs/design/r14-composable-lifecycle-contract.md`
- `docs/design/r16-multi-host-conformance-infrastructure-contract.md`
- `docs/design/r18-portable-value-equality-contract.md`
- `docs/design/r20-open-functions-contract.md`
- `docs/design/r21-numeric-source-portable-representation-contract.md`
- `docs/design/r22-exact-numeric-runtime-contract.md`
- `docs/architecture/execution-realization.md`
- `docs/strategy/roadmap/r21-r24.md`
- `docs/strategy/roadmap/r35-r37.md`

External precedent to review only after the Genia evidence above:

- WebAssembly Component Model / WIT interfaces, worlds, resources, ownership/borrowing, composition, and Canonical ABI
- WASI 0.3 async `stream<T>` / `future<T>` work

## Classification used below

| Classification | Meaning |
| --- | --- |
| **PROVEN** | Existing implemented/audited Genia behavior substantially answers the question. |
| **PARTIAL** | Strong precedent exists, but generalization still needs an explicit design decision. |
| **NEW** | Existing releases do not provide the semantic mechanism. |
| **PLANNED PRECEDENT** | Not implemented, but current roadmap already assumes a closely related shape. |
| **DEFER** | Important, but intentionally outside the first component/provider generalization. |

## Stage 0 evidence matrix

| Proposed concept | Existing Genia evidence | Status | Stage 0 conclusion |
| --- | --- | --- | --- |
| Opaque provider capability | R11 defines one opaque host-injected provider capability; R12 repeats the pattern for embedding/indexing/retrieval/reranking. | **PROVEN** | Do not invent a new provider object model. Generalize the existing opaque-capability pattern. |
| Explicit provider rather than ambient lookup | R11 rejects provider registries, name dispatch, ambient providers, source-visible provider factories, and implicit config; R12 follows the same pattern. | **PROVEN** | No ambient provider registry should be a general invariant. |
| Ordinary callables at provider boundaries | R11 `model/4` and R12 provider constructors return ordinary callables and reuse existing Outcome/pipeline composition. | **PROVEN** | Do not add a second invocation language or provider-specific call syntax merely to support components. |
| Ordinary portable values outside providers | R11 and R12 keep requests/results as ordinary Genia values while SDK/wire objects remain host-local. | **PROVEN** | Preserve the rule: semantic values above the boundary, provider-native representation below it. |
| Provider substitution | R12 explicitly permits replacing an embedder when the replacement preserves the declared embedding `space`; incompatible replacements require re-embedding/re-indexing. | **PROVEN, domain-scoped** | Provider substitution is already acceptable when semantic compatibility is explicit. Generalization must preserve that rule. |
| Compatibility stronger than signature matching | R12 `index_handle`/retrieval compatibility uses hidden identity plus exact `space`/`dims` checks before an attempt. | **PROVEN** | Provider compatibility cannot be duck typing by function names alone. |
| Opaque provider-produced handle | R12 `index_handle` is opaque, host-produced, non-constructible, non-inspectable, non-keyable, non-serializable, and non-persistable. | **PROVEN** | This is an existing concrete precursor to a component resource. |
| Identity-bearing provider/resource semantics | R18 classifies providers, authorities, host handles, retrieval handles, Flow/Seq, processes, etc. as identity-bearing runtime values. Future live Store/execution/actor/job/subscription handles default to this family unless another approved contract says otherwise. | **PROVEN** | Reuse R18 identity; do not create component-local equality rules. |
| Opaque semantic token distinct from live resource | R18 separately defines opaque semantic tokens and uses future storage `Revision` as the motivating example. | **PROVEN** | Keep immutable semantic tokens separate from live resource handles. |
| Explicit authority separate from provider capability | R11/R12 require provider capability, protected credential, and purpose-scoped authority separately; declassification happens immediately before the attempt. | **PROVEN** | Capability availability and authority to perform an effect remain distinct. |
| Provider binding as attachment, not acquisition | R14 `lifecycle_config(provider)` captures an already-constructed provider, performs no acquisition/refresh/ambient lookup, and explicitly rejects dependency injection/service-container semantics. | **PROVEN** | Realization may attach providers; it must not silently discover/acquire them. |
| Lifecycle foundation for resources | R14 provides deterministic scope enter/work/reverse-unwind and ownership isolation among peers. | **PROVEN FOUNDATION** | Future resource lifetime should reuse R14 rather than add a second cleanup model. |
| Owned/borrowed/expired resource semantics | R14 provides scopes/lifetimes, but there is no general component-level owned vs borrowed handle contract or general escape rule. | **NEW** | This is genuinely new work and should be a narrow extension over R14/R18. |
| Provider construction is inert | R11/R12 constructors capture explicit capability/config/credential/authority and do not perform provider IO. | **PROVEN** | Component/interface declaration and binding should stay inert unless a later contract explicitly says otherwise. |
| Provider failure normalization | R11/R12 normalize timeout/rejection/rate-limit/transport/malformed-response failures and strip raw host exception/provider details. | **PROVEN** | Raw host exceptions stay below any portable provider boundary. |
| Universal provider-result envelope distinct from Outcome | R11/R12 encode provider failures as ordinary `err(...)` Outcomes; R36 separately plans execution/provider failure categories. | **UNRESOLVED / NEW** | Do not claim a two-envelope model exists. The operation/provider/execution failure seam must be designed explicitly. |
| Concern-sized providers | R12 uses separate embed/index/retrieve/rerank capabilities rather than one universal backend object. | **PROVEN** | Prefer capability-sized interfaces; avoid god-provider objects. |
| Application owns composition | R11 keeps prompt/chains/conversation state in ordinary functions/pipelines/`scan`; R12 keeps grounding assembly ordinary. | **PROVEN** | Provider/component machinery must not become a workflow engine. |
| Whole-computation `requires` inventory | No implemented application-facing construct describes a complete capability footprint. R16, however, already proves the enforcement shape: shared cases declare `requires`, hosts advertise capability support, and unsupported requirements fail closed without invoking the adapter or counting as pass. | **NEW application concept; PROVEN enforcement shape** | Novelty is application-level declaration/meaning, not declare/check/fail-closed mechanics. Reuse R16's discipline. |
| Whole-computation `provides` inventory | Modules/R20 export names and contributions, but no component-level semantic export contract exists. | **NEW** | Design with `requires`; do not confuse module exports with provider/component exports. |
| Explicit transitive provider graph | Existing APIs compose providers manually; there is no general inspectable provider dependency graph. | **NEW** | Likely later than the first requires/provides proof. If added, it must remain explicit, inert, and non-ambient. |
| Interface identity | R20 has explicit interface/contribution identity; R12 has hidden compatibility identity. | **PARTIAL** | There is strong identity precedent but no general component-interface identity/revision model. |
| Interface revision/version negotiation | R16 has contract revisions; R12 has compatibility labels; R36 plans compatibility/capability revision negotiation. | **PARTIAL** | Start with exact identity/revision matching. Do not infer SemVer compatibility initially. |
| Provider conformance evidence | R16 has deterministic capability/conformance evidence; R11/R12 have deterministic provider fixtures and exact normalization contracts. | **PARTIAL** | Ingredients exist, but no reusable `provider implements interface X` conformance protocol exists yet. |
| Canonical cross-language component value boundary | Core IR is a portability boundary for Genia semantics; R11/R12 have capability-specific conversions; R21/R22 settle numeric source/runtime and R23 completes interchange. | **RESOLVED BELOW (P3/P4, INCLUDING NUMERIC)** | Preserve the full P3/P4 model, numeric and non-numeric alike, now that R23 is complete. Do not make Python conversion rules the ABI. |
| Canonical component resource boundary | R18 identity plus R12 opaque handles provide ingredients, but no Python/C++/Wasm-neutral resource-handle contract exists. | **NEW** | Likely a small handle identity/lifetime contract, not serialization of underlying objects. |
| Raw FFI underneath a portable provider | Current FFI is explicitly host-specific; R11/R12 private host adapters already hide Python provider mechanics behind portable Genia values. | **PARTIAL** | Prove that raw FFI can implement a provider without leaking host specificity into application source. |
| Actual WIT provider | No current Genia/WIT component integration. | **NEW** | Use as a later interoperability proof, not as the starting semantic model. |
| Export Genia as a WIT/component provider | No current mechanism. | **NEW / DEFER** | Consumer/provider model first. |
| Flow ↔ WIT `stream<T>` / `future<T>` | Genia Flow has its own lazy pull/single-use/bounded-demand contract. | **NEW / DEFER** | Separate design for buffering, demand, cancellation, cleanup, and backpressure. No implicit equivalence. |
| Provider placement/remoting | `execution-realization.md` and planned R36 already separate logical computation from physical placement/infrastructure. | **PLANNED PRECEDENT** | Provider binding must not imply transparent remoting or erase distributed failure semantics. |
| Store as provider/resource | R35 plans bounded identity-bearing `Store`, Store-relative `Location`, opaque `Revision`, provider mechanics below portable semantics. | **PLANNED PRECEDENT** | R35 should consume a general model if ready rather than invent another independent provider pattern. |
| Execution as provider/resource | R36 plans portable `Execution`, opaque `ExecutionHandle`, capability/authority requirements, and normalized execution/provider failures. | **PLANNED PRECEDENT** | R36 is a major consumer, but its heavy execution boundary must not automatically govern same-process provider calls. |
| R37 as composed proof | R37 plans Genia-native tooling that discovers through R35 and invokes hosts through R36. | **PLANNED INTEGRATION PROOF** | Explicitly use R37 to test composition of multiple provider-shaped abstractions. |
| Provider binding vs R20 open-function dispatch | R20 links selected contribution units into an immutable lexical function view and dispatches by argument pattern/guard at call time. | **DISTINCT** | R20 is not provider resolution. Provider binding chooses realization before/around calls; R20 chooses clauses from already-linked semantics per call. |

## Settled house rules to preserve

These should be treated as constraints on later design unless a future contract explicitly overturns one:

1. Providers are opaque capabilities, not source-visible provider class hierarchies.
2. Providers are explicit, not ambient.
3. Provider construction/binding is inert.
4. Binding/attachment does not acquire or discover a provider.
5. Ordinary Genia values form the semantic API boundary; provider-native objects stay private.
6. Provider-backed behavior composes through ordinary callables, Outcomes, functions, and existing pipelines.
7. Provider replacement requires semantic compatibility, not matching method names.
8. Providers and live handles use R18 identity-bearing equality semantics.
9. Opaque immutable tokens such as future `Revision` remain distinct from live resources.
10. Authority is explicit and separate from provider identity/capability.
11. Raw host errors/details do not cross the portable boundary unnormalized.
12. Provider machinery does not become a workflow engine, service locator, dependency-injection container, or ambient registry.
13. Missing declared capability support fails closed; R16's `requires`/capability discipline is the precedent for enforcement shape.
14. Host portability, component/provider portability, raw FFI, and execution placement remain separate axes.

## Genuinely new core

After accounting for existing R11/R12/R14/R16/R18 evidence, the first design surface is much smaller than the original WIT-first proposal implied.

### A. Whole-program requires/provides semantics

Question: should a Genia computation have an explicit, inspectable external capability contract analogous in purpose to a WIT world?

The open problem is the **application-level semantic meaning and scope** of such a declaration. R16 already proves the mechanical pattern of declared requirement + advertised support + deterministic fail-closed gating.

Do not assume new syntax is necessary. First prove that an application-facing manifest expresses something materially unavailable through explicit arguments/modules alone: whole-program inspectability, authority analysis, provider composition, portability checks, or execution realization.

### B. Resource ownership across provider boundaries

R14 supplies scope ownership/unwind and R18 supplies identity-bearing equality. Missing is the bridge:

```text
resource
  owned   -> lifetime tied to one owner/scope
  borrowed -> usable only for a bounded call/scope
  expired -> deterministic rejection after lifetime
```

The hard questions are escape and transfer:

- may a borrowed resource be returned?
- may it be inserted into a List/Map?
- may a closure capture it?
- may a Flow retain or emit it?
- may ownership move to a child scope?
- may an owned resource cross an R36 execution boundary?

### C. Canonical component boundary

Need one host-neutral contract for values/resources crossing a provider boundary. This is distinct from:

- portable Core IR, which defines Genia execution semantics;
- a host's native objects;
- R11/R12's capability-specific private conversions.

This must preserve Genia's own semantics for Outcome, maps/order/equality,
representations, protected values, diagnostics, and—now that R23 is
complete—Integer/Decimal/Rational/Float64 interchange, per the frozen P3/P4
sections below.

### D. Failure layering

R11/R12 normalize provider failures into ordinary `err(...)` Outcomes. R36 plans a separate execution-level taxonomy. A general provider model must decide where these layers meet.

The design must distinguish at least conceptually:

```text
operation semantic result
same-process provider realization failure
R36 execution/placement failure
```

Do not create duplicate meanings for timeout, unauthorized, incompatible, provider failure, or cancellation across overlapping envelopes.

## P3 — Provider-boundary value inventory

Status: **RESOLVED/FROZEN FOR ARCHITECTURE.** With R23 complete, the
Integer/Decimal/Rational/Float64 rows below close the previously blocked
numeric cells alongside the already-resolved non-numeric inventory. This is a
non-authoritative admissibility inventory, not implemented serialization
behavior, and it selects no wire encoding for any value family, numeric or
otherwise.

The inventory applies PAI-3 without turning every runtime value into portable
data. A value may cross only when its complete semantic value can survive the
crossing. Host/SDK objects, live identity, authority, lifetime, executable
behavior, and private exception data are not ordinary boundary payloads.

### Recursive admissibility rule

A structural value is portable only when:

1. its value family has an approved boundary treatment;
2. every recursively reachable semantic field, key, value, Outcome field, and
   representation-metadata field is portable;
3. every map key is legal under R18 and retains the same canonical key identity;
4. no borrowed carrier, local-only value, protected payload exposure, or raw
   provider/native exception detail occurs anywhere in the graph; and
5. construction is within the applicable contract's size/depth/resource limits.

One inadmissible leaf makes the complete attempted payload inadmissible. The
crossing is rejected deterministically before provider invocation (or, for a
provider-produced result, at the adapter's return boundary before application
observation). It is P6 Layer-2 boundary misuse, not an interface operation
`err(...)`. A contract may instead define a different portable snapshot,
descriptor, or semantic token, but that is a distinct value and is never
inferred from the live value.

### Value-family matrix

“Structural record” below means an ordered, explicitly tagged semantic record;
it does not select JSON, a host dictionary, or a wire encoding.

| Value family | Current semantic category | Crosses? | Conditions and canonical non-numeric treatment | Identity/equality and authority/protection | Evidence | Deferred/open question |
| --- | --- | --- | --- | --- | --- | --- |
| `none(reason, context?)` | Outcome / structural value | **Conditional** | Preserve the Outcome variant and recursively portable reason/context; bare `none` preserves its canonical absence meaning. | R18 recursive Outcome equality; no raw exception or sensitive context. | `GENIA_STATE.md` §2; R18 “Structural values”; R10 diagnostics. | Numeric fields remain blocked as below. |
| `some(value[, context])` | Outcome / structural value | **Conditional** | Preserve the variant, value, and optional context exactly; all fields must pass recursive admissibility. | Structural equality; protection is never stripped. | `GENIA_STATE.md` §2; R18; R9 Outcome interaction. | None beyond recursively deferred fields. |
| `err(reason, context?)` | Outcome / structural value | **Conditional** | Preserve normalized, non-sensitive semantic reason/context; adapter must normalize and discard raw host/provider exception data first. | Structural equality; protected leaves cannot become rendered diagnostics. | R11/R12 normalization; R10 errors; PAI-8/P6. | Interface contracts continue to own their reason/context vocabulary. |
| Bool | Ordinary immutable scalar | **Portable** | Preserve `true`/`false` as Bool, distinct from Integer. | Structural; Bool and Integer are distinct keys. | R18 equality and key rules. | None. |
| String | Ordinary immutable Unicode scalar | **Portable** | Preserve exact Unicode scalar sequence; not display/debug text. | Structural and keyable under R18. | R19 as summarized by `GENIA_STATE.md`; R18. | Codec/text encoding is outside P4. |
| Symbol / quoted identifier | Ordinary immutable symbol scalar | **Portable** | Preserve Symbol kind and exact name; do not reduce it to String. Quoted strings remain Strings. | Structural and keyable; symbol/string identity stays distinct. | `GENIA_STATE.md` §4.1; `GENIA_RULES.md` §9.2; R18. | No new general quotation/token family. |
| List | Ordinary immutable ordered container | **Conditional** | Ordered sequence of recursively portable elements. | Recursive structural equality; legal key use follows R18, not host hashing. | `GENIA_STATE.md` §2; R18. | Size/resource limits belong to a later codec/ABI contract. |
| Pair | Ordinary structural value | **Conditional** | Explicit pair with recursively portable `car` and `cdr`; never silently flattened to a List. | Recursive structural equality and existing key rules. | `GENIA_STATE.md` §2; R18 structural families. | Promise-backed streams are local because Promise is local-only. |
| Tuple | Full argument-tuple/pattern mechanism; no current public ordinary Tuple value family | **Explicitly deferred** | No provider-boundary Tuple tag is invented. Public sequence data uses List or an explicitly contracted record/pair. | Host tuple identity/layout has no semantic authority. | `GENIA_RULES.md` §4; R18 map-key section explicitly rejects host tuples as authority for a public kind. | A future public Tuple value would need its own contract. |
| Map / ordered map | Persistent ordered structural container | **Conditional** | Preserve deterministic entry order and each recursively portable key/value. Encode as an ordered entry sequence at the semantic layer, not a JSON object or host dictionary. | Key legality and canonical identity are exactly R18; equal cross-kind legal keys remain one entry identity, including numeric keys per the Integer/Decimal/Rational/Float64 rows below. | `GENIA_STATE.md` §§2, 7.2; R17/R18; R9 JSON distinguishes object mapping. | None; numeric key representation is resolved in the numeric rows below. |
| Sheet | Immutable structural columnar value | **Conditional** | Preserve ordered columns and rows/cells only when column identifiers and every cell are recursively portable; do not lower implicitly to CSV or maps. | R18 names semantic fields; no live backing identity crosses. | `GENIA_STATE.md` §3.2; R18 structural families. | A codec schema/layout remains future work. |
| Bytes | Immutable structural byte value | **Portable** | Preserve exact byte sequence as Bytes, not Unicode String or rendered/base64 text. | Structural equality; current non-keyability remains. | `GENIA_STATE.md` Bytes/JSON/ZIP section; R18. | Wire encoding is unspecified. |
| ZIP entry | Immutable structural descriptor/value | **Conditional** | Preserve its contract-defined semantic fields recursively; no open archive/file handle crosses. | Structural equality over named semantic fields. | R18 “RNG, Format, bytes, ZIP entries, Sheets…” | Codec/schema is unspecified. |
| Format value | Immutable structural formatting value | **Conditional** | Preserve contract-defined format structure and recursively portable semantic fields; never substitute rendered output. | R18 structural equality; protected replacement rules still apply. | R18 structural families; current Format rules in `GENIA_STATE.md`. | Boundary schema is not selected here. |
| Deterministic RNG state | Immutable structural state value | **Conditional** | May cross only when the public deterministic algorithm/state contract is preserved exactly; host RNG objects never cross. | Structural equality over deterministic state. | R18; `GENIA_STATE.md` random helpers. | General algorithm/version negotiation is not defined here. |
| Inert closed operation/data descriptors | Ordinary immutable structural values | **Conditional** | Preserve only explicitly public, immutable semantic fields recursively (for example a plain `ResourceRef` map or inert HTTP operation value); do not include live handles. | Equality follows the owning descriptor contract and R18. | R18 structural family; `GENIA_STATE.md` resource/HTTP sections. | Each descriptor contract decides admission; no reflection-based auto-serialization. |
| R9 represented value | Representation carrier / structural value | **Conditional** | Preserve the exact ordered facet stack plus recursively portable carried value and portable facet metadata. Never collapse to display text, JSON text, or the unrepresented value. | R9 recursive equality and facet order remain authoritative; reserved/protected facets retain stronger rules. | R9 “Representation value model”, “Identity, equality, and keys”. | Provider-owned facet metadata needs an owning contract. |
| R10 protected carrier | Protected identity-bearing carrier | **Conditional, fail closed** | Crossing is allowed only if the boundary can preserve the same opaque protected carrier and all R10 sink/declassification rules without exposing/reconstructing its payload. Transport must never become declassification. Otherwise reject. | Carrier-identity equality; never a map key; only matching scoped authority may reveal immediately at an authorized sink. | R10 protected carrier, transport, sinks, declassification; R18 protected family. | Cross-process/cross-provider reconstruction or credential transport is **deferred**; no rule is invented here. |
| Approved opaque semantic token | Immutable opaque semantic token | **Contract-specific conditional** | Crosses only when its owning contract explicitly defines boundary materialization preserving hidden domain/provenance/semantic identity. Token crossing is not live-handle identity transfer. | R18 three-component equality, with no callback/IO/exposure. | R18 “Opaque semantic tokens”; P5 uses the category conceptually. | No generic token reconstruction, schema, or minting rule. |
| Integer | Numeric semantic scalar; arbitrary-precision exact integer (R17/R22 §1) | **Portable** | Preserve the exact arbitrary-precision mathematical Integer value and its distinct kind (never Bool, never folded into Decimal/Rational/Float64). The boundary role is the exact value itself, analogous to String's "exact Unicode scalar sequence"; it is neither R23's canonical decimal-digit display spelling (a rendering surface) nor R23's JSON safe-integer interval `[-9007199254740991, 9007199254740991]` (a JSON-specific interoperability restriction this boundary does not inherit). A realization may materialize it as canonical decimal digit text or a native big-integer type, but never a fixed-width silent-truncation host integer. | R18/R22 mathematical-value equality and canonical key identity; Integer and Bool remain distinct kinds/keys; a boundary-crossed Integer participates in R22 §10.1 cross-family equality (for example `1 == 1.0`) without losing its own Integer kind tag. | R17; R22 §1, §10.1; R18 key rules; R23 §2.1, §4.1 (contrasted, not adopted as boundary rule). | Per-realization magnitude/resource-limit ceilings are R22 §11's normalized `numeric-resource-limit` concern, not defined here; no wire width is chosen. |
| Decimal | Numeric semantic scalar; arbitrary-precision exact `coefficient * 10^exponent` value (R22 §2) | **Conditional** | Crosses only when the exact canonical `(coefficient, exponent)` pair after R22 §2 canonicalization (trailing-zero-stripped coefficient, sign carried by coefficient, no Decimal negative-zero identity, Decimal kind retained even for mathematically integral values) is preserved. The boundary role is this exact coefficient/exponent structural pair -- not R23 §2.2's fixed/scientific display spelling, and not R23 §4.2's `stable_json_decimal`-gated JSON number token, which is a strictly narrower, lossy-by-design JSON interoperability rule this boundary does not inherit or bypass. A realization may materialize the pair as two arbitrary-precision Integers, or as a canonical decimal string it parses lexically back into the exact pair, but never through a host binary float and never through a `stable_json_decimal`-style stability gate. | R18/R22 mathematical-value equality and canonical key identity; a boundary-crossed Decimal must reconstruct to the identical canonical `(coefficient, exponent)` pair so R18 map-key identity and R22 §10.1 cross-family equality behave identically before and after crossing. | R22 §2, §10.1; R18; R23 §2.2, §4.2 (contrasted, not adopted). | Concrete coefficient/exponent wire encoding is a later codec choice, not fixed here; R22 §11 resource limits on coefficient/exponent magnitude apply unchanged. |
| Rational | Numeric semantic scalar; exact reduced ratio of arbitrary-precision Integers (R22 §3) | **Conditional** | Crosses only when the exact canonical `(numerator, denominator)` pair after R22 §3 canonicalization (denominator positive and greater than `1` for a surviving Rational; sign carried by numerator; gcd-reduced) is preserved. A non-terminating Rational such as `1/3` crosses this boundary as an exact Rational: R23 §4.3's rule that a Rational is JSON-encodable only when it has a finite `stable_json_decimal`-satisfying Decimal equivalent is a JSON-specific interoperability restriction, not a provider-boundary admissibility rule, and is not inherited here. The boundary role is the exact numerator/denominator structural pair, not R23 §2.3's `<numerator>/<denominator>` display spelling. A realization may materialize the pair as two arbitrary-precision Integers or as a lexically parsed canonical `<numerator>/<denominator>` string reconstructed into the exact pair -- never through a host float or a finite-decimal intermediate. | R18/R22 mathematical-value equality and canonical key identity; cross-family equality with Integer/Decimal must hold identically after crossing (a denominator-one Rational already collapsed to Integer before construction, so it is never observed as a "surviving" Rational at the boundary either). | R22 §3, §10.1; R18; R23 §2.3, §4.3 (contrasted, not adopted). | Wire encoding for the two Integer components is a later codec choice; numerator/denominator magnitude limits reuse R22 §11 unchanged. |
| Float64 | Numeric semantic scalar; one explicit IEEE-754 binary64 bit pattern, an explicit approximate domain distinct from the exact family (R22 §4) | **Conditional** | Crosses only when the exact binary64 bit pattern is preserved bit-for-bit, including the sign of zero (`+0.0` distinct from `-0.0`) and, when present, NaN (as "the value is NaN" only -- R22 §4/R23 §10 approve no public NaN payload/sign construction, so no specific payload bit pattern is guaranteed) and signed infinities distinctly. This boundary does **not** inherit R23 §4.4's stricter JSON rule (finite-only; NaN/infinity rejected outright): that is JSON's own narrower interoperability policy, not this boundary's admissibility rule. A future codec contract may still choose to restrict a *specific* realization to finite values only (mirroring R23 §4.4) or to permit full bit-exact NaN/infinity crossing; this analysis fixes only the semantic floor (bit-exactness whenever permitted at all) and forbids silent coercion, payload fabrication, or loss. R23's shortest-roundtrip decimal spelling remains one proven lossless *finite*-value encoding a future codec may reuse, without this analysis selecting it as mandatory. | R18/R22 finite/zero/NaN/infinity equality and key rules remain authoritative after crossing: a boundary-crossed finite Float64 equals an exact value with the identical mathematical dyadic value (R22 §10.2 bridge) without rounding the exact operand to Float64 first; NaN remains non-reflexive and therefore illegal as a map key on both sides; `+0.0`/`-0.0` remain the same map key and compare equal to exact zero on both sides. | R22 §4, §9, §10.2; R18; R23 §2.4, §4.4 (contrasted, not adopted). | Whether/how a *specific future* realization permits NaN/infinity to cross at all, and the concrete finite-value wire encoding, are later codec decisions explicitly out of scope here. |
| Provider capabilities, configuration providers, model/retrieval providers | Identity-bearing runtime capabilities | **Local-only / non-transferable** | The capability object does not cross. A later explicit binding supplies a capability on the receiving side. | R18 identity; possession grants no authority; providers remain explicit and opaque. | R11/R12/R14; R18; PAI-1/6/7. | Remote reference/proxy semantics are not inferred. |
| Authorities | Opaque identity-bearing host capabilities | **Local-only / non-transferable** | Never ordinary boundary data; receiving realization must receive its own explicit authorized capability. | Identity-only; non-serializable; separate from provider identity. | R10 declassification; PAI-7. | Authority transfer and credential transport excluded. |
| Retrieval/index and other host handles | Identity-bearing live handles | **Local-only / non-transferable** | Reject the live handle. A separately contracted descriptor/token/reconstruction request would be a distinct value. | Runtime identity cannot be reconstructed structurally. | R12 index handle; R18 identity family. | Handle reconstruction/proxy/distributed identity excluded. |
| Owned live resource | R14/R18 identity-bearing resource | **Local-only as a live carrier** | Remains within its owning runtime/scope. P2 permits only its narrow same-runtime parent-to-child move. | Singular ownership and runtime identity; ownership grants no authority. | P2; R14 lifecycle; R18. | Cross-execution transfer, leases, proxies, and reconstruction deferred. |
| Borrowed resource/view | Bounded non-owning live value | **Never crosses** | May not escape its borrow window; may not be returned, retained in a result graph, emitted by Flow, serialized, or cross a provider/process boundary. | Crossing is pre-invocation misuse, not provider failure. | P2 scenario matrix; R14 lifetime rules. | No async/remote borrow model. |
| Flow / Seq / Promise | Lazy/delayed identity-bearing runtime values | **Local-only / non-transferable** | Do not consume, snapshot, or equate them with streams merely to cross. Materialization, if explicitly requested by another contract, yields a distinct ordinary value. | R18 identity; Flow remains lazy, pull-based, single-use. | `GENIA_STATE.md` Flow/Promise; R18; execution-realization. | Flow/remote-stream, backpressure, cancellation, and buffering deferred. |
| Ref / Cell / Process / Actor | Mutable/live identity-bearing runtime values | **Local-only / non-transferable** | Neither handle nor reachable live state crosses automatically. | R18 identity; equality never inspects state. | `GENIA_STATE.md` concurrency sections; R18. | Snapshot, remote reference, actor address, and distributed identity excluded. |
| Server, IO source/sink, file/socket/HTTP live resource | Host/live identity-bearing resource | **Local-only / non-transferable** | No open resource or listener crosses; only a separately approved inert descriptor may. | Runtime identity and R14 ownership stay local; authority remains explicit. | R14; R18 identity family; execution-realization. | Reconstruction, proxying, placement, and transport are separate contracts. |
| Function, closure, function group, Template/matcher, host/native callable | Executable identity-bearing value | **Local-only / non-transferable** | Code, captured environment, and callable identity do not cross. Interfaces exchange values, not executable closures. | R18 identity; no structural/function equality. | `GENIA_STATE.md` function/callable categories; R9 Templates; R18. | Closure serialization, bytecode transport, and code mobility excluded. |
| Module, environment, meta-environment, runtime namespace | Identity-bearing runtime namespace/state | **Local-only / non-transferable** | A module's separately exported portable values may cross; module/environment identity and bindings do not. | R18 identity; module is not a Map. | `GENIA_STATE.md` function/module values; R18. | No module snapshot/reflection protocol. |
| Raw provider/SDK/FFI/native object or raw exception | Host-private implementation value | **Never crosses** | Normalize to the interface-owned semantic value/Outcome or reject before observation. | No Genia equality/authority meaning is inferred. | R11/R12 private adaptation; PAI-3/8; R16 host discipline. | None; this is a fixed exclusion. |

Planned Store/Execution/job/subscription handles are examples of the R18
identity-bearing default only. They are not current values and this inventory
does not define them.

### Numeric admissibility summary (Integer/Decimal/Rational/Float64)

Now that R23 is complete, the four numeric rows above close the previously
blocked cells:

- **Outcome admissibility.** Each numeric kind is an ordinary structural leaf
  under the recursive admissibility rule; a numeric value inside `none(...)`,
  `some(...)`, or `err(...)` is admissible exactly when that numeric value is
  itself admissible under its row above, recursively.
- **List/Pair/Map/Sheet/represented-value admissibility.** Each numeric kind
  is an ordinary recursively portable leaf inside these families, subject to
  the same recursive admissibility rule as any other leaf: a List/Pair/Map/
  Sheet/represented value containing an inadmissible numeric leaf (for
  example a Float64 whose NaN/infinity a target realization has chosen not to
  admit, per that row's deferred note) makes the entire attempted crossing
  inadmissible, never silently dropped or coerced. A numeric Map key follows
  R18/R22 canonical key identity exactly as in a non-boundary Map (for
  example, Integer `1` and mathematically-equal Decimal `1.0` remain the same
  key; NaN remains illegal as a key on both sides of the boundary).
- **Recursive failure conditions.** Recursion into a numeric leaf can fail
  only for reasons already stated in its row: loss of exact
  coefficient/exponent or numerator/denominator identity, loss of bit-exact
  Float64 identity (including sign of zero), silent binary64 coercion of an
  exact value, silent JSON-style stability-gate rejection applied outside an
  actual JSON boundary, or a realization's declared resource limit (R22
  §11). No numeric leaf fails for a reason invented here beyond its row.
- **Protected-carrier interaction.** A numeric value may appear as the
  payload of an R10 protected carrier exactly as any other value family may:
  the protected-carrier row's fail-closed rule governs unchanged -- the
  carrier crosses only if its opaque identity and every R10 sink/
  declassification rule survive without exposing the numeric payload, and
  transport of a protected numeric value never becomes declassification. No
  numeric-specific protected-value rule is introduced; the existing R10/R18
  protected family rule already covers it.
- **Resource limits.** All four kinds reuse R22 §11's `numeric-resource-limit`
  normalization unchanged: a realization may impose implementation-specific
  coefficient/numerator/denominator/exponent magnitude ceilings, but must
  normalize the failure as `numeric-resource-limit` (never as a smaller
  language domain), never silently round/truncate, and never leak raw host/
  library exception text.
- **Distinct from Core IR and from display/debug rendering.** For all four
  numeric kinds, the provider-boundary role defined above (exact value,
  exact coefficient/exponent pair, exact numerator/denominator pair, exact
  bit pattern) is a distinct concept from both R21's tagged Core IR literal
  encoding (which governs how a numeric literal is classified and carried
  through parsing/compilation, per R21's own contract) and from R23's
  canonical display/debug rendering (fixed/scientific Decimal notation,
  `<numerator>/<denominator>`, `float64(...)`, which govern human-facing
  text). A future codec may choose to reuse R23's rendering text as one
  possible lossless encoding for a specific transport, but the boundary's
  admissibility rule above does not depend on, assume, or require any of the
  three.
- **What is explicitly NOT decided here.** No wire encoding, no mandatory
  codec, no textual spelling chosen as *the* boundary format, and no general
  NaN/infinity interchange policy for every future realization. Those remain
  later codec-contract decisions, per the "Explicit exclusions" list under
  P4 below.

## P4 — Canonical provider-boundary treatment

Status: **RESOLVED/FROZEN FOR ARCHITECTURE.** With R23 complete, the numeric
semantic shape below closes the previously blocked cells alongside the
already-resolved non-numeric canonical boundary shape.

`ProviderBoundaryValue` is a semantic admissibility model, not a runtime type,
class hierarchy, codec, schema, or new Genia value family. It contains only an
approved ordinary semantic scalar (including each of the four numeric kinds
below), tagged Outcome, ordered sequence/pair, ordered map entry sequence,
represented value with its ordered facet information, approved inert
structural value, or explicitly approved semantic token, recursively subject
to P3. This is a **semantic shape**, not a serialization format: it fixes
which exact fields must survive a crossing and does not choose byte layout,
text grammar, schema language, or transport protocol for any value family,
numeric or otherwise.

The crossing must preserve:

- exact Genia value family and variant (including Bool versus Symbol versus
  String, every Outcome variant, and Integer versus Decimal versus Rational
  versus Float64 -- these four numeric kinds never collapse into one another
  or into a host-native numeric type at the boundary);
- for **Integer**: the exact arbitrary-precision mathematical value;
- for **Decimal**: the exact canonical `(coefficient, exponent)` pair after
  R22 §2 canonicalization (sign carried by coefficient; trailing zeros
  stripped; Decimal kind retained even when the mathematical value is
  integral) -- never a host `decimal.Decimal`/`float` standing in for this
  pair, and never silently reduced through a JSON-style stability gate;
- for **Rational**: the exact canonical `(numerator, denominator)` pair after
  R22 §3 canonicalization (denominator positive and greater than `1` for a
  surviving Rational; sign carried by numerator; gcd-reduced) -- never a host
  `fractions.Fraction` standing in for this pair, and never silently rounded
  to a terminating Decimal or binary64 approximation;
- for **Float64**: the exact IEEE-754 binary64 bit pattern, including the
  sign of zero and, when an already-approved boundary produced one, NaN
  (presence only, no payload/sign guarantee) and signed infinities -- an
  exact semantic category distinct from the exact numeric family, never
  silently produced by rounding an Integer/Decimal/Rational, and never the
  implicit target of a cross-kind numeric coercion;
- exact order and multiplicity of sequences, map entries, representation
  facets, and other contract-defined ordered fields;
- R18 equality and canonical map-key identity, including for numeric keys
  (for example Integer `1` and mathematically equal Decimal `1.0` remain one
  canonical key on both sides of the boundary; NaN remains illegal as a key
  on both sides);
- for a successful Outcome: the exact `some(value[, context])` variant and
  its recursively admissible value/context;
- for a rejected/absent Outcome: the exact `none(reason, context?)` or
  `err(reason, context?)` variant with normalized, non-sensitive reason/
  context and no raw host/provider exception text;
- for an ordered map: entry order exactly as constructed, never reordered by
  a target's own native map/dictionary iteration order;
- R9 carried value, facet order, and portable representation metadata for a
  represented value (a represented numeric value, for example a numeric
  value wrapped by a representation carrier, is admissible exactly when both
  the facet stack/metadata and the carried numeric value are independently
  admissible under their own rules -- representation does not relax or
  substitute for the numeric preservation rules above);
- R10 protected-carrier constraints unchanged for a protected payload of any
  kind, numeric included: the carrier's opaque identity and every sink/
  declassification rule must survive without exposing the payload, or the
  crossing is rejected; and
- an approved token's contract-defined semantic identity without exposing its
  hidden representation, and the token-versus-live-handle distinction: an
  opaque immutable semantic token (R18) may cross when its owning contract
  approves it, while a live identity-bearing resource/handle never does --
  this distinction is orthogonal to numeric kind and applies unchanged
  whether or not the token happens to wrap numeric data.

This semantic shape is sufficient, without choosing a codec, for at least:
a Python realization (the current reference host, whose `GeniaDecimal`/
`GeniaRational`/explicit-Float64 runtime types already carry these exact
fields per R22, so a Python-side `ProviderBoundaryValue` mapping is a direct
field-for-field read, never a re-derivation through `decimal.Decimal` or
`fractions.Fraction`); a future C++ realization (which needs only an
arbitrary-precision integer pair for Decimal/Rational and a raw `uint64_t`/
`double` bit pattern for Float64 to represent the same exact fields, with no
Python-specific type required); and a future WIT mapping (WIT's own numeric
primitive types are fixed-width and would need an explicit, separately
contracted lowering for arbitrary-precision Integer/Decimal/Rational --
P4 fixes only the semantic fields such a lowering must preserve, and does not
itself attempt or approve that lowering).

The crossing must never carry provider-native/SDK/runtime objects, raw host
exceptions, executable code/closures/environments, live handles/resources,
borrowed values, providers, authorities, or exposed protected payloads. A
container does not launder an inadmissible leaf: the whole attempted crossing
is rejected. Input rejection happens during boundary validation/marshaling
before provider invocation; invalid provider output is normalized or rejected
at the return adapter before it becomes application-visible. This uses P6's
existing ownership of misuse and interface error normalization; it adds no new
failure envelope.

Represented values remain represented values. Maps remain deterministic ordered
entry collections with arbitrary currently legal Genia keys; they are not JSON
objects and must not inherit host dictionary behavior. Protected carriers may
be transported only under the P3 fail-closed condition: exact protection is
preserved and no payload is revealed. Cross-process protected-carrier
reconstruction remains deferred, so an implementation unable to preserve that
contract rejects the value.

This boundary is distinct from Core IR (program semantics), host-native Python
objects, JSON, display/debug rendering, R23 numeric interchange, WIT Canonical
ABI, and any eventual wire format. A later realization may choose a codec only
if it reproduces these semantic observations exactly.

### Explicit exclusions

P3/P4 do not define numeric interchange encoding; JSON encoding policy;
canonical number spelling; NaN/Infinity interchange policy; Decimal textual
encoding; Rational textual encoding; Float64 bit/text encoding; wire format;
binary ABI; schema language; reflection protocol; automatic serialization;
closure/code mobility; remote proxy semantics; handle reconstruction;
distributed identity; provider discovery; ambient registry; authority transfer;
credential transport; or WIT mapping. Each requires a separate future contract
unless already explicitly implemented for a different, narrower boundary.

## P3/P4 skeptical architecture freeze review (issue #941)

Before marking P3/P4 frozen, the numeric additions above were reviewed
adversarially against nine specific failure modes. Each is recorded with what
was checked and the outcome (clean, or found-and-fixed).

| Check | What was verified | Outcome |
| --- | --- | --- |
| JSON leakage | Whether the model implicitly assumes JSON is the provider boundary anywhere. Every numeric row explicitly names R23's JSON-specific rules (the safe-integer interval, `stable_json_decimal`, the Rational finite-equivalent gate, the Float64 finite-only rule) and explicitly states this boundary does not inherit them. The general P4 paragraph already states the boundary is "distinct from ... JSON." | **Clean.** No JSON assumption found; each JSON-specific rule is named only to be explicitly excluded. |
| Python `Decimal`/`Fraction` leakage | Whether any numeric field is described as if Python's own `decimal.Decimal`/`fractions.Fraction` were the semantic model, rather than R22's `GeniaDecimal`/`GeniaRational` semantics. Every Decimal/Rational bullet states "never a host `decimal.Decimal`/`float` standing in for this pair" and "never a host `fractions.Fraction` standing in for this pair," and ties the canonical fields directly to R22 §2/§3's own canonicalization rules, not to any Python stdlib type's canonicalization behavior (which differs -- for example Python's `Fraction` does not reduce a denominator of `1` to a plain `int`). | **Clean.** No Python-stdlib-as-semantics phrasing found. |
| Binary64 coercion | Whether Decimal/Rational are implied to be silently converted to Float64 anywhere in the boundary crossing. Every Decimal/Rational bullet states the pair is preserved "never through a host binary float" / "never silently rounded to a terminating Decimal or binary64 approximation," and the general "must preserve" list states Float64 is "never silently produced by rounding an Integer/Decimal/Rational" and "never the implicit target of a cross-kind numeric coercion." | **Clean.** No implicit coercion path found; explicit prohibitions were already present in the draft. |
| Lost map-key identity | Whether R18 key identity survives the boundary. The P4 preservation list has an explicit numeric-keys bullet (Integer `1`/Decimal `1.0` remain one key; NaN remains illegal as a key on both sides), and the Numeric admissibility summary repeats this for List/Pair/Map/Sheet admissibility. | **Clean.** R18 key identity is explicit, not assumed. |
| Lost representation metadata | Whether R9 represented-value facets survive when the carried value is numeric. The P4 list has an explicit represented-value bullet stating a represented numeric value is admissible only when both the facet stack/metadata and the carried numeric value are independently admissible, and that representation does not relax the numeric preservation rules. | **Clean.** No implicit facet-dropping found. |
| Protected payload exposure | Whether a numeric value inside a protected carrier is handled consistently with the already-resolved non-numeric protected-value rule (R10 fail-closed, P3's protected-carrier row). The P4 list has an explicit protected-carrier bullet stating the rule is "unchanged for a protected payload of any kind, numeric included," and the Numeric admissibility summary repeats this rather than inventing a numeric-specific protection rule. | **Clean.** No separate/weaker numeric protected-value rule was introduced; the existing R10/R18 rule is reused unchanged. |
| Accidental live-handle serialization | Whether adding numeric rows accidentally implies a live resource/handle could be serialized because it happens to wrap or reference a number (for example a numeric field inside an opaque handle). The token-versus-handle distinction in the P4 list is explicit and orthogonal to numeric kind; the existing non-numeric P3 rows already reject every live-handle family unconditionally, and nothing in the numeric additions creates an exception for a handle merely because its payload is numeric. | **Clean.** No new live-handle crossing path was introduced. |
| Confusion between Core IR and provider boundary | Whether it is clear R21's tagged Core IR and this provider boundary are different concepts. The initial draft stated this only at the general P4 level, not per numeric kind, which the requirement (issue #941: "distinguish from Core IR literal encoding and from display spelling") called for explicitly per family. | **Found and fixed.** Added an explicit "Distinct from Core IR and from display/debug rendering" bullet to the Numeric admissibility summary naming R21's tagged Core IR literal encoding and R23's canonical rendering as two separate, non-authoritative-for-this-boundary concepts for all four numeric kinds. |
| Ambiguity around Float64 NaN/zero | Whether the boundary treatment of NaN/`-0.0` is fully specified rather than left as "TBD." The Float64 row and the P4 list state precisely: `+0.0`/`-0.0` are always distinct and always preserved when a Float64 crosses at all; NaN is preserved as "the value is NaN" only (no payload/sign guarantee, matching R22 §4/R23 §10's own non-goal); and whether a *specific future realization* is permitted to admit NaN/infinity at all (versus rejecting them the way R23's own JSON boundary does) is the one deliberately open codec-level choice, consistent with the issue's own scope constraint that this work selects no mandatory wire codec. | **Clean, with one deliberately scoped-out codec choice.** The semantic floor (bit-exactness whenever a value is permitted to cross at all, exact zero-sign/NaN-presence handling) is fully specified; only the codec-level admit/reject policy for a specific transport is left to a later contract, which is in scope for exclusion under P4's own "Explicit exclusions" list, not an unresolved semantic hole. |

No check surfaced a genuine unresolved semantic hole that would block P8 or
P9. The one finding (Core IR/display-rendering distinctness) was a
documentation-completeness gap, not a semantic contradiction, and was fixed
in this same review before freezing.

## Relationship to WIT

WIT is useful as:

1. mature vocabulary for interfaces/worlds/resources;
2. an adversarial architecture comparison;
3. a possible external component ABI/ecosystem;
4. a later proof that Genia's model is genuinely language-neutral.

WIT is **not** Genia's semantic authority. Do not redefine Genia's Outcome, exact numerics, Flow, map/equality, representations, protected values, lifecycle, or diagnostics merely to mirror WIT.

The desired direction is:

```text
R11/R12/R14/R16/R18 evidence
        |
        v
extract common Genia provider model
        |
        v
solve missing whole-program/resource/boundary/failure semantics
        |
        v
Genia provider/component model
        |
        +--> R32 Database
        +--> R35 Store
        +--> R36 Execution
        +--> R37 Genia-native conformance tooling
        |
        v
attempt WIT interoperability mapping
```

not:

```text
WIT -> define Genia semantics
```

## R20 disambiguation

Do not use R20 open functions as provider selection.

R20 chooses a clause at call time based on arguments/patterns/guards from an already-linked immutable function view.

Provider binding chooses which realization satisfies a semantic capability for a computation/execution.

Those are different decisions. Mixing them would make deployment/realization choices part of semantic argument dispatch.

## Methodical work ledger

Use this table as the ordered preflight. Work one row at a time. Each completed row should update this file with evidence and a short decision, rather than starting implementation prematurely.

| ID | Question | Current state | Exit evidence |
| --- | --- | --- | --- |
| **P0** | What common provider invariants can be extracted from R11/R12/R14/R16/R18 without adding behavior? | **RESOLVED IN PREFLIGHT** | The preflight records the evidence matrix and PAI-1 through PAI-13; no new behavior is claimed. |
| **P1** | Do we need an application-facing whole-computation `requires`/`provides` concept? What does it add beyond explicit arguments/modules? | **RESOLVED: MINIMAL MANIFEST CONCEPT** | Inert whole-computation metadata enables transitive pre-execution inspection; ordinary arguments remain operational and R16 supplies only the enforcement shape. |
| **P2** | What is the smallest owned/borrowed/expired resource model built on R14 + R18? | **RESOLVED FOR ARCHITECTURE** | Dynamic R14-owned carrier, singular ownership, bounded non-escaping borrow, expiry misuse, and one parent-to-child move; APIs and advanced lifetimes deferred. |
| **P3** | Which Genia values may cross a component/provider boundary after R22/R23, and which remain host/process-local? | **RESOLVED/FROZEN FOR ARCHITECTURE** | Explicit value-family matrix, including all four numeric kinds, tied to existing contracts. |
| **P4** | What is the canonical provider-boundary representation, distinct from Core IR and host-native representation? | **RESOLVED/FROZEN FOR ARCHITECTURE** | Semantic boundary contract, including numeric exact-value preservation, sufficient for later Python/C++/WIT proofs without choosing a codec or leaking host defaults. |
| **P5** | How are interface identity, exact contract revision, and provider compatibility represented? | **RESOLVED FOR ARCHITECTURE** | Exact nominal identity plus exact opaque revision; no structural/SemVer inference, registry, or package system. |
| **P6** | Where is the line between operation Outcome, provider-realization failure, and R36 ExecutionResult/execution failure? | **RESOLVED FOR ARCHITECTURE** | Same-process calls keep interface Outcomes, composition/validity faults are misuse, and R36 remains the sole outer execution envelope. |
| **P7** | If a provider graph exists, how does it stay explicit, inert, inspectable, and non-DI? | **RESOLVED FOR ARCHITECTURE** | Explicit immutable validated binding plan over already-constructed capabilities; exact matching, closed transitive graph, fail-closed ambiguity/cycles, no R20 selection. |
| **P8** | What is the smallest proof of alternate provider realization with unchanged application logic? | **RESOLVED BY CONCRETE SUBSTITUTION PROOF** | `retrieve/4` proven with two realizations (existing fixed-order/fixed-score fixture vs. a new dict-backed real cosine-similarity fixture) behind the unchanged `GeniaRetrieveProvider`/`GeniaRetriever`/`create_fixture_retrieve_provider` shape; identical application-facing Genia source, identical portable Outcome shape, no provider-specific leakage, no R20/R14/R18/Outcome change — see `docs/design/p8-alternate-provider-substitution-proof-design.md` (design), `hosts/python/r12_retrieve_cosine_fixture.py` and `tests/unit/test_r12_retrieve_alternate_realization.py` (implementation, issue #945), and `GENIA_STATE.md` section 9.38. |
| **P9** | Can the resulting Genia model map to one actual WIT component without changing Genia semantics? | Deferred until P0-P8 are coherent | One bounded WIT interop proof; any mismatch documented rather than hidden. |

## Work order and gates

Recommended sequence:

1. **P0 is resolved.** PAI-1 through PAI-13 make the existing invariants explicit without adding behavior.
2. **P6 is resolved for architecture.** Same-process interface Outcomes remain ordinary; R36 alone owns the outer execution envelope.
3. **P1 and P2 are resolved for architecture.** The selected scope is a minimal inert manifest plus a narrow R14/R18 resource model, not a component subsystem.
4. **R22 and R23 are complete; P3/P4 numeric interchange is resolved/frozen for architecture (issue #941).** Do not define a component ABI that accidentally routes exact Genia numerics through host binary floats.
5. **P5/P7 only after the semantic need is clear.** Avoid building a registry/DI system in anticipation of requirements.
6. **P8 must reuse existing Genia provider semantics instead of inventing two toy providers from scratch.**
7. **P9 is last.** WIT is an interoperability test, not the starting model.

No step in this analysis bypasses the normal contract -> design -> failing test/spec -> implementation -> documentation -> audit workflow if behavior is eventually promoted.

## Recommended first proof

Do not start with two arbitrary toy providers. Reuse an existing R12-like semantic boundary because it already has portable values, opaque provider identity, compatibility checks, normalized Outcomes, and deterministic fixtures.

The proof should establish only:

- stable interface identity;
- explicit provider binding;
- unchanged application logic between two provider realizations;
- identical portable observations where the interface contract says they must match;
- no ambient provider discovery;
- no provider-native value leakage;
- no change to R20 dispatch, R14 lifecycle, R18 equality, or Outcome semantics.

Resource ownership should be a separate proof after that.

## Roadmap interaction

Do **not** renumber releases merely because this analysis exists.

The design should be resolved before future releases freeze independent provider/resource abstractions that would be expensive to reconcile later. The clearest consumers are:

- **R32 — Database Data Boundary**
- **R35 — Portable Storage and Resource Semantics**
- **R36 — Location-Independent Genia Execution**
- **R37 — Genia-Native Conformance Tooling**

R37 is especially useful as an integration proof because it is already planned to discover through R35 and invoke hosts through R36 in one Genia-native workflow.

Until promoted, this work remains architecture/preflight material rather than a numbered release.

## Promotion criteria

Do not create implementation tickets for a general provider/component model until the preflight can answer all of the following without hand-waving:

1. What new problem cannot be solved cleanly by existing explicit provider arguments/modules?
2. What exact whole-computation requirement/export semantics are needed?
3. What are the resource ownership/borrowing/expiry rules?
4. Which values/resources may cross the boundary?
5. What is the canonical boundary representation?
6. How are interface identity and compatibility established?
7. Which failure layer owns each failure kind?
8. How is binding/composition explicit and non-ambient?
9. How does the design preserve R10/R14/R18/R20 constraints?
10. What concrete killer-workflow or planned-roadmap consumer benefits from the abstraction?

Only after those are answered should the work be classified as a dedicated release, a prerequisite slice for an existing release, infrastructure, or continued parking-lot architecture.

## Decision log

Keep this short and append-only unless correcting a factual error.

- **2026-09-15 — Provider model reframed.** The initial WIT-first framing was rejected. R11/R12/R14/R18 already prove most provider semantics; WIT becomes comparison/interoperability precedent.
- **2026-09-15 — Provider failure correction.** R11/R12 normalize provider failures but encode them as ordinary `err(...)` Outcomes. A universal separate provider-result envelope is not implemented and remains unresolved against R36.
- **2026-09-15 — R16 enforcement precedent added.** Whole-application `requires`/`provides` is new in purpose, but R16 already proves the mechanical `requires` + advertised capability + deterministic fail-closed gating pattern.
- **2026-09-15 — R20 kept separate.** Open-function argument dispatch is not provider realization/binding.
- **2026-09-15 — R37 included as integration consumer.** R37's planned composition of R35 Store and R36 Execution makes it a future proving ground for the generalized model.
- **2026-09-17 — P0/P1/P2/P5/P6/P7 preflight resolved.** The focused preflight selects a minimal inert manifest, R14-owned dynamic resource lifetimes, exact nominal interface revisions, ordinary same-process Outcomes with an R36 outer envelope, and an explicit immutable binding plan. It authorizes no implementation or release change.
- **2026-09-18 — P3/P4 non-numeric boundary inventory resolved.** The recursive admissibility matrix and semantic `ProviderBoundaryValue` treatment preserve R9/R10/R14/R18 rules without defining a codec. Numeric provider-boundary encoding/interchange remains **BLOCKED ON R23**.
- **2026-09-19 — P3/P4 numeric hole closed; both RESOLVED/FROZEN FOR ARCHITECTURE (issue #941).** With R23 complete, the value-family matrix and `ProviderBoundaryValue` model were extended with Integer/Decimal/Rational/Float64 rows/fields preserving R22's exact coefficient/exponent, numerator/denominator, and bit-exact Float64 semantics without inheriting R23's JSON-specific stability gates or intervals, and without coercing to Python `decimal.Decimal`/`fractions.Fraction` or host binary64. A skeptical freeze review found and fixed one documentation-completeness gap (explicit per-kind Core IR/display-rendering distinctness) and found no genuine semantic hole. No wire codec is selected; `GENIA_STATE.md` is untouched.

- **2026-09-19 — P8 resolved by concrete substitution proof (issue #945).**
  `retrieve/4` (design `docs/design/p8-alternate-provider-substitution-proof-design.md`,
  issue #943) now has two realizations behind the unchanged
  `GeniaRetrieveProvider`/`GeniaRetriever`/`create_fixture_retrieve_provider`
  shape -- the existing fixed-order/fixed-score fixture and a new
  `hosts/python/r12_retrieve_cosine_fixture.py` dict-backed real
  cosine-similarity fixture -- proven identical in application-facing
  Genia source, portable Outcome shape, and non-leakage, with genuinely
  differing content (order/score), per
  `tests/unit/test_r12_retrieve_alternate_realization.py` and
  `GENIA_STATE.md` section 9.38. No `src/genia/retrieval.py` change was
  required or made.

## Current Stage 0 verdict

**P0/P1/P2/P3/P4/P5/P6/P7 ARCHITECTURE PREFLIGHT RESOLVED/FROZEN. P8 RESOLVED BY CONCRETE SUBSTITUTION PROOF. No implementation authorization beyond the resolved proofs.**

P3 and P4 are now fully resolved and frozen for architecture, including all
four numeric kinds, following R23's completion and issue #941's skeptical
freeze review. P8 is resolved by the concrete `retrieve/4` substitution
proof above (issue #945); P9 remains future proof work. The resolved
preflight does not promote a numbered release or change implemented
semantics beyond what section 9.38 documents; the doc's `PROPOSED /
EXPLORATORY` status and `GENIA_STATE.md`-is-final-authority disclaimer
above remain in force for this content, numeric included.
