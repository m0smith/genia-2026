# Genia Provider Composition Architecture Preflight

Status: **Resolved architecture analysis — non-authoritative and not implemented.**

This document resolves Provider Composition ledger rows **P0, P1, P2, P5,
P6, and P7 only**. It authorizes no language/runtime behavior, syntax,
parser/AST/Core IR change, tests, providers, WIT integration, C++ work, or new
execution/storage behavior. `GENIA_STATE.md` remains final authority. The
central work ledger remains `docs/analysis/provider-composition-stage0.md`.

The reasoning order is deliberately Genia-first:

```text
implemented Genia semantics
  -> common architecture
  -> actual gaps
  -> smallest candidate abstractions
  -> later WIT comparison
```

These conclusions constrain later contracts; they do not block R24-R31.

## Terms

- A **semantic interface** names a concern-sized behavioral contract. It is not
  a class, module path, SDK object, or same-named function set.
- A **provider** is an explicit opaque capability realizing one or more
  semantic interfaces.
- A **requirement manifest** is inert metadata describing a closed
  computation's required/provided interfaces. It is not a lookup mechanism.
- A **binding plan** is an explicit immutable association from requirements to
  already-constructed provider capabilities, validated before execution.
- A **live resource** is an identity-bearing opaque handle whose valid use is
  bounded by ownership and lifecycle. An immutable opaque semantic token is
  not a live resource.
- **Authority** answers whether an effect may occur. Provider identity answers
  which realization is offered. They remain separate.

## P0 — Existing provider architecture

### Evidence matrix

| Invariant | Evidence and exact mechanism | Status | Safe reuse | Must not infer |
| --- | --- | --- | --- | --- |
| Explicit opaque providers | R11/R12 host/application injection supplies non-constructible model/embed/index/retrieve/rerank capabilities. | **Proven** | Opaque, concern-sized capability values. | Provider classes, a registry, or universal backend. |
| Explicit inert construction | R11/R12 constructors validate/capture provider, config, credential, and authority without IO, declassification, or attempt. | **Proven** | Capture now; attempt only on explicit call. | Discovery, fallback, eager initialization. |
| No ambient acquisition | R11/R12 reject registries; R14 `lifecycle_config` captures one already-built provider. | **Proven** | Explicit arguments/attachment. | Current-provider state, DI, service location, lifecycle acquisition. |
| Private host adaptation | R11/R12 cross the public boundary with ordinary closed values while SDK/wire objects remain private. | **Proven** | Ordinary values and Outcomes. | Arbitrary host objects are portable/component values. |
| Ordinary calls | R11/R12 return ordinary callables; pipelines and `scan` own composition. | **Proven** | Existing functions/callables/pipelines. | Provider call syntax or workflow orchestration. |
| Capability, credential, authority separation | R11/R12/R14 HTTP pass protected credential and purpose-scoped authority separately; declassification is just-in-time. | **Proven** | Separate explicit inputs. | Provider possession grants authority. |
| Normalized provider failures | R11/R12/R14 map failures to domain `err(...)` families and strip raw host/provider details. | **Proven** | Contract-owned non-sensitive Outcomes. | One universal provider envelope/taxonomy. |
| Concern-sized providers | R12 separates embed/index/retrieve/rerank. | **Domain precedent** | Small independently substitutable interfaces. | Every domain needs that exact split. |
| Semantic substitution checks | R12 checks hidden compatibility identity plus exact space/dimensions before attempt. | **Proven in one domain** | Pre-attempt exact compatibility validation. | Duck typing or name/signature/dimension-only matching. |
| Opaque live handles | R12 `index_handle` is opaque/non-serializable; R18 makes providers/live handles identity-bearing. | **Proven foundation** | R18 identity for live resources. | Structural equality, reconstruction, or cross-process identity. |
| Tokens differ from handles | R18 separates immutable opaque semantic tokens, with future `Revision` as precedent. | **Proven category** | Preserve token/resource distinction. | A revision or compatibility label is a live resource. |
| Attachment is not acquisition | R14 binds an existing config provider as a reserved peer without lookup/refresh. | **Proven** | Explicit scope attachment. | DI, automatic creation, rebinding. |
| Deterministic lifecycle | R14 defines parent/child scope ownership, ordered entry, reverse unwind, failure ordering, and expiry. | **Proven foundation** | Reuse R14 state/unwind. | General owned/borrowed/transfer already exists. |
| Loud expiry/no lazy leak | R14 rejects out-of-lifetime context access and finalizes bounded Flow element scopes. | **Proven precedent** | Dynamic validity and no stale access. | Every provider resource is already scope-bound. |
| Fail-closed capability gating | R16 cases declare `requires`; hosts advertise; unmet requirements are `UNSUPPORTED` before invocation. | **Proven enforcement shape** | Declare/check/do-not-invoke. | Application requirements are R16 host feature flags. |
| Exact revisions | R16 matches protocol versions exactly and pins conformance to exact contract revisions. | **Proven precedent** | Exact revision and separate evidence. | SemVer ranges or general provider identity. |
| Claims differ from evidence | R16 capability/revision claims are separately checked by deterministic conformance evidence. | **Domain precedent** | Identity/claim never self-certifies. | Claiming an interface proves conformance. |
| Pure identity equality | R18 identity comparison performs no calls, IO, or acquisition. | **Proven** | Same-runtime pure identity. | Remote/structural provider comparison. |
| R20 is not provider selection | R20 dispatches an already-linked immutable function by arguments/patterns/guards. | **Proven distinction** | Keep semantic dispatch separate. | Select realization by call shape or import/contribution order. |

The starting hypothesis is supported with qualifications. Genia has strong
precedents for explicit providers, ordinary values, authority, normalization,
compatibility guards, identity, and lifecycle. It does **not** yet have a
general computation manifest, resource ownership contract, interface identity/
revision model, failure-layer rule, or provider graph.

### Provider Architecture Invariants (PAI)

1. **PAI-1 — Explicit opaque capability.** Providers are explicitly supplied,
   opaque, and never obtained by ambient lookup.
2. **PAI-2 — Inert construction/binding.** Declaration, construction, and
   binding perform no provider acquisition or operation attempt.
3. **PAI-3 — Ordinary semantic boundary.** Ordinary values, callables, and
   existing Outcomes cross the boundary; SDK/wire/runtime objects stay private.
4. **PAI-4 — Concern-sized interfaces.** Prefer independently substitutable
   concerns; provider machinery is not workflow orchestration.
5. **PAI-5 — Exact semantic compatibility.** Check explicit semantic identity
   before attempt, never name-only duck typing.
6. **PAI-6 — Preserve identity categories.** Providers/live handles use R18
   identity; immutable semantic tokens do not become resources.
7. **PAI-7 — Separate authority.** Capability, credential, and authority are
   distinct. Binding grants no authority.
8. **PAI-8 — Normalize at the owner.** The contract owning a failure assigns
   its observable form; raw host/provider details never cross.
9. **PAI-9 — Reuse R14 lifecycle.** Resource ownership/expiry/unwind cannot
   introduce a second cleanup state machine.
10. **PAI-10 — Declare/check/fail closed.** Missing, ambiguous, or incompatible
    requirements prevent execution/attempt. R16 supplies the shape, not the
    application semantics.
11. **PAI-11 — Explicit deterministic composition.** No DI container, service
    locator, mutable registry, implicit fallback, or import-order choice.
12. **PAI-12 — Separate portability axes.** Host conformance, provider boundary,
    raw FFI, and execution placement are different claims.
13. **PAI-13 — R20 is not realization selection.** Open functions choose a
    semantic clause after binding, not a provider realization.

## P1 — Whole-computation `requires` / `provides`

Explicit function arguments remain the best local mechanism. Modules name
constructors/APIs, and R14 scopes attach already-built providers. None gives a
closed computation an inspectable transitive capability footprint *without
executing application code*. R16 solves a different question: whether a host
can run a conformance case, not whether an application has a Store or Model.

A whole-computation inventory enables pre-execution deployment validation,
authority review, exact interface checking, transitive inspection, R36
negotiation, and R37 orchestration. It does not replace explicit parameters.

### Model comparison

| Concern | A — explicit values only | B — declarative manifest | C — module/interface metadata only |
| --- | --- | --- | --- |
| Simplicity | Best; no new concept. | Small if inert/non-resolving. | Couples requirements to module structure. |
| Inspection/tooling | Requires convention or execution; incomplete transitively. | Closed deterministic inventory. | Works only when module/computation boundaries coincide. |
| Gating | Manual at entry points. | One R16-shaped fail-closed gate. | Risks gating during module load. |
| Authority | Strong locally; no whole-computation review. | Declares need but grants nothing. | Risks confusing import visibility with authority. |
| Transitive dependencies | Manual wiring, no closed graph. | Explicit union/closed graph. | Hidden or duplicated in imports. |
| Portability | Strong locally, weak for deployment tooling. | Host-neutral interface metadata. | Implementation module structure may leak. |
| Lifecycle | Caller-owned. | Manifest owns no lifecycle; R14 still does. | Risks module-lifetime coupling. |
| Runtime cost | None beyond calls. | One pre-execution validation. | Metadata loading/scanning. |
| DI drift | Low. | Moderate, bounded by PAI-1/2/7/11. | High if imports become lookup. |
| R36/R37 value | Each reinvents inspection. | Direct negotiation/orchestration input. | Useful only for module-shaped executions. |

### Decision: **MINIMAL MANIFEST CONCEPT**

A metadata-only **computation capability manifest** is justified. Its sole
responsibilities are to identify a closed computation; list exact required and
provided P5 interface identities/revisions; carry explicit transitive
requirements; permit deterministic inspection/fail-closed validation; and keep
authority/resource requirements separate.

It does not acquire, construct, select, call, refresh, or dispose providers;
inject lexical bindings; replace function arguments; treat imports as bindings;
grant authority; choose placement/transport/retry/lifecycle; imply syntax/Core
IR/reflection; expose implementation identity; or make every function a
component. R16's reusable shape is **declare -> advertise/bind -> exact check
-> fail closed before invocation**. Application identities are P5 identities,
not R16 capability-name strings.

## P2 — Resource ownership, borrowing, and expiry

### Decision: smallest viable model

The first model is **dynamic and scope-enforced**, built on R14 and R18:

- an **owned resource** has one identity-bearing carrier and exactly one owning
  R14 scope; aliases may exist but ownership is singular;
- a **borrowed view** is temporary and non-owning, valid only during one
  explicit provider call or child-scope callback;
- **expired/moved** is shared state observed by every alias after owner unwind
  or transfer.

Borrowing is needed to say “use, but do not close/retain” without transfer. It
is not a new type system. **Borrow escape is prohibited initially.** Escape
means reachability after the call/callback window: return; insertion into a
returned/retained List/Map/Outcome/represented value; closure/Promise/Flow/Seq/
cell/actor capture; Flow emission; longer-scope attachment; export; or process
crossing. Boundary checks may conservatively reject any result graph containing
a borrow.

Validity is shared between a generic carrier (identity, owning scope, state),
R14 (lifetime transitions/unwind), and the provider (domain operations). Use
after expiry/move, borrow escape, double close, or invalid transfer is **runtime
misuse before invocation**, not an operation `err(...)`. A valid operation may
still return its interface Outcome.

Ownership transfer is initially one explicit validated move from an active
parent to an active child before parent unwind. Old ownership aliases become
moved/invalid; borrowed views cannot transfer. General ownership return,
sibling/detached/cross-execution transfer is deferred.

### Scenario matrix

| # | Scenario | First-model decision |
| --- | --- | --- |
| 1 | Provider returns owned resource | Receiving active scope is sole owner; no owner scope means misuse, not implicit unbounded lifetime. |
| 2 | Provider accepts borrowed resource | Temporary synchronous view; provider cannot close, transfer, retain, or return it. |
| 3 | Borrow returned | Initial contracts prohibit it in callback results; crossing the borrow boundary is rejected. |
| 4 | Borrow in List | Only transiently inside the window; retained/returned container is recursively rejected. |
| 5 | Borrow in Map | Same; carriers are not approved structural map keys. |
| 6 | Closure captures borrow | Rejected if closure can survive the window; no closure-lifetime inference. |
| 7 | Flow captures borrow | Rejected because Flow is lazy. |
| 8 | Flow emits borrow | Rejected; emit an ordinary snapshot/descriptor instead. |
| 9 | Child receives resource | Borrow by default for child work; parent retains ownership. |
| 10 | Transfer to child | Only explicit move while both scopes are active; child becomes sole owner. |
| 11 | Parent exits with references | Structured child completes first; aliases then expire and do not extend lifetime. |
| 12 | Duplicate aliases | Same identity/state, not duplicate ownership; close/expiry/move reaches all aliases. |
| 13 | Use after expiry | Deterministic runtime misuse before provider invocation; no native details. |
| 14 | Cross R36 boundary | Live carrier never crosses. Send a portable descriptor/reconstruction token plus explicit binding/authority, or reject. |
| 15 | R18 comparison | Pure identity equality; no operation and no active-lifetime requirement. Equal expired aliases remain same identity. |
| 16 | Protected state behind resource | Rendering/serialization reveals none; use still needs explicit operation authority. Ownership grants none. |

Live resources are not serialized/persisted/rebuilt from display identity.
Portable descriptors or R18 semantic tokens are distinct values and do not
preserve live identity.

Deferred: static borrowing/affine types; detached/shared/finalizer-owned
resources; ownership return/sibling moves; remote identity/proxies/leases/GC;
async borrows and borrowed streams; public carrier/API/diagnostic spelling;
serialization; and P3/P4 representation.

## P5 — Interface identity and contract revision

| Model | Assessment | Decision |
| --- | --- | --- |
| Named identity | Readable but cannot distinguish incompatible revisions. | Insufficient alone. |
| Named + exact revision | Deterministic and inspectable; matches R16 exactness. | **Selected.** |
| Canonical module identity + export | Useful R20-like provenance but leaks module/implementation structure. | Provenance only. |
| Content/schema-derived | Brittle and falsely implies schema captures behavior/effects/failures. | Rejected as semantic identity. |

### Decision: exact nominal identity + exact opaque revision

The minimal interface key is `(canonical nominal interface name, exact opaque
contract revision)`. Example spellings are illustrative only; no grammar or
syntax is approved. Compatibility is nominal and exact, never inferred
structurally. A provider may explicitly claim multiple keys; each claim is
validated independently.

SemVer has no semantic authority and ranges are not inferred. Any future
compatibility relation must be explicit contract-owned evidence. Structural
schema/signature similarity may contribute to conformance evidence but does not
prove behavioral, authority, failure, or resource compatibility. Claims and
conformance evidence remain separate.

Transitive manifests carry exact keys. Diagnostics name expected/provided keys
and requirement paths, never provider implementation identity. Application code
gains no general provider reflection. Interface keys are inert metadata,
conceptually R18 opaque semantic tokens rather than forgeable strings. R20
module/interface identity may record declaration provenance, but is not this
compatibility namespace. No registry, package manager, discovery service, or
global catalog is introduced.

## P6 — Failure layering

### Decision

There are three owners, not three mandatory envelopes:

1. **Semantic operation result.** A valid same-process provider call remains an
   ordinary call returning the interface's Outcome/result. The interface owns
   semantic absence/rejection, its call timeout, normalized availability, and
   response validation.
2. **Composition/runtime misuse.** Missing/ambiguous/incompatible binding,
   invalid capability, resource expiry/escape, and pre-operation adapter
   violation fail closed. There is **no generic provider realization envelope**
   for same-process calls. Explicit initialization, if later approved, must
   receive an interface-specific ordinary Outcome; binding stays inert.
3. **R36 execution result.** R36 is the only outer envelope for whether a
   bounded computation launched/completed: launch, placement/protocol
   incompatibility, execution timeout/cancel, worker loss, and uncertain
   distributed completion.

An R36 execution may successfully return `err("model-timeout", ...)`: execution
completed and the inner operation failed. If R36 cannot complete, its outer
result reports that and no operation Outcome is invented. A call deadline is
Layer 1; a computation deadline is Layer 3. One observation has one owner even
when one physical outage could normalize differently at different boundaries.

### Failure matrix

| Example | Owner | Observation/classification |
| --- | --- | --- |
| Retrieval has no evidence | L1 retrieval | `none("retrieval-no-results")`; semantic absence. |
| Model rejects valid request | L1 model | `err("model-rejected", {kind})`. |
| Same-process call deadline | L1 interface | Domain timeout `err(...)`; no R36 layer. |
| Same-process provider unavailable/connect failure | L1 interface | Existing normalized transport/availability `err(...)`. |
| Malformed provider result | L1 interface | Domain response-invalid `err(...)`. |
| Host exception during valid provider call | L1 adapter/interface | Domain transport/other `err(...)`; strip type/message/stack/identity. |
| Missing required binding | L2 validation | Missing-interface diagnostic; computation does not start; not Outcome. |
| Wrong interface revision | L2 validation | Expected/provided key diagnostic; no attempt. |
| Two bindings for one slot | L2 validation | Ambiguous-binding diagnostic; no arbitrary choice. |
| Resource use after expiry | L2 validity | Runtime misuse; provider not called. |
| Explicit provider initialization rejects credentials | L1 initialization contract, if approved | Interface-specific unauthorized `err(...)`; binding itself remains inert. |
| R36 launch failure | L3 R36 | Outer launch failure; no inner Outcome. |
| Remote worker unavailable | L3 R36 | Outer execution/provider-unavailable failure. |
| Whole-execution deadline | L3 R36 | Outer execution timeout. |
| Execution cancellation | L3 R36 | Outer cancellation; inner cancellation only if explicitly observed. |
| R36 protocol/capability incompatibility | L3 negotiation | Outer unsupported/incompatible result before launch. |
| R36 succeeds; returned value is retrieval transport `err` | L3 success carrying L1 | Successful execution with exact ordinary `err(...)` value. |
| Authority absent during composition review | L2 validation | Missing-authority diagnostic; no execution/attempt. |
| Protected credential/authority mismatch at valid call boundary | Existing R10 misuse | Deterministic misuse before attempt, not provider rejection. |
| Provider authorization changes after valid attempt begins | L1 interface | Domain permission/rejection `err(...)`. |

The closest portable adapter owning a boundary strips raw exceptions. Private
host logs may follow host policy, but portable observations contain no stacks,
SDK bodies/types, endpoints, implementation identities, credentials, or
uncontrolled exception text.

## P7 — Explicit provider composition

P7 consumes P1's manifest, P2 resources, P5 keys, and P6 failure owners.

| Model | Assessment | Use |
| --- | --- | --- |
| Direct explicit values | Already proven and best inside programs, but lacks transitive inspection alone. | Remains invocation mechanism. |
| Explicit immutable binding map | Deterministic/inspectable and can validate manifests; risks container drift if lookup/injection is added. | **Selected with constraints.** |
| Closed component/world graph | Premature subsystem duplicating modules/lifecycle and requiring P3/P4. | Rejected now. |
| Provider factories/combinators | Ordinary explicit construction; may hide effects and cannot alone produce closed inspection. | Used before binding; bind resulting capabilities. |

### Decision: validated immutable binding plan

Use ordinary explicit provider values plus one inert immutable binding plan at
the computation boundary. The plan is not an application lookup API and does
not inject values. Bootstrap/realization code uses the validated association to
pass capabilities as ordinary arguments and attach resources through R14.

Inputs are: the P1 root manifest; explicit already-constructed capabilities;
each provider's claimed P5 keys and transitive manifest; separately supplied
authority assignments and lifecycle/resource plan; and optional conformance
evidence references (never substitutes for identity match).

Validation builds the finite transitive graph; matches exact keys; requires one
explicit binding per single requirement; rejects missing keys, revision
mismatch, ambiguity, undeclared fallback/claims, and unresolved authority or
resource requirements; rejects cycles initially; and yields an immutable plan
plus inspection report or one deterministic P6 Layer-2 diagnostic. No provider
attempt occurs. Multiple capable providers are not ambiguous until more than
one is explicitly bound to one slot; composition must explicitly choose, with
no priority/first/last/import-order/fallback rule.

### Required scenarios

| # | Scenario | Resolution |
| --- | --- | --- |
| 1 | One required provider | One exact key and explicit capability; pass as ordinary value. |
| 2 | Three independent providers | Three exact bindings validate independently; input order never selects. |
| 3 | One provider, two interfaces | Explicitly claim both exact keys; validate each independently; one capability may fill both. |
| 4 | Two providers can satisfy one interface | Plan explicitly chooses one; binding both is ambiguity. |
| 5 | Missing provider | Layer-2 diagnostic before execution. |
| 6 | Incompatible revision | Exact mismatch before execution; no coercion/range. |
| 7 | Duplicate binding | Reject; never first/last wins. |
| 8 | Provider A requires B | A's transitive manifest adds B; validate and pass B explicitly during construction/activation. |
| 9 | Provider graph cycle | Reject initially with deterministic requirement path; no lazy proxy cycle. |
| 10 | Provider authority unavailable | Separate authority validation fails; provider cannot mint authority. |
| 11 | Memory vs local Store | Select one explicit binding for the same exact Store interface; semantics govern substitution. |
| 12 | Genia/Python/C++/WIT implementation | Implementation language is absent from application semantics; each preserves the same interface/value/failure/authority/resource contract. |
| 13 | Local vs R36-hosted provider | Same semantic interface may be bound, but R36 remains explicit and adds its outer envelope; no transparent remoting. |

Binding is inert; activation may attach an existing provider/resource owner to
R14, whose unwind remains authoritative. Authority purposes/classes may be
inspected without secrets and are supplied separately. Same-process calls use
interface Outcomes; plan failures are Layer 2; R36 is the outer execution
layer. Inspection exposes root/transitive keys, chosen associations,
requirement paths, mismatches, authority/resource summaries, and evidence
references—never native object identity/address/SDK type/credential. A plan is
fixed for one execution; rebinding requires a new explicit plan.

### Why R20 does not select providers

```text
R20: arguments -> pattern/guard -> clause
P7:  semantic requirement -> explicit realization binding -> provider -> call
```

R20 operates after explicit lexical linking. Reusing it would make deployment
selection depend on argument shape or contribution visibility and defeat
whole-computation inspection. A provider may itself expose an open function if
its contract says so, but open dispatch cannot choose the provider (PAI-13).

## Synthesis

### 1. Is a new abstraction required?

**SMALL GENERALIZATION.** Ordinary values/callables/Outcomes and R14 remain the
operational foundation. A narrow reusable layer is justified for inert
manifests, exact interface/revision tokens, immutable binding validation, and a
generic R14-tied identity-bearing resource carrier with dynamic ownership/
expiry and bounded borrowing.

This is not a component subsystem. No syntax, invocation model, registry,
workflow engine, ABI, or universal provider result is justified. Any behavior
needs a later numbered-release contract and normal phase gates.

### 2. What remains for P3/P4?

Blocked on R22/R23 completion: exact Integer/Decimal/Rational/Float64 boundary
sets and representation; post-R22 numeric equality/keys; R23 textual/JSON
preservation; and binary/ABI mappings depending on those distinctions.

Investigable now, but not implemented here: non-numeric primitives; List/Pair/
Map ordering and keys; Outcomes; represented/protected values; Unicode; Bytes;
interface tokens; local-only closures/Flow/Seq/resources; closed-shape
validation; deterministic diagnostics; descriptor versus live carrier; and
semantic values versus host/WIT representation. P3/P4 must decide whether
protected values may cross and how authorized sinks work; serialization must
not recreate protection by default.

Core IR remains the program-semantics portability boundary. P4 is a distinct
provider value/resource boundary and must not copy Python conversions into an
ABI.

### 3. What remains for P8?

Reuse one R12 retrieval scenario: identify the exact retrieval revision; bind
the existing deterministic capability and a second realization preserving the
same space/dimension/compatibility semantics; run unchanged application logic;
prove the observations the interface requires (not necessarily identical
scores/results); prove incompatible space/revision fails before attempt; and
preserve authority, error, and provenance rules. Do not invent two toy
providers. This needs a later contract/tests.

### 4. What remains for P9?

A WIT proof must map one exact Genia interface/revision without making WIT
identity authoritative; preserve approved P3/P4 values and Outcomes; map owned
creation/borrow/expiry/cleanup without weakening R14; keep native/Wasm objects
private; preserve explicit authority/protection; distinguish operation,
component/transport, and R36 failures; reject incompatibility before call;
prove substitution against a non-WIT implementation; and document mismatches
rather than changing Genia. It need not initially prove Flow/stream equivalence,
transparent remoting, arbitrary module export, or a registry.

### 5. Roadmap recommendation

Continue architecture work during R22/R23; freeze numeric P3/P4 only after
R23. Do not block R24-R31 solely for provider composition. Settle/contract the
common model before R32 Database contract freeze. R35 Store and R36 Execution
must consume or explicitly reconcile it rather than create competing resource,
identity, and failure models. R37 should be the major composed integration
proof.

Do **not** assign or renumber a provider-composition release now. After R23, a
pre-R32 contract gate should decide whether the small generalization belongs in
R32 prerequisite work or warrants a numbered release. This document changes no
release.

## Resolution record

| Item | Resolution |
| --- | --- |
| P0 | Evidence extracted as PAI-1 through PAI-13. |
| P1 | **MINIMAL MANIFEST CONCEPT**; inert metadata, ordinary arguments operational. |
| P2 | Dynamic R14-owned carrier; singular owner, bounded borrow/no escape, child move only. |
| P5 | Exact nominal identity + exact opaque revision; no SemVer inference. |
| P6 | Interface Outcomes + composition/runtime misuse + R36-only outer envelope; no generic provider envelope. |
| P7 | Explicit immutable validated binding plan; no registry, DI, fallback, or R20 selection. |
