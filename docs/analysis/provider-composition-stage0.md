# Genia Provider Composition — Stage 0 Retrospective and Work Ledger

Status: **Analysis / architecture preflight input — non-authoritative and not implemented.**

`GENIA_STATE.md` remains final authority for implemented Genia behavior. This file records evidence, settled conclusions, unresolved design questions, and an ordered work ledger so provider/component work can proceed methodically without reopening the same architectural ground.

## Why this file exists

A review of Genia's current FFI direction against WebAssembly Interface Types (WIT) initially suggested a new component/interface/provider architecture. Independent review of the repository showed that this framing was too external-first: Genia has already implemented and audited much of the provider pattern in R11, R12, R14, R16, and R18.

The working conclusion is therefore:

> Genia should first extract and generalize the provider architecture it already has, then design only the missing whole-program composition, resource-lifetime, cross-language-boundary, and failure-layer semantics. WIT is a comparison target and potential interoperability target, not the semantic authority for Genia.

This file is intentionally not a contract, syntax proposal, roadmap release, or authorization to implement new runtime behavior.

## Source-of-truth and evidence basis

Read these before changing the conclusions in this file:

- `AGENTS.md`
- `GENIA_STATE.md`
- `GENIA_RULES.md`
- `GENIA_REPL_README.md`
- `README.md`
- `docs/strategy/killer-workflow.md`
- `docs/strategy/release-roadmap.md`
- `docs/design/r11-ai-composition-contract.md`
- `docs/design/r12-retrieval-grounding-contract.md`
- `docs/design/r14-composable-lifecycle-contract.md`
- `docs/design/r16-multi-host-conformance-infrastructure-contract.md`
- `docs/design/r18-portable-value-equality-contract.md`
- `docs/design/r20-open-functions-contract.md`
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
| Canonical cross-language component value boundary | Core IR is a portability boundary for Genia semantics; R11/R12 have capability-specific conversions; R21-R23 settle numeric source/runtime/interchange. | **NEW** | Define only after R22/R23 settle exact numeric interchange. Do not make Python conversion rules the ABI. |
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

This must preserve Genia's own semantics for Outcome, maps/order/equality, representations, protected values, diagnostics, and—after R22/R23—Integer/Decimal/Rational/Float64 interchange.

### D. Failure layering

R11/R12 normalize provider failures into ordinary `err(...)` Outcomes. R36 plans a separate execution-level taxonomy. A general provider model must decide where these layers meet.

The design must distinguish at least conceptually:

```text
operation semantic result
same-process provider realization failure
R36 execution/placement failure
```

Do not create duplicate meanings for timeout, unauthorized, incompatible, provider failure, or cancellation across overlapping envelopes.

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
| **P0** | What common provider invariants can be extracted from R11/R12/R14/R16/R18 without adding behavior? | **READY** | Written invariant list reconciled against current authoritative docs; contradictions identified explicitly. |
| **P1** | Do we need an application-facing whole-computation `requires`/`provides` concept? What does it add beyond explicit arguments/modules? | Not started | Concrete use cases showing inspectability/composition/authority value; R16 fail-closed enforcement shape reused; no syntax required yet. |
| **P2** | What is the smallest owned/borrowed/expired resource model built on R14 + R18? | Not started | Lifetime/escape/transfer matrix and failure boundary, with no second lifecycle/equality system. |
| **P3** | Which Genia values may cross a component/provider boundary after R22/R23, and which remain host/process-local? | Blocked on R22/R23 for final numeric answer | Explicit value-family matrix tied to existing contracts. |
| **P4** | What is the canonical provider-boundary representation, distinct from Core IR and host-native representation? | Not started; numeric portion blocked on R22/R23 | Representation contract sufficient for at least Python/C++ proof without host-default numeric leakage. |
| **P5** | How are interface identity, exact contract revision, and provider compatibility represented? | Not started | Exact identity/revision rule, initially without automatic SemVer compatibility. |
| **P6** | Where is the line between operation Outcome, provider-realization failure, and R36 ExecutionResult/execution failure? | **Highest-risk open seam** | Failure matrix with one owner for each timeout/incompatible/unauthorized/provider/cancel/launch case. |
| **P7** | If a provider graph exists, how does it stay explicit, inert, inspectable, and non-DI? | Not started | Minimal graph/composition model or explicit decision that existing argument passing is sufficient. |
| **P8** | What is the smallest proof of alternate provider realization with unchanged application logic? | Not started | Reuse an existing R12-style semantic interface; demonstrate two realizations with identical portable observations and no provider-specific leakage. |
| **P9** | Can the resulting Genia model map to one actual WIT component without changing Genia semantics? | Deferred until P0-P8 are coherent | One bounded WIT interop proof; any mismatch documented rather than hidden. |

## Work order and gates

Recommended sequence:

1. **Complete P0 first.** Do not design new syntax or implementation while the existing provider invariants are still implicit.
2. **Attack P6 early.** The R11/R12 Outcome model versus R36 execution failure model is the most likely source of architectural duplication.
3. **Do P1 and P2 next.** These determine whether a true whole-program component/resource abstraction is needed.
4. **Let R22/R23 finish before freezing P3/P4 numerics.** Do not define a component ABI that accidentally routes exact Genia numerics through host binary floats.
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

## Current Stage 0 verdict

**GO for a narrow architecture preflight. No implementation authorization.**

The next work item is P0: extract the common provider invariants from the already implemented/audited R11/R12/R14/R16/R18 contracts and identify any contradictions or hidden assumptions before proposing new semantics.
