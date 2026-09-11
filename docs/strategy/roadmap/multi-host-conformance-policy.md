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

## Evidence model and CI expectations (complete as of E16-7, issue #764)

`tools/spec_runner --host '<command>' --evidence <path>` (`tools/spec_runner/evidence.py`)
publishes one deterministic JSON evidence document per run, recording exactly the
observable claims this policy requires:

- `protocol_version`
- `contract_revision`: `declared` (what the host claimed), `checkout` (what
  this run actually tested against), and `classification` (`current` /
  `resolvable_ancestor` per E16-4's pinned-conformance-vs-current-main-
  compatibility distinction — `unresolvable` never reaches evidence, since
  the run stops before any case executes)
- `capabilities` (the host's full claimed-capability map) and
  `capability_operations` (which of `parse`/`lower`/`eval`/`cli` it
  implements at all)
- `total_cases` and `applicable_cases` (`total_cases` minus invalid specs)
- `counts`: `pass`, `fail`, `unsupported`, `protocol_error`, `crash`,
  `timeout`, `invalid` — every discovered case resolves to exactly one of
  these; `build_evidence` raises rather than publish a document whose
  counts do not sum to `total_cases`

The document is a pure function of the run's inputs (`json.dumps(...,
sort_keys=True, indent=2)`): identical inputs always produce
byte-identical evidence, so repeated runs are directly comparable. No
capability or category can be summarized as passing merely because it was
unsupported or unexecuted — that state is always its own field, never
folded into `pass`.

**External-host CI expectations:**

- pin an exact `genia-2026` revision in CI (checkout that revision, or an
  equivalent pinned mechanism) and declare it as `contract_revision` in
  the host's `capabilities` response
- run `tools/spec_runner --host '<adapter command>' --evidence
  <artifact-path>` against that pinned checkout; publish the evidence
  document as a CI artifact
- fail the CI job on the runner's exit code, which is nonzero exactly
  when `fail`, `protocol_error`, `crash`, `timeout`, or `invalid` is
  nonzero — `unsupported` alone never fails the job
- separately, and non-blocking, run the same host binary against current
  `genia-2026` `main` to surface `resolvable_ancestor`-classified drift
  evidence; a host may legitimately show `fail`/drift there while its
  pinned-revision run stays clean — that is the intended signal, not a
  contradiction to reconcile
- `genia-2026` proves this same evidence model works for the Python
  reference host (`hosts/python/protocol_adapter.py`) and for a fixture/
  external-bootstrap path (`tools/spec_runner/fixtures/
  protocol_fixture_adapter.py`; `m0smith/genia-cpp`'s
  `bootstrap/protocol_adapter_stub.py`) before any real second host is
  required to use it

The exact cross-repository CI vendor/checkout mechanics beyond "pin a
revision, run the generic protocol, publish the evidence artifact" remain
each host repository's own choice; this policy fixes the observable
claims, not a particular CI product.

## Host repository transition (complete as of E16-6, issue #763)

R16 E16-6 created/bootstrapped [`m0smith/genia-cpp`](https://github.com/m0smith/genia-cpp)
as the first external production-host repository: a repository shell
(`README.md`/`AGENTS.md` naming `genia-2026` as authoritative, a pinned
`genia-2026` contract revision and E16-1 adapter-protocol version, and a
minimal, self-contained, non-semantic protocol-participation placeholder)
with **no real C++ interpreter**. `hosts/cpp/` in `genia-2026` transitioned
in the same change to a pointer/scaffold location (see `hosts/cpp/
README.md`); no duplicate authoritative-looking C++ implementation exists
in two locations. Production C++ implementation belongs in
`m0smith/genia-cpp`, landing in R21 (`docs/strategy/roadmap/r16-r20.md`),
unless a later approved architecture decision changes this plan.

## Scope guardrail

R16 (E16-1 through E16-7, issues #758-#764) has landed: a generic multi-host
conformance runner now exists (`tools/spec_runner --host`), proven against
the Python reference host and the `m0smith/genia-cpp` bootstrap placeholder.
Current truth, unchanged by this policy document: Python remains the only
implemented **production** host, and no real second production host is
implemented yet. See `GENIA_STATE.md` §0 for the authoritative statement.
