# Multi-Host Conformance Policy

Status: **Planned architecture/process policy — non-authoritative.**
This document does not define implemented Genia behavior. `GENIA_STATE.md` remains final authority.

## Repository boundary

Beginning with R16 planning, `genia-2026` is the authoritative language, reference-host, and conformance repository. It owns the language contract, Core IR portability boundary, shared semantic specs, generic conformance protocol/runner, and the Python reference host.

Substantial non-Python production hosts are planned to live in dedicated repositories such as `m0smith/genia-cpp`. External host repositories implement Genia; they do not define Genia. No external host repository may override or silently fork `GENIA_STATE.md`, `GENIA_RULES.md`, `GENIA_REPL_README.md`, shared specs, or the portable contracts in this repository.

The dependency direction is one-way:

```text
genia-2026  ---> authoritative contract/spec/protocol ---> external host repositories
```

A host implementation must not become an upstream source of language truth.

## Host Portability Is Not Distributed Execution

Multi-host conformance and distributed execution are independent concerns.

Multi-host conformance asks whether different host implementations preserve the
same observable Genia semantics.

Distributed execution asks whether one logical computation may be physically
realized across multiple processes, machines, transports, or infrastructure
components.

R16-R23 multi-host work must not accidentally introduce distributed-execution
semantics merely to enable another host.

Likewise, a future distributed realization must not define language semantics
through the behavior of one host or infrastructure provider.

See `docs/architecture/execution-realization.md` for the parked architectural
direction.

## Conformance claim rule

A host may claim support for a Genia capability only when it passes the authoritative shared specs applicable to that capability against the exact Genia contract revision it declares.

Each external host is planned to record at least:

- the exact `genia-2026` contract revision it targets
- the host-adapter protocol version it implements
- the capabilities it claims as supported, partial, or unsupported
- the conformance result for every applicable selected shared case

`unsupported` is not `pass`. Unexecuted, silently skipped, malformed, crashed, or protocol-invalid cases must never be reported as conformance passes.

## Pinned conformance and current-main compatibility

R16 should distinguish two different questions:

1. **Pinned conformance** — does the host correctly implement the exact `genia-2026` revision it claims?
2. **Current-main compatibility** — would that host also pass the applicable conformance suite from the current `genia-2026/main`?

Pinned conformance is the release/certification claim. Current-main compatibility is a forward-drift signal. A host can therefore remain correctly conforming to its declared revision while being visibly behind current `main`.

## Capability-aware synchronization

Hosts are not required to expose identical capability sets. Synchronization means identical observable behavior for every capability a host claims, not forced support for every Python-host-only surface.

The conformance report should make at least these states explicit:

```text
PASS
FAIL
UNSUPPORTED
PROTOCOL ERROR
CRASH/TIMEOUT
```

Future public host status may use maturity labels such as Reference, Conforming, Experimental, or Stale, but exact labels belong to the R16 contract/design gate. Status must be derived from evidence rather than manually optimistic documentation.

## Drift handling rule

When a non-Python host disagrees with the shared contract/spec, do not copy another host implementation merely to make the test pass.

The required loop is:

```text
host disagrees with shared evidence
  -> inspect the authoritative Genia contract/spec
  -> if the contract is clear, fix the host
  -> if the contract is ambiguous, stop host-side guessing
  -> clarify the contract in genia-2026 and add/adjust shared evidence
  -> resume the host implementation
```

A successful host implementation should not require opening another host's implementation source to infer Genia semantics. Needing Python implementation details to resolve observable behavior is evidence of a portability-contract gap.

## Planned CI model

R16 should make a generic runner capable of invoking a host adapter without embedding host-specific implementation knowledge. External-host CI should pin and test a declared `genia-2026` revision. `genia-2026` should also make it easy to run registered hosts, or fixture substitutes where cross-repository credentials are inappropriate, against candidate/current shared specs.

A conformance summary should publish, per host and category/capability:

- contract revision
- protocol version
- claimed capabilities
- applicable case count
- pass count
- fail count
- unsupported count
- protocol/crash/timeout count

The exact cross-repository CI mechanics remain an R16 design decision. This planning policy requires the observable claims, not a particular CI vendor or checkout strategy.

## Planned host repository transition

R16 may create/bootstrap `m0smith/genia-cpp` as the first external production-host repository, but R16 must not implement the real C++ interpreter. Existing `hosts/cpp/` scaffolding in `genia-2026` should be migrated deliberately so there is never a duplicate authoritative-looking C++ implementation in two locations.

During transition, `hosts/cpp/` may become a pointer/scaffold/metadata location. Production C++ implementation introduced by R19 and later C++ releases belongs in `m0smith/genia-cpp` unless a later approved architecture decision changes this plan.

## Scope guardrail

This policy is planning/process guidance only. Until R16 lands, current truth remains unchanged: Python is the only implemented/reference host and no generic multi-host runner exists.
