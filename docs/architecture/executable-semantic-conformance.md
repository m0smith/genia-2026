# Executable Semantic Conformance Architecture

Status: **Architecture/pre-flight — non-authoritative.** This document defines no
Genia language or runtime behavior. `GENIA_STATE.md` remains final authority.

Issue: #991

## Purpose

Genia already has an executable multi-host conformance architecture. The goal of
this document is to make its existing semantic-evidence chain explicit enough
that new portable behavior can be added without rediscovering portability rules
inside a host implementation.

This is a strengthening of R16, not a replacement for it.

## Existing architecture to preserve

R16 already provides the mechanisms needed for multi-host proof:

- one authoritative repository for language contract, Core IR, shared specs,
  protocol, and generic runner;
- a versioned host-adapter protocol with host-neutral `parse`, `lower`,
  `eval`, `cli`, and `capabilities` operations;
- one capability vocabulary owned by `spec/manifest.json` and described by
  `docs/host-interop/capabilities.md`;
- per-case `requires:` applicability;
- exact contract-revision identity;
- deterministic evidence;
- explicit PASS / FAIL / UNSUPPORTED / PROTOCOL ERROR / CRASH / TIMEOUT
  classification;
- the rule that unsupported behavior is never a pass;
- the rule that host disagreement is resolved against the authoritative
  contract/shared evidence, never by copying another host.

R24 already strengthens this operationally: capability claims are evidence
backed, capability growth is explicit, applicable shared cases are inventoried,
and unresolved semantic ambiguity is a release blocker.

No parallel runner, protocol, capability registry, evidence format, or semantic
authority is needed.

## The semantic-evidence chain

The intended maintenance path is:

```text
authoritative implemented truth
  GENIA_STATE.md
        |
        v
supporting contract / rules / portable boundary
        |
        +---------------------------+
        |                           |
        v                           v
portable representation       semantic sync guardrails
(Core IR where applicable;    semantic_facts.json where useful
 ordinary values/protocol/
 capability contract otherwise)
        |
        v
shared executable spec cases
        |
        v
spec/manifest.json capability vocabulary
+ per-case requires
        |
        v
R16 generic host protocol
        |
        v
host capability claim
        |
        v
deterministic evidence
```

This is a traceability model, not a new source-of-truth hierarchy.
`GENIA_STATE.md` remains authoritative. Not every semantic fact needs an entry
in `semantic_facts.json`, and not every semantic boundary belongs in Core IR.

## Current traceability inventory

| Link | Current mechanism | State |
| --- | --- | --- |
| Implemented behavior -> authority | `GENIA_STATE.md` hierarchy in `AGENTS.md` | Strong and process-enforced |
| Cross-doc semantic fact -> drift guard | `docs/contract/semantic_facts.json` + doc sync tests | Machine-checkable for selected protected facts, intentionally not exhaustive |
| Portable syntax/value semantics -> representation | Core IR plus ordinary value/protocol contracts | Strong where explicitly contracted; must remain concern-specific |
| Portable behavior -> executable cases | shared YAML under `spec/` | Strong for behavior represented by shared cases; coverage is incremental |
| Case -> required capability | case `requires:` + `spec/manifest.json` vocabulary | Machine-checkable |
| Capability -> host claim | R16 `capabilities` operation | Machine-checkable |
| Claim -> proof | generic runner + deterministic evidence | Machine-checkable |
| Release slice -> complete traceability | release-specific practice, especially R21/R24 | Present as precedent, not yet a single cross-cutting obligation |

The last row is the principal gap. The architecture is already present; the
maintenance obligation is not stated once as a general rule.

## Semantic-change conformance obligation

For future work that adds or changes **portable observable behavior**, its
contract/design gate should answer all of the following before a host-specific
implementation is treated as the definition of the behavior:

1. **Authority:** what exact portable behavior will become implemented truth if
   the slice lands?
2. **Boundary:** where is that behavior represented? This may be Core IR,
   ordinary Genia values, an existing protocol, or a capability/provider
   contract. Core IR is not the default answer for effects or live resources.
3. **Executable proof:** which shared cases demonstrate the portable
   observations? If shared evidence is impossible, the design must say why and
   must not imply cross-host conformance it cannot prove.
4. **Applicability:** which existing capability names gate those cases? Add a
   capability only when the behavior introduces a genuinely new independently
   claimable host surface.
5. **Host evidence:** what must a host claim and pass before that capability is
   reported supported?
6. **Truth synchronization:** which authoritative/current-behavior docs change
   after implementation and verification?
7. **Ambiguity stop:** if an implementing host must inspect another host's source
   to determine observable semantics, stop and repair the contract/shared
   evidence first.

This obligation generalizes existing R16 policy and R21/R24 practice. It does
not add language behavior.

## Capability coverage, not a second profile system

Do not introduce an independent conformance-profile taxonomy now.

The existing capability vocabulary already answers the useful question:
**which independently claimable portable surfaces does this host support, and
what evidence applies to each?**

If human-facing groupings become useful, derive them as views over existing
capabilities and shared-case evidence. Examples might later group capabilities
for reporting as core values, flow, lifecycle, storage, or execution, but such
groupings must not:

- change case applicability;
- allow a host to pass a group while failing a required capability;
- become a second capability registry;
- create semantic dependencies absent from the underlying contracts.

A new profile mechanism is justified only if a concrete future requirement
cannot be expressed as a derived view over the existing vocabulary.

## Capability-backed semantics and provider realization

Future storage, execution, events, and actors need two deliberately separate
layers:

```text
portable semantic contract
        |
        v
portable values / Outcomes / lifecycle / Flow / identity rules
        |
        v
explicit capability/provider boundary
        |
        +-------------------+-------------------+
        v                   v                   v
      local               process              cloud
   realization          realization          realization
```

The upper layers define observable Genia meaning. The lower layer defines how an
environment realizes the required effect.

Existing architecture already constrains this split:

- R14 supplies lifecycle ownership rather than provider-local lifetime rules.
- R16 supplies capability declaration and fail-closed applicability.
- R18 supplies identity/equality families rather than component-local equality.
- provider-composition preflight supplies explicit opaque providers, explicit
  binding, authority separation, and normalized failures rather than ambient
  discovery.
- R35 is planned to own portable storage/resource semantics.
- R36 is planned to own location-independent Genia execution.
- R37 is planned to consume those boundaries while moving conformance
  orchestration into Genia.

A local implementation is therefore a realization of portable semantics, not
the semantic definition.

## Implications for events and actors

Events and actors should enter the roadmap only after their own contracts can
fit the same chain.

For an event system, architecture work should separately define at least the
portable event observation/delivery contract, subscription identity and
lifecycle, ordering guarantees, failure/backpressure behavior, and the
capability boundary for realization. Local queues, cloud pub/sub, and other
transports must not define those semantics by accident.

For actors, architecture work should separately define actor identity,
message/protocol semantics, lifecycle/supervision, state transition
observations, failure/restart semantics, Flow participation, and placement
versus realization. A Genia-only local actor and an AWS-backed actor should be
two realizations of the same approved portable contract where that contract
requires equivalence.

This document deliberately does not choose those semantics or assign release
numbers. It only establishes the conformance obligation they must satisfy.

## R24 as the proving ground

R24 is the first real opportunity to detect semantic-evidence gaps using an
independent implementation.

The existing R24 preflight already requires:

- a declared C++ capability set;
- exact applicable shared-case inventory;
- deterministic R16 evidence;
- zero failed applicable cases for the claimed minimal capability set;
- honest unsupported classification outside that set;
- no unresolved semantic ambiguity.

During R24, the following condition should be treated as a portability finding:

> C++ needs to inspect Python implementation source to determine an observable
> Genia result that is not already fixed by authoritative contract/shared
> evidence.

The response is not to document Python behavior in C++. The response is to stop
that C++ slice, clarify Genia's authoritative contract if needed, add or repair
shared evidence, and then resume the host.

The current R24 materials already anticipate this: the issue sequence permits a
slice to add missing shared evidence when it finds a genuine gap.

## Smallest useful change now

The smallest useful change is **process hardening, not runtime
infrastructure**.

After skeptical review, the recommended implementation follow-up is to add one
repository-level semantic-change/conformance checklist or testable process
guard that requires portable feature work to identify:

- portable authority/boundary;
- shared conformance evidence;
- capability applicability;
- host-evidence impact;
- documentation synchronization.

It should reuse the existing R16 mechanisms. It should not add a semantic
manifest, new runner, new evidence format, new profile registry, or new Core IR.

Before implementing even that process change, inspect whether an existing
process document can carry the obligation without another artifact. Prefer one
small edit plus focused validation over a new subsystem.

## Relationship to R37

R37 remains unchanged in purpose.

R37 should make the conformance **orchestration** Genia-native after R35/R36
provide the portable storage/execution mechanisms it needs. It should preserve
R16's protocol taxonomy, capability discovery, revision checks, applicability,
comparison, and evidence semantics.

This architecture should therefore make R37 easier, but must not implement R37
early.

## Skeptical review

The proposal was challenged against the main failure modes in issue #991.

### Does it duplicate R16?

**No, if kept at this scope.** Every execution mechanism is reused from R16.
The proposal adds no runner, protocol, evidence format, applicability rule, or
capability registry. A future implementation that creates any of those without
a separately demonstrated gap should be rejected.

### Does it create a second capability system?

**No.** It explicitly rejects independent profiles. Reporting groups, if ever
needed, are derived views over `spec/manifest.json` capabilities and shared
case evidence.

### Does it bloat Core IR?

**No.** The semantic-change obligation requires an explicit portability
boundary but states that Core IR is only one possible boundary. Effectful/live
resource behavior normally belongs in ordinary values/protocol/capability
contracts instead.

### Does it pull R37 forward?

**No.** The generic runner remains Python infrastructure. No Genia-native YAML,
storage discovery, host invocation, comparison, or evidence orchestration is
introduced.

### Does it confuse host portability with distributed execution?

**No.** R16 remains the host-conformance mechanism; R36 remains the planned
location-independent execution abstraction. Provider realization is explicitly
below portable semantics.

### Does it make `semantic_facts.json` a second language definition?

**No.** Semantic facts remain selective cross-document drift guards.
`GENIA_STATE.md` remains final authority.

### Is a new machine-readable semantic manifest required?

**No evidence currently justifies one.** Existing capability and spec metadata
already support executable applicability/evidence. The missing piece is a
cross-cutting maintenance obligation. Building a semantic meta-model now would
add duplication and drift risk without a demonstrated consumer.

## Verdict and stop gate

**PASS for architecture/pre-flight, with a narrow recommendation.**

The repository does not need a new executable-conformance subsystem. R16 is
already that subsystem. R24 should be used to expose contract/evidence holes,
and future portable features should be required to connect their semantic
contract to shared cases, existing capability applicability, and deterministic
host evidence.

The only immediate follow-up recommended by this architecture is a small
process-level conformance obligation using existing machinery.

**STOP:** Do not implement that follow-up, modify runtime behavior, add
capabilities, change Core IR, renumber the roadmap, or begin event/actor
semantics as part of issue #991 without explicit approval.
