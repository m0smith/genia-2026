# Genia Provider Composition — Architecture Preflight (P0/P1/P2/P5/P6/P7)

Status: **Architecture/preflight decision record — non-authoritative, pre-contract, not implemented.**

`GENIA_STATE.md` remains final authority for implemented Genia behavior. This
document is subordinate to `docs/analysis/provider-composition-stage0.md`
(the evidence ledger and work order) and does not change it; it resolves the
six architecture questions Stage 0 marked `READY`/`Not started` for P0, P1,
P2, P5, P6, and P7. P3, P4, P8, and P9 remain open per Stage 0's ledger and
are summarized only in the synthesis below.

This document authorizes no implementation. It does not approve syntax. It
does not renumber, block, or accelerate any release. R24–R31 are not blocked
by this document's existence.

---

## P0 — Extract the existing provider architecture

### Question
What common provider invariants are already proven by R11, R12, R14, R16,
and R18 without adding any new behavior?

### Existing evidence
`docs/analysis/provider-composition-stage0.md`'s evidence matrix already
performs this extraction in detail and is treated as the evidence base here
rather than re-derived. Spot-verified against the source contracts:

- R11 (`docs/design/r11-ai-composition-contract.md`): "Provider capability:
  an opaque host-injected value... Source cannot construct, inspect,
  compare, render"; "There is no provider registry, name dispatch, general
  outbound HTTP function, ambient provider, or implicit configuration
  read"; authority is a distinct opaque R10 value matched against the
  credential's configuration-provider identity and a purpose token;
  declassification happens immediately before the one provider attempt;
  failures normalize to Outcomes without retaining raw provider/SDK detail.
- R12 (`docs/design/r12-retrieval-grounding-contract.md`): concern-sized
  providers (embed/index/retrieve/rerank, not one god-provider); `space`/
  compatibility identity checked before an attempt; opaque `index_handle`
  that is non-constructible/non-inspectable/non-keyable/non-serializable.
- R14 (`docs/design/r14-composable-lifecycle-contract.md`): explicit
  rejection of "lexical injection, no dependency injection" (line 26) and
  "not dependency injection, not a service container" (line 411) for
  `lifecycle_config(provider)`; binding captures an already-constructed
  provider and performs no acquisition/refresh/ambient lookup; deterministic
  parent/child scope entry and reverse-unwind ownership.
- R16 (`docs/design/r16-multi-host-conformance-infrastructure-contract.md`):
  declared `requires:` per case, advertised `capabilities`, deterministic
  fail-closed `UNSUPPORTED` (never scored as pass); explicit distinction
  between pinned-conformance and current-main-compatibility, itself a
  precedent for "claims about support are evaluated, not assumed."
- R18 (`docs/design/r18-portable-value-equality-contract.md`): "Future live
  Store/execution/actor/job/subscription handles default to this family"
  (identity-bearing) "unless a later approved contract deliberately
  classifies a new value as an opaque semantic token"; a future storage
  `Revision` is the motivating opaque-semantic-token example, explicitly
  distinct from a live identity-bearing handle; providers, authorities, and
  handles are listed as not map-keyable.

### Alternatives considered
1. Re-derive the invariant list from scratch by re-reading all five
   contracts independently of Stage 0.
2. Treat Stage 0's evidence matrix as authoritative evidence and confirm it
   against primary sources rather than duplicating the extraction.
3. Skip verification and simply cite Stage 0.

### Decision
Alternative 2. Stage 0's extraction is confirmed accurate against the
primary contracts (spot-checked above); no contradiction was found. The
Provider Architecture Invariants below are the P0 exit artifact, restating
Stage 0's "Settled house rules to preserve" with contract citations added
and with each invariant tagged for reuse scope.

**Provider Architecture Invariants (P0 exit list):**

| # | Invariant | Source | Reuse scope |
| - | --- | --- | --- |
| 1 | Providers are opaque capabilities, not source-visible class hierarchies | R11, R12 | General |
| 2 | Providers are explicit, never ambient/registry/name-dispatch | R11, R12 | General |
| 3 | Provider construction/binding is inert (no IO at construction/attachment time) | R11, R12, R14 | General |
| 4 | Binding/attachment captures; it never acquires or discovers | R14 | General |
| 5 | Ordinary Genia values are the semantic boundary; provider-native SDK/wire objects stay private below it | R11, R12 | General |
| 6 | Provider-backed behavior composes through ordinary callables, Outcomes, and existing pipelines — no second invocation language | R11, R12 | General |
| 7 | Provider substitution requires declared semantic compatibility (e.g. `space`), not matching function names | R12 | Domain-scoped precedent; generalization needed (see P5) |
| 8 | Providers/live handles use R18 identity-bearing equality by default | R18 | General |
| 9 | Opaque immutable semantic tokens (e.g. future `Revision`) are distinct from live identity-bearing resources | R18 | General |
| 10 | Authority is explicit and separate from provider capability/identity | R10, R11, R12 | General |
| 11 | Raw host exceptions/SDK detail never cross the portable boundary unnormalized | R11, R12 | General |
| 12 | Provider machinery must not become a service locator, DI container, ambient registry, or workflow engine | R14 (explicit rejection) | General |
| 13 | A declared-but-unsupported capability fails closed; it is never silently skipped or scored as pass | R16 | General (mechanism); application-level meaning is new (P1) |
| 14 | Host portability, provider/component portability, raw FFI, and execution placement are separate axes | `execution-realization.md`, R16 | General |
| 15 | R20 open-function argument dispatch is not provider selection | R20 | General (see P7 disambiguation) |

### Rejected alternatives
Re-deriving from scratch (Alternative 1) was rejected as duplicate work with
no evidentiary benefit — Stage 0's matrix already cites exact mechanisms per
contract, and spot verification found no drift from the current contracts.

### Preserved invariants
All 15 above. None are new behavior; all restate already-approved contract
language.

### New semantic obligations
None. P0 defines no new semantics.

### Explicit non-goals
- No new provider object model, registry, or class hierarchy.
- No claim that these invariants are implemented as a unified cross-release
  API — each is proven only within its own release's domain (AI/retrieval/
  lifecycle/conformance/equality) until a later release generalizes it.

### Dependencies / blocked work
None. This is the foundation P1/P2/P5/P6/P7 cite below.

### Consequences for later releases
- R32: must reuse invariants 1–14, not invent a database-specific provider model.
- R35: Store/Location/Revision must reuse invariant 9 (opaque token vs. live handle) as R18 already anticipates.
- R36: Execution/ExecutionHandle must reuse invariants 1–4, 8, 10–14.
- R37: composes R35+R36 realizations of these same invariants; no new invariant expected.

### Status
**RESOLVED**

---

## P1 — Whole-computation `requires`/`provides`

### Question
Does Genia need an application-facing whole-computation declaration of
required/provided semantic capabilities, beyond what explicit function
arguments, modules, and R16-style capability gating already provide?

### Existing evidence
- No implemented application-facing capability-footprint construct exists.
- R16 already proves the *mechanical* shape: declared `requires:` per case,
  advertised `capabilities`, deterministic fail-closed `UNSUPPORTED`. That
  shape answers "does a host support conformance capability X," which is a
  **different question** from "does this application need semantic provider
  X to run," even though both use a declare/advertise/fail-closed pattern.
- R20 module/interface identity (`docs/design/r20-open-functions-contract.md`
  §2.1) shows Genia already has an inert, explicit, portable-key identity
  model for cross-module contribution — evidence that "declare an identity,
  link explicitly, fail closed" is a workable Genia idiom, but R20 itself is
  about clause dispatch, not capability requirements.
- The killer workflow (`docs/strategy/killer-workflow.md`) is
  Outcome-aware validated data pipelines with explicit sources/sinks; it
  does not currently need whole-program capability inspection to succeed.
- R36 (planned) will need compatibility negotiation using "semantic contract
  revision/protocol/capability identity" — a real future consumer of
  whole-computation capability inspection, but not yet a proof that the
  concept must exist as a *language* construct rather than tooling-side
  bookkeeping.

### Alternatives considered
1. **Model A — no new concept.** Dependencies stay ordinary explicit
   arguments (`main(store, model, clock, ...)`). Composition/inspection is
   whatever the caller assembles.
2. **Model B — declarative requirement manifest.** A new
   requires/provides construct as a runtime or declaration-time value
   (conceptual only; no syntax approved).
3. **Model C — module/interface metadata only.** Requirements/provides
   attached as inert metadata on a module/component, not a new runtime
   value, inspectable by tooling but not executed against at call sites.

Evaluated against: whole-program inspection, deployment/realization
validation, authority review, provider compatibility checking, tooling,
static pre-execution failure, transitive composition, R36 negotiation, R37
orchestration.

- Model A gives none of whole-program inspectability, but has zero new
  mechanism, zero portability cost, and is exactly what R11/R12/R13/R14
  already do today (explicit provider/config arguments). It does not
  preclude later tooling from statically walking a call graph if ever
  needed — that is a tooling problem, not a language-semantics gap.
- Model B (a manifest as a first-class runtime concept) risks becoming a
  second module system layered over ordinary arguments/imports, and risks
  drifting toward a DI container if a "requires" declaration is ever used to
  auto-supply providers rather than merely describe them. It is the
  heaviest-weight option and the current evidence does not show a
  killer-workflow or R32/R35/R36/R37 need that explicit arguments/modules
  cannot already satisfy.
- Model C (inert metadata for tooling/inspection only, never consulted by
  the runtime to select or supply a provider) is the only model that adds
  inspectability without adding a second binding mechanism. But no current
  concrete consumer (R32/R35/R36/R37 as currently planned) requires it yet;
  R36's own planned compatibility negotiation is described in terms of
  `Execution`/`ExecutionHandle` capability/contract identity, not a
  whole-*program* manifest.

### Decision
**NO NEW REQUIRES/PROVIDES CONCEPT at this time.** Explicit function
arguments plus R16-style declare/advertise/fail-closed capability checking
(reused per-provider, not as a new whole-program construct) are sufficient
for every concrete need identified so far. Model C (inert module/component
metadata) is named as the *only* fallback worth reconsidering, and only if
a concrete R36 or R37 slice later demonstrates that tooling genuinely cannot
walk an explicit-argument call graph to answer a capability-footprint
question it actually needs answered.

### Why
The burden of proof set by the task ("a new concept is justified only if it
provides concrete value ordinary arguments/modules cannot provide cleanly")
is not met. Every candidate benefit (inspection, authority review,
compatibility checking, fail-closed gating) is already achievable today:
inspection/tooling can statically read explicit argument lists and R16-style
per-provider capability declarations; authority review already happens at
the R10/R11/R12 authority-argument boundary; fail-closed gating is already
R16's proven mechanism, reusable per-provider without a new whole-program
wrapper. Introducing a manifest concept now, ahead of a concrete R32/R35/R36
consumer that needs it, would risk exactly the "service container" drift
P0's invariant 12 forbids: a requires/provides declaration is one edit away
from also supplying/resolving providers, at which point it stops being
inspectable metadata and becomes ambient binding.

### Rejected alternatives
- Model B is rejected now as unjustified new mechanism; it may be
  reconsidered only if a future release shows a concrete case explicit
  arguments cannot express.
- Model C is not rejected outright but deferred: it is the fallback if
  R36/R37 tooling needs, not application semantics, later prove
  insufficient with explicit arguments alone.

### Preserved invariants
1, 2, 3, 4, 6, 12, 13 (fail-closed reused per-provider, not invented as a
new whole-program wrapper), 14.

### New semantic obligations
None.

### Explicit non-goals
- No manifest syntax.
- No claim that R16's `requires:`/`capabilities` mechanism is reused
  verbatim at the application level — it is cited only as proof that the
  declare/advertise/fail-closed *shape* is a workable Genia idiom, should a
  concrete future need justify Model C.

### Dependencies / blocked work
Revisit only if a concrete R36 negotiation slice or R37 orchestration slice
demonstrates that explicit-argument call-graph inspection is insufficient.

### Consequences for later releases
- R32: database credentials/connections stay ordinary explicit R10/R13
  arguments; no database-specific manifest.
- R35: Store/Location arguments stay explicit; no whole-program storage
  manifest.
- R36: `Execution` capability/authority requirements are described per
  `Execution` value (already planned), not via a whole-program manifest;
  if R36 design work later finds it needs whole-program capability
  inspection beyond what an `Execution` value's own requirements express,
  that is new evidence this decision must be revisited against, not grounds
  to silently build Model B inside R36.
- R37: discovery/orchestration reads explicit R35/R36 values; no manifest
  required for the planned integration proof.

### Status
**RESOLVED** (Model A now; Model C explicitly named as the only
reconsideration path, gated on concrete future evidence).

---

## P2 — Resource ownership, borrowing, and expiry

### Question
Do provider/component resources need a small ownership contract
(owned/borrowed/expired) beyond what R14 lifecycle scopes and R18 identity
already provide?

### Existing evidence
- R14 provides deterministic parent/child scope entry, peer isolation, and
  reverse-unwind cleanup, but only at the *scope* level — there is no
  existing concept of a resource being "borrowed" for a narrower window than
  its owning scope, and no existing escape-detection rule.
- R18 provides identity-bearing equality/keying for resources but no
  lifetime/validity state machine.
- R12's `index_handle` is the closest existing precedent: opaque,
  non-constructible, non-inspectable, non-keyable, non-serializable — i.e.
  today Genia's answer to "can a handle escape its safe context" is
  effectively "the handle carries no usable structure to escape with," not
  an enforced ownership discipline.
- No implemented Genia value currently has a "used after expiry" failure
  mode to generalize from; this is genuinely new ground, as Stage 0 already
  classifies it (`NEW`).

### Alternatives considered
Required scenarios (16 listed in the task) were used as the test matrix
rather than enumerated individually here; the two alternatives are:

1. **Full owned/borrowed/expired lifetime model now**, with escape rules for
   closures, Lists, Maps, Flow, and child scopes, enforced dynamically at
   runtime — i.e. begin generalizing Rust/WIT-shaped ownership immediately.
2. **Smallest viable model: scope-owned only, no borrowing primitive yet.**
   A resource's validity is tied to exactly one R14 scope (its creating
   scope or a scope it is explicitly transferred to). There is no
   "borrowed" state distinct from "owned by the current scope." Escape is
   defined structurally, the same way R12 already achieves it: a resource
   handle is opaque and carries no way to be reconstructed or persisted
   outside its owning scope's lifetime, so "escape" reduces to "the handle
   is used after its owning scope has unwound," which R14 can already
   detect via existing scope-lifetime state.

### Decision
**Alternative 2 — smallest viable model, scope-owned only; no distinct
"borrowed" state in the first generalization.**

- Ownership is dynamic/runtime-enforced, tied 1:1 to an R14 scope: a
  resource is valid exactly while its owning scope (or a scope it was
  explicitly transferred to) is entered.
- "Borrowed" is **not** introduced as a first-class state. A function that
  receives a resource as an ordinary argument does not need a borrow
  marker: it simply must not retain the resource past the call unless the
  resource crosses into a scope that itself outlives the call (e.g. stored
  by the *caller's* scope, not a callee-local one) — this is exactly what
  R14 already prevents by construction, since nothing hands a callee a way
  to outlive the caller's scope without an explicit R14 attachment.
- Genia can prohibit borrowed escape structurally rather than statically:
  a resource handle remains opaque and non-serializable (per the R12
  `index_handle` precedent), so placing it in a List/Map, capturing it in a
  closure, or emitting it from a Flow does not change its validity — using
  it after its owning scope unwinds is a deterministic runtime failure
  (an `err(...)` Outcome analogous to R14's existing failure-matrix rows),
  not a silent success or a language-level detection of "escape" as a
  distinct static category.
- Resource validity belongs to **a combination** of the provider (which
  decides what "valid" means operationally) and R14 scope state (which
  decides *when* validity ends structurally) — not a new generic "resource
  carrier" type. This avoids inventing a second lifecycle mechanism.
- Ownership transfer to a child scope is explicit and reuses R14's existing
  attachment discipline (the same discipline `lifecycle_config` already
  uses) — never implicit reparenting.
- Use-after-expiry is a normalized `err(...)` Outcome (reusing R11/R12's
  proven normalization pattern), not a raw runtime crash and not silent
  misuse-as-success. This keeps P2 consistent with P6's failure layering
  below rather than inventing a parallel failure channel.
- Serialization/cross-process identity: a live resource does **not**
  serialize as itself. Only an explicit, provider-defined, opaque semantic
  token (R18's `Revision`-shaped precedent, invariant 9) may cross a
  process/execution boundary; the live resource itself does not.
- Duplicate aliases of the same resource share identity under R18 equality;
  aliasing does not create separate ownership — there remains exactly one
  owning scope per resource.

### Why
The evidence base (R14 scopes + R18 identity + R12 opaque-handle precedent)
already answers most of the required scenarios without inventing borrowing
as a distinct mechanism: opacity plus scope-tied validity make "does this
escape" reduce to an ordinary R14 lifetime question the runtime can already
answer, rather than requiring new static analysis or a second type-system
concept. Importing Rust/WIT's exact owned/borrowed distinction now would add
mechanism (a compile-time-checkable borrow discipline) Genia has no
compile-time enforcement point for, and no concrete scenario in the killer
workflow or R32/R35/R36 currently requires borrow-checking granularity
narrower than "this scope is still entered."

### Rejected alternatives
Alternative 1 (full borrow-checked model) is rejected now as premature
mechanism; R35 (Store/Resource) and R36 (Execution) are the first concrete
consumers and can motivate a distinct "borrowed" state later if their own
design work finds scope-tied ownership insufficient — that is new evidence,
not something to pre-build speculatively.

### Preserved invariants
3, 4, 6, 8, 9, 11, 12.

### New semantic obligations (deferred, not authorized)
If later promoted: a resource-validity check at use time; a normalized
expiry Outcome; explicit-only ownership transfer to a child scope. None of
this is authorized by this document — it is the shape a later R35/R36
resource contract should reuse rather than reinvent.

### Explicit non-goals
- No "borrowed" first-class state in the first generalization.
- No static/compile-time borrow checking.
- No generic serialization of live resources.
- No new resource-carrier value family distinct from existing R14 scopes
  plus R18 identity.

### Dependencies / blocked work
R35 (Store/Location/Revision) and R36 (Execution/ExecutionHandle) are the
concrete consumers that should validate or falsify this model with real
resource shapes before any borrowing primitive is considered.

### Consequences for later releases
- R32: database connections/cursors, if resource-shaped, should be
  scope-owned per this model, not a bespoke ownership scheme.
- R35: `Store`/live resource handles should be scope-owned; `Revision`
  stays the separate opaque-token precedent already anticipated by R18.
- R36: `ExecutionHandle` should be scope-owned; crossing an execution
  boundary should use an opaque token/descriptor, never the live handle
  itself, consistent with "resource identity may not cross a process
  boundary" above.
- R37: composes R35 Store resources and R36 Execution resources under one
  scope-owned model — first integration proof of whether scope-only
  ownership is actually sufficient.

### Status
**PARTIAL.** The smallest model is defined and preserves R14/R18 without a
second lifecycle mechanism, but it is explicitly unvalidated against a real
resource shape (R35/R36 do not exist yet). Treat this as the working
hypothesis for R35/R36 to confirm or falsify, not a closed design.

---

## P5 — Interface identity and contract revision

### Question
How does Genia identify a semantic provider interface and determine whether
a provider satisfies the exact contract an application expects?

### Existing evidence
- R12 compatibility identity: hidden identity plus exact `space`/`dims`
  checks *before* an attempt — nominal-plus-structural-field exactness, not
  duck typing.
- R16 `contract_revision`: an exact identifier (commit SHA or tag), checked
  for exact match vs. resolvable-ancestor vs. unresolvable — three
  outcomes, never a fuzzy "close enough."
- R20 canonical module/interface identity (`docs/design/r20-open-functions-contract.md`
  §2.1): identity is `(declaring module's canonical module identity,
  exported binding name)` — never a filesystem path, object address, or
  hash-of-convenience.
- R18: identity-bearing equality for providers/handles (invariant 8).
- R36 (planned): "compatibility negotiation using semantic contract
  revision/protocol/capability identity" — a named future consumer, not yet
  a concrete mechanism to generalize from.

### Alternatives considered
1. **Named identity only** (e.g. `genia:storage/store`) — no revision
   component; compatibility is "same name."
2. **Named identity + exact revision** (e.g. `genia:storage/store@1`) —
   nominal identity plus an exact, non-inferred revision match, directly
   generalizing R16's `contract_revision` exact/ancestor/unresolvable model
   and R20's `(module identity, name)` pair.
3. **Canonical module identity + exported interface name only** (pure R20
   reuse, no separate revision axis) — treats interface identity exactly
   like R20 interface identity, with revision folded into the module
   identity itself (a new module version is a new module identity).
4. **Content/schema-derived identity** (structural hashing of the
   interface's shape) — analyzed per the task's instruction, not assumed
   desirable.

### Decision
**Alternative 2 — named identity + exact revision, nominal (not
structural) compatibility, no automatic inference between revisions.**

- Interface identity is nominal: an exact declared name/key plus an exact
  declared revision. Two interfaces with structurally identical shapes but
  different declared identities are **not** interchangeable — this
  generalizes R12's rule that compatibility is explicit and declared
  (`space` match), never inferred from matching field/function shape alone.
- Compatibility checking is exact-revision matching by default, directly
  reusing R16's already-proven three-way exact/ancestor/unresolvable
  discipline rather than inventing a fourth outcome or a compatibility
  range.
- A provider may claim multiple interfaces (concern-sized providers,
  invariant from P0/R12) — claiming interface X does not imply claiming any
  related interface Y, even a same-named earlier or later revision.
- SemVer numbers carry **no semantic/compatibility authority** in this
  model per explicit user direction during this preflight: if a revision
  identifier happens to look like a SemVer string, Genia's compatibility
  check still requires an exact match (or an explicitly declared-compatible
  set, if a later contract adds one) — SemVer, where used at all, is at
  most a human-readable convention/suggestion for provider authors and
  tooling, never a rule the runtime uses to infer that `1.3.0` may satisfy
  a `1.2.0` requirement. This is stricter than typical SemVer compatibility
  inference by design, matching the task's conservative default and R16's
  existing exact-match precedent.
- Diagnostics refer to interfaces by their declared nominal identity
  (module/name/revision), never by provider implementation identity — this
  mirrors R20 §7 provenance rules and R11/R12's "raw host detail never
  leaks" invariant (11).
- Application code inspecting interface identity: identity is ordinary,
  inspectable data (a name/revision pair), not an opaque token — this
  differs from a live *handle*, which stays opaque per P0 invariant 9.
  Identity describes a *contract*; a handle is a *live resource*. Conflating
  the two would make every compatibility check require holding a live
  resource just to ask "what does this claim to implement."
- Transitive requirements (provider A requiring provider B) identify B the
  same way: nominal name + exact revision, checked before A is considered
  usable — no separate transitive-identity mechanism.

### Why
Alternative 1 (name-only) fails the R16/R12 precedent that exactness
matters — a name alone cannot express "this provider was built against an
older/incompatible version of interface X," and R12 already proves that
silent name-based matching is exactly the failure mode Genia rejects.
Alternative 3 (fold revision into module identity) is close to what R20
already does, but conflating "different revision" with "different module"
would make routine revision bumps look like unrelated interfaces to
tooling/diagnostics, losing the "same interface, different revision"
relationship P6/P7 need to report a useful "incompatible revision" error
(vs. "unknown interface entirely"). Alternative 4 (content/schema hashing)
is rejected: it would let two independently authored interfaces that
happen to share a structural shape silently satisfy each other, exactly
the "duck typing at scale" P0 invariant 7 already forbids, and it produces
diagnostics tied to a hash rather than a human-legible declared name.

### Rejected alternatives
1 (name-only) and 4 (structural/content-derived) are rejected as violating
the existing R12 "explicit compatibility, not signature matching" rule. 3
is rejected as collapsing two distinguishable questions (interface identity
vs. revision) into one axis, which would weaken diagnostics.

### Preserved invariants
7, 8, 9, 11 (as clarified above: identity is ordinary data; handles stay
opaque), 13, 15.

### New semantic obligations (deferred, not authorized)
An interface declares a nominal name and an exact revision; a provider
claims a set of (name, revision) pairs; compatibility checking is exact
match unless a later contract explicitly authorizes a compatible-set
declaration. Not implemented by this document.

### Explicit non-goals
- No package manager, registry, or global discovery system.
- No automatic SemVer range inference — SemVer, if present in a revision
  string at all, is informational only, never load-bearing.
- No structural/content-derived identity.

### Dependencies / blocked work
Feeds directly into P7 (composition needs exact identity to bind against).

### Consequences for later releases
- R32: database driver "interfaces" (if this shape is reused) use exact
  nominal name + revision, not driver-name-only matching.
- R35: Store provider interface identity reuses this model rather than
  inventing a storage-specific compatibility scheme.
- R36: Execution's planned "semantic contract revision/protocol/capability
  identity" negotiation should consume this exact model rather than a
  parallel one.
- R37: orchestration diagnostics report interface identity using this
  nominal name/revision shape, never provider implementation detail.

### Status
**RESOLVED** (as the conservative default the task specified; open only to
the extent a future contract explicitly adds a compatible-set mechanism).

---

## P6 — Failure layering

### Question
Where does the line fall between (1) an operation's ordinary semantic
result, (2) a same-process provider-realization failure, and (3) R36's
planned execution/placement failure — without creating overlapping or
duplicate-meaning taxonomies?

### Existing evidence
- R11/R12 normalize provider failures (timeout, rate-limit, transport,
  malformed response, rejection) into ordinary `err(...)` Outcomes. No
  second provider-result envelope exists today; Stage 0 explicitly flags a
  universal two-envelope model as **unresolved/not implemented** if ever
  claimed.
- R36 (planned, not implemented) separately plans a distinct
  `ExecutionResult` with "normalized unsupported/incompatible/unauthorized/
  launch/timeout/cancel/execution/provider failures" and "no implicit
  retries."
- R14 provides the deterministic partial-entry/failure matrix for lifecycle
  scopes — an existing precedent for *structured* failure handling that is
  not itself an Outcome, because it governs scope entry/unwind, not a
  return value.
- `execution-realization.md`: distributed execution can introduce retries,
  duplicate work, partial failure, unavailable workers — conditions "must
  remain observable where they affect program correctness," and Genia
  "must not adopt the fiction that a remote operation is merely a local
  call executing somewhere else."

### Alternatives considered
1. **Two envelopes always**: every provider call, even same-process,
   returns both an Outcome and a separate provider-realization-failure
   envelope, unified with R36's `ExecutionResult` shape.
2. **Three-layer model, same-process calls stay ordinary Outcomes**:
   (a) operation semantic result remains an ordinary Outcome
   (`some`/`none`/`err(...)`), exactly as R11/R12 already do; (b) a
   same-process provider realization failure (crash, unavailable, protocol
   violation, contract mismatch, init failure, timeout, cancellation,
   authority rejection) is *also* normalized directly into that same
   `err(...)` Outcome — it does **not** get a second envelope, because
   R11/R12 already prove this normalization works without one; (c) R36
   `ExecutionResult` remains the **only** outer envelope, and it exists
   specifically because execution crosses a boundary an ordinary call does
   not — uncertain completion, retries-not-implicit, placement failure —
   which a same-process call structurally cannot produce.
3. **Merge layers 2 and 3**: always route same-process provider calls
   through the R36 `ExecutionResult` shape too, on the theory that "a
   provider call is a kind of execution."

### Decision
**Alternative 2 — three conceptual layers, but only two runtime envelopes.**
Same-process provider calls remain ordinary Outcome-returning calls,
exactly as R11/R12 already implement; a generic provider-realization
envelope distinct from Outcome is **not** created; R36 `ExecutionResult`
remains the only outer execution envelope, used only when a call actually
crosses R36's execution/placement boundary.

Representative failure-owner matrix (10 examples per the task's minimum):

| # | Failure | Owning layer | App observes | Outcome? | Notes |
| - | --- | --- | --- | --- | --- |
| 1 | `retrieve(...)` finds nothing | (a) operation result | `none(...)` | Yes | Ordinary absence, not a failure at all |
| 2 | Model call times out | (b) provider realization, same process | `err("model-timeout", ...)` | Yes | R11-proven pattern; no second envelope |
| 3 | Provider adapter crashes internally | (b) provider realization | `err("provider-unavailable", ...)` or equivalent normalized kind | Yes | Raw exception stripped per invariant 11 |
| 4 | Provider returns malformed/protocol-violating response | (b) provider realization | `err("provider-protocol-violation", ...)` | Yes | Still same-process; still an Outcome |
| 5 | Declared interface revision mismatch (P5) | (b) provider realization, checked before attempt | `err("interface-incompatible", ...)` | Yes | Checked before the call per R12/R16 precedent — fails closed, never attempted |
| 6 | Authority rejected at declassification | (b) provider realization | `err("unauthorized", ...)` | Yes | Reuses R10/R11 declassification-failure pattern |
| 7 | R36 execution succeeds; the *provider operation inside it* returns `err(...)` | (a) operation result, carried inside (c) | App reads `ExecutionResult`'s returned value, which is the ordinary `err(...)` Outcome | Yes, nested | Distinguishable: execution completed; the *computation's own result* happened to be an error value |
| 8 | R36 execution cannot complete the provider operation at all (worker crash mid-call, launch failure) | (c) R36 execution/placement | App reads `ExecutionResult`'s own failure classification (e.g. `launch`, `execution`) | No — this is execution metadata, not the computation's Outcome | Structurally distinct from #7: no computation result exists to report |
| 9 | R36-executed call times out at the placement layer (worker unreachable) vs. a same-process provider timing out (row 2) | (c) vs. (b) | `ExecutionResult` `timeout` classification vs. `err("...-timeout", ...)` Outcome | Row-dependent | Same word "timeout" means different things at different layers — never merged into one taxonomy entry |
| 10 | R36 execution is cancelled mid-flight | (c) R36 execution/placement | `ExecutionResult` `cancel` classification | No | Cancellation ownership belongs to R36, not to the provider-realization layer, because only the execution layer knows whether the work was placed remotely and may be duplicated/retried |

Ownership summary:
- **Layer (a) operation semantic result** is always an ordinary Outcome.
  This is unconditionally true whether or not a call happens to be executed
  through R36.
- **Layer (b) same-process provider realization failure** does not get its
  own envelope. It is normalized directly into the same Outcome channel as
  layer (a), reusing R11/R12's proven normalization exactly. This directly
  answers the task's skepticism question: same-process providers are
  **not** burdened with distributed-execution machinery.
- **Layer (c) R36 execution/placement failure** is the only outer envelope,
  and it exists only because crossing an execution boundary can fail in
  ways a same-process call structurally cannot (launch failure, worker
  unavailability, uncertain completion, cancellation, duplicate delivery).
  It wraps, but does not replace, layer (a)'s Outcome — row 7 vs. row 8
  above is the load-bearing distinction: "execution succeeded but the
  computation's own answer was an error" (still just an Outcome, nested
  inside a successful `ExecutionResult`) is different in kind from
  "execution itself could not produce a computation result" (an
  `ExecutionResult`-level failure with no Outcome to unwrap).
- Timeout and cancellation ownership: **layer (b)** owns a same-process
  provider's own operation timeout (row 2); **layer (c)** owns
  execution/placement-level timeout and all cancellation (rows 9–10),
  because only the execution layer knows about worker placement, retries,
  and duplicate-delivery risk per `execution-realization.md`.
- Raw host exceptions are stripped at whichever layer first touches host
  detail — R11/R12 already do this at layer (b); R36 must do the same at
  layer (c) for its own provider-specific process mechanics.

### Why
This avoids the two failure modes the task explicitly warns against: (1) a
second universal provider envelope duplicating Outcome (rejected — R11/R12
already prove Outcome-only normalization works for every same-process
provider failure kind observed so far), and (2) burdening same-process
providers with R36's distributed-execution machinery merely because a
future execution layer will exist. Keeping `ExecutionResult` as the *only*
outer envelope, and only invoked when a boundary is actually crossed, keeps
the "same physical failure can mean different things depending on which
layer it occurred in" property intact (row 9) without inventing overlapping
taxonomy entries for the same word.

### Rejected alternatives
Alternative 1 (always two envelopes) is rejected as inventing mechanism
same-process calls do not need and as directly contradicting Stage 0's
existing finding that no such envelope is implemented today. Alternative 3
(merge layers 2/3) is rejected because it would make every provider call
pay the "uncertain completion / retries / placement" conceptual cost that
`execution-realization.md` explicitly reserves for calls that actually
cross a process/placement boundary — same-process calls have none of those
properties and must not pretend otherwise.

### Preserved invariants
6, 11, 12, 14.

### New semantic obligations (deferred, not authorized)
None beyond what R11/R12 already implement for layer (a)/(b). Layer (c)'s
exact `ExecutionResult` shape remains R36's own contract to write; this
document only fixes that it is the sole outer envelope and how it relates
to (a)/(b).

### Explicit non-goals
- No new Outcome variant or a second Outcome-like type.
- No claim that R36's `ExecutionResult` exists yet — it is referenced only
  as planned precedent per Stage 0's `PLANNED PRECEDENT` classification.
- No retrofitting of R11/R12's existing normalized-failure kind names.

### Dependencies / blocked work
R36's own contract must still define `ExecutionResult`'s exact shape; this
document only fixes the layering rule it must satisfy.

### Consequences for later releases
- R32: database query/transaction failures are layer (a)/(b) — ordinary
  Outcomes — unless a query is itself dispatched through R36, in which case
  row 7/8's distinction applies.
- R35: Store operation failures (not-found vs. operational failure, per
  R35's own planned Outcome-absence distinction) are layer (a)/(b).
- R36: must write `ExecutionResult` to satisfy exactly the layer-(c) role
  fixed here — it must not also try to re-normalize layer (a)/(b) results
  into its own taxonomy.
- R37: orchestration must read layer (a) Outcomes and layer (c)
  `ExecutionResult`s as distinct, per row 7 vs. row 8, when reporting
  conformance evidence.

### Status
**RESOLVED**, with the explicit caveat that R36's own `ExecutionResult`
contract is not yet written — this document fixes the *seam*, not R36's
exact taxonomy.

---

## P7 — Explicit provider composition

### Question
How are application requirements connected to provider implementations
without ambient discovery, a mutable global registry, dependency injection,
a service container, implicit fallback, import-order behavior, or R20
dispatch-as-deployment-selection?

### Existing evidence
This decision consumes P0 (invariants), P1 (no manifest concept — Model A),
P2 (scope-owned resources), P5 (nominal name + exact revision identity),
and P6 (failure layering) directly, per the task's own instruction not to
design P7 independently.

- R11/R12 already demonstrate the working pattern at single-provider scale:
  a provider capability is constructed explicitly (host-side factory or
  explicit application code) and passed as an ordinary argument into
  `model(...)`/`index(...)`/etc.
- R14 `lifecycle_config(provider)` demonstrates the pattern at the
  lifecycle-attachment scale: an already-constructed provider is captured,
  never acquired.
- R20's `(module identity, exported name)` linking is explicit,
  import-order-independent, and immutable once linked — a strong structural
  precedent for "explicit selection, no ambient discovery," even though R20
  itself is clause dispatch, not provider realization (see disambiguation
  below).

### Alternatives considered
1. **Direct explicit values**: `main(store_provider, model_provider)` —
   ordinary function arguments, no composition mechanism beyond what
   function calls already provide.
2. **Explicit immutable binding map**: a conceptual `bind { Store ->
   local_store, Model -> gemini }` construct resolved once, before
   execution, into an immutable set of realizations (no syntax approved).
3. **Explicit component/world composition**: requirements/provides form a
   closed graph validated before execution (heavier machinery, closer to a
   WIT world).
4. **Provider factories/combinators**: ordinary Genia functions construct
   providers and pass them onward — composition is just function
   composition, with no new binding construct at all.

### Decision
**Alternative 1 (direct explicit values / ordinary function composition),
with Alternative 4 (factories/combinators) as its natural extension for
multi-provider and transitive cases — no new binding construct.**

Walking the required scenarios under this model:

1. **One provider**: `main(store)` — ordinary argument.
2. **Three independent providers**: `main(store, model, clock)` — ordinary
   arguments; no manifest needed (consistent with P1's Model A decision).
3. **One provider satisfying two interfaces**: the provider value is passed
   to both call sites that need it; P5 identity lets each call site verify
   the specific (name, revision) it needs independently. No special
   multi-interface binding mechanism — this is just "pass the same value
   twice."
4. **Two providers capable of satisfying the same interface**: the
   *application* (caller), not the language, picks which value to
   construct and pass — e.g. `main(local_store())` vs. `main(gemini_model())`.
   There is no ambiguity at the language level because there is no
   selection step to be ambiguous about; ambiguity, if any, is an ordinary
   application-code decision (an `if`/config read the application already
   controls).
5. **Missing provider**: an ordinary missing-argument/misuse failure, or if
   the provider is itself optional and constructed lazily, an ordinary
   `err(...)` from whatever explicit construction step failed — fails
   closed by construction, never silently substitutes a default.
6. **Incompatible revision**: a P5 identity check fails at first use
   (mirroring R12's "check before attempt"), producing the layer-(b)
   `err("interface-incompatible", ...)` Outcome from P6's row 5.
7. **Duplicate ambiguous binding**: cannot occur structurally under this
   model — there is no binding table to have duplicate entries in. If two
   *values* are constructed and only one function parameter exists, the
   application's own code, not language machinery, decides which one is
   passed. This is a deliberate simplification relative to Models 2/3: it
   trades away a build-time "detect duplicate bindings" check for
   eliminating an entire class of binding-table machinery the evidence does
   not yet justify.
8. **Provider A requiring provider B**: B is constructed first and passed
   explicitly into A's own construction call — an ordinary factory/
   combinator (Alternative 4), e.g. `gemini_model(retry_policy(http_client))`.
   This is transitive composition via ordinary nested calls, not a graph
   resolver.
9. **Provider graph cycle**: cannot occur, because construction is ordinary
   value construction in dependency order — Genia already has no mechanism
   for a value to depend on its own not-yet-constructed self outside of
   explicit recursive functions, and provider construction is not
   privileged over that existing rule.
10. **Provider requiring authority not supplied**: an ordinary
    construction-time or declassification-time misuse/`err(...)` failure,
    exactly as R10/R11 already implement — no new authority-composition
    mechanism.
11. **Same application, memory Store vs. local Store**: the application
    constructs and passes whichever value it wants — `main(memory_store())`
    vs. `main(local_store(path))` — no language-level switch needed.
12. **Same interface implemented in Genia, Python FFI, C++, later WIT/Wasm**:
    irrelevant to the composition model — P5 identity and P0 invariant 5
    (ordinary values above, provider-native objects below) already ensure
    the *caller* only ever sees an ordinary ordinary ordinary Genia-level
    provider value regardless of implementation language; composition does
    not need to know or care which host language backs a given provider.
13. **Provider hosted locally vs. reached through R36 later**: the
    provider value itself does not change shape; only whether calling
    through it also crosses R36's `ExecutionResult` layer (P6, layer c)
    changes. Composition (which value gets passed where) is orthogonal to
    placement.

### Why
Every required scenario is already expressible through ordinary explicit
values and ordinary function composition, consistent with P1's finding
that no whole-program manifest is justified. Introducing a binding-map or
world/graph construct (Alternatives 2/3) would add exactly the "service
locator by another name" risk the task explicitly warns about: a binding
table that resolves `Store -> local_store` by name is one small step from
becoming a name-keyed ambient lookup the moment any code path consults it
implicitly rather than the caller passing it explicitly. Ordinary argument
passing has no such step to take — there is no table to consult implicitly.
This also keeps composition deterministic, inspectable (the call graph *is*
the composition graph — read the source), immutable per-execution by
construction (nothing rebinds an already-passed value), and free of
import-order effects, since Genia's existing evaluation order already
governs when each construction call runs.

### Rejected alternatives
Alternatives 2 and 3 are rejected now as unjustified mechanism, matching
P1's Model A/Model C reasoning. They remain reconsiderable only if a
concrete R32/R35/R36/R37 slice demonstrates a composition shape ordinary
nested function calls genuinely cannot express (for example, if R37's
integration proof needs to describe a provider graph *before* any
provider is constructed, for tooling/validation purposes separate from
execution — that would be new evidence, not something to pre-build here).

### R20 disambiguation (required by the task)
Provider composition is **not** R20 open-function dispatch:

```text
R20:                          arguments -> pattern/guard selection -> clause
Provider composition:  semantic requirement -> explicit realization binding -> provider -> ordinary calls
```

R20 selects among already-linked clauses *at call time* based on argument
shape, after linking has already fixed the participating unit set. Provider
composition selects *which value to construct and pass* before any call
happens — the "selection," such as it is, is application code choosing what
to construct, not a runtime pattern match over argument shapes. A provider's
own semantic contract may of course use ordinary pattern matching/guards on
its own arguments after binding (that is just ordinary Genia code), but
*which provider realization is bound in the first place* must never depend
on R20-style argument-shape dispatch — doing so would make deployment
choice a hidden side effect of what values happen to be passed to an
unrelated call, exactly the coupling this document forbids.

### Preserved invariants
1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 13, 14, 15.

### New semantic obligations
None. This is a reuse-composition decision, not a new mechanism.

### Explicit non-goals
- No binding-map/world/graph syntax or runtime value.
- No compile-time or load-time "resolve the whole provider graph" pass.
- No claim that duplicate-binding ambiguity (scenario 7) is detected by
  language machinery — it is prevented structurally by there being no
  binding table, and is otherwise an ordinary application-code decision.

### Dependencies / blocked work
None beyond what P1/P2/P5/P6 already establish. This is the P7 exit
artifact the task requires.

### Consequences for later releases
- R32: database connection/driver values are ordinary explicit arguments,
  constructed and passed exactly like R11/R12 providers today.
- R35: `Store` values are ordinary explicit arguments/factories; no Store
  registry.
- R36: `Execution` provider selection (local vs. remote) is an ordinary
  explicit value the caller constructs and passes — R36's own contract
  should not reinvent binding.
- R37: composes R35 Store values and R36 Execution values as ordinary
  arguments into its orchestration functions — first real multi-provider
  composition proof of this model at meaningful scale.

### Status
**RESOLVED** for the composition *shape*. Explicitly **PARTIAL** for
scenario 7 (duplicate/ambiguous binding) in the sense that the task asked
for "ambiguity behavior" as a defined property of the model: this document
answers it by removing the ambiguity surface entirely (no binding table),
which is a valid but load-bearing design choice that R32/R35/R36/R37 should
confirm remains adequate as real multi-provider applications are built.

---

## Synthesis

### 1. Is a new language/runtime abstraction actually required?

**SMALL GENERALIZATION.** Not "no" — P2 and P5 do identify genuinely new
semantic surface (a scope-owned resource validity rule; a nominal
name+revision interface identity model) that no existing release currently
implements as a reusable, cross-release contract. But it is not "NEW
COMPONENT SUBSYSTEM" — P1 and P7 both conclude that no new binding/
manifest/graph mechanism is justified by current evidence, and P0/P6
conclude that the bulk of "provider architecture" is already implemented
and merely needs to be recognized as a reusable pattern rather than
reinvented per release. The burden of proof for a new component subsystem
(highest per the task) is not met by any of the six questions.

### 2. What remains for P3/P4?

Per Stage 0, P3 (which values may cross a component/provider boundary) and
P4 (canonical provider-boundary representation) remain explicitly blocked
on R22/R23 for their numeric portion — routing exact Decimal/Rational
values through a boundary representation cannot be settled before R22/R23
freeze exact numeric runtime/interchange semantics. Non-numeric boundary
questions that **can** already be investigated without waiting: which
non-numeric value families (Outcome, maps, protected values, opaque
tokens vs. live handles per P2/P0 invariant 9, representations) are
boundary-eligible in principle, reusing this document's P2 resource model
and P5 identity model as the framework those investigations should sit
inside. This document does not perform that investigation; it only notes
that P3/P4's non-numeric half is unblocked and P2/P5 are ready inputs to it.

### 3. What remains for P8?

Per Stage 0's own recommendation (already correct and unchanged by this
document): reuse an existing R12-shaped semantic boundary rather than
inventing two toy providers. Concretely, P8 should construct two
realizations of one existing R12-style interface (for example, two
`embed`/`index` provider realizations already compatible under R12's
`space` rule) and demonstrate, under this document's P5 identity model and
P7 composition model, that swapping which realization is constructed and
passed produces identical portable observations with zero provider-specific
leakage and zero change to R14/R18/R20/Outcome behavior. This document
authorizes no such implementation; it only sharpens what P8 should prove
now that P5/P7 have concrete shapes to test against.

### 4. What remains for P9?

An eventual WIT interoperability proof would need to demonstrate that one
concrete Genia interface — identified under this document's P5 nominal
name+revision model, with a provider realized either as raw FFI or (later)
as an actual WIT component — can be bound under this document's P7
composition model without changing Genia's own Outcome, equality, Flow, or
lifecycle semantics to resemble WIT's. Per the task, this is not to be
implemented; it remains deferred until P0–P8 are coherent, per Stage 0's
existing ordering.

### 5. Roadmap recommendation

**No release renumbering is warranted.** This document's findings support
the existing planning rule exactly as stated in the task:
- Architecture work is appropriately happening now, during the R21–R24
  numeric/C++-host arc, as preflight rather than a numbered release.
- P3/P4's numeric boundary portion stays frozen until after R23, as Stage 0
  already states.
- R24–R31 are not blocked by this document's existence — none of P0/P1/P2/
  P5/P6/P7's conclusions require any change to R24–R31's planned scope.
- The architecture (specifically P2's resource model, P5's identity model,
  P6's failure-layering seam, and P7's composition shape) should be settled
  — which this document does, as a preflight hypothesis — before R32's
  Database contract freeze, so R32 does not invent an independent provider/
  resource model.
- R35 and R36 should consume this document's P2/P5/P6/P7 models rather
  than inventing independent ones; both are named as the concrete
  consumers that will confirm or falsify P2's "scope-owned, no borrowing"
  hypothesis and P7's "no binding table" hypothesis.
- R37 remains the appropriate major integration proof, composing R35 and
  R36's realizations of this shared model.

No new numbered provider-composition release is recommended: P1 and P7
both found that no new runtime/language machinery is currently justified,
which is the condition under which the task said a numbered release should
*not* be recommended.

---

## Skeptical self-check (per task quality bar)

1. **Does requires/provides add anything beyond ordinary arguments?** No —
   P1 explicitly found no concrete case it solves that explicit arguments
   don't already solve; Model A adopted.
2. **Can resource ownership stay simple?** Yes, by declining to add
   "borrowed" as a first-class state and reusing R14 scope lifetime
   structurally (P2) — but this is flagged PARTIAL pending R35/R36
   validation, not asserted as proven.
3. **Is provider composition DI under a nicer name?** No — P7's decision
   specifically has no binding table, registry, or implicit resolution
   step; every realization choice is an ordinary explicit value the caller
   constructs, which is the structural property that distinguishes it from
   DI (DI's defining feature is that *something other than the caller*
   decides what gets supplied).
4. **Does interface identity create an accidental package/type system?**
   No — P5 deliberately excludes a registry/package manager and keeps
   identity to a nominal name+revision pair with no discovery mechanism.
5. **Does failure layering create a second Outcome system?** No — P6
   explicitly keeps same-process provider failures inside the existing
   Outcome channel; only R36's *own*, separately-contracted
   `ExecutionResult` is a second envelope, and only for calls that actually
   cross an execution boundary.
6. **Are same-process providers burdened with distributed-execution
   machinery?** No — P6's row-by-row matrix is built specifically to keep
   layers (a)/(b) free of layer (c)'s concerns.
7. **Is planned R35/R36 semantics being used as implemented authority?**
   No — every R35/R36 reference above is explicitly labeled planned/not
   implemented, consistent with Stage 0's `PLANNED PRECEDENT`
   classification; this document adds no implemented-truth claim.
8. **Are WIT assumptions leaking into Genia semantics?** No — P2
   deliberately declines to import Rust/WIT's borrow-checked ownership
   model; P5's identity model is compared against WIT only as external
   precedent, never as the starting semantics.
9. **Is a proposed abstraction actually needed by the killer workflow?**
   None of P0/P1/P2/P5/P6/P7 add a new abstraction the killer workflow
   must adopt; all are reuse/generalization decisions or deferred.
10. **Could ordinary values/functions/lifecycle solve the need instead?**
    Yes for P1 and P7 (explicitly chosen); largely yes for P2 (scope reuse);
    P5/P6 add identity/layering vocabulary because R16/R11/R12 already
    proved those specific mechanisms are needed, not because this document
    invented a new requirement for them.

## Open issues that should stop later R32/R35/R36 contract work if unresolved

1. **P2's "no borrowing" hypothesis is unvalidated** against a real
   resource shape. If R35 or R36 design work finds a genuine need for a
   narrower-than-scope validity window (a resource usable only for one call
   but not stored anywhere), that is new evidence this document does not
   yet have, and R35/R36 contract authors must not silently invent a
   borrowing mechanism without updating this document first.
2. **P7 scenario 7 (duplicate/ambiguous binding)** is answered by removing
   the ambiguity surface, not by detecting it. If a future release's
   concrete usage pattern needs multiple same-interface providers resolved
   by something other than "the application chooses which value to pass,"
   that is new evidence against this document's P7 decision.
3. **R36's `ExecutionResult` does not yet exist.** P6 fixes the seam
   (layers a/b/c) but not R36's exact taxonomy; R36 contract work must
   satisfy the seam without re-normalizing layer (a)/(b) results into its
   own envelope.

None of these open issues are current blockers to R24–R31; they are
conditions R32/R35/R36 contract authors must check against before freezing
their own provider/resource models.
