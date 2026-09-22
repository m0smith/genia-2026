# External Process Execution Architecture

Status: Architecture and planning record — not itself a language contract.
This document fixed the boundaries later consumed by the
[external direct process execution contract](../design/execution-process-contract.md)
and [implementation design](../design/execution-process-design.md), both
now approved, and the resulting `execution.process` capability is now
**implemented in the Python reference host** — see `GENIA_STATE.md`
section 9.40 for the authoritative implemented contract and
`docs/host-interop/capabilities.md` for its registry entry. This document
itself still adds no syntax, host adapter, Flow behavior, or Core IR node
of its own; where a boundary below was resolved by the approved contract,
this record notes the resolution rather than restating it. `GENIA_STATE.md`
remains final authority for implemented behavior.

## Classification and namespace

```text
Capability:       execution.process
Portability:      optional portable
Acquisition:      explicit opaque provider/authority
Semantic surface: portable bounded direct-execution semantics
Core IR:          unchanged
```

The namespaces remain distinct:

```text
process.*          = implemented Genia logical process/actor facilities
execution.process  = implemented (Python reference host) external
                      executable/process execution; portable contract,
                      registered as execution_process in spec/manifest.json,
                      not yet exercised by any shared-spec case
```

An implementing host will use R16's existing `supported`, `partial`, or
`unsupported` declaration vocabulary. Absence of this optional capability will
not by itself make a host generally nonconforming. `execution.process` is
registered as `execution_process` in `spec/manifest.json`'s registry
(matching the existing name-only-registration precedent of other
Python-host-only capabilities such as `shell_stage`); no shared-spec case
requires it yet, since no host-neutral provisioning mechanism exists to
exercise that claim (see `docs/host-interop/capabilities.md`'s
`execution.process` entry for the full reasoning); this record still does
not create another registry.

## Provisioning boundary

External execution follows the capability-provisioning model in
[Host Capability Taxonomy](host-capability-taxonomy.md): host support is
combined with policy to produce an explicit opaque program capability. Host
support is not program authority. The exact source-level acquisition API,
provider shape, and authority purpose remain for the later contract; there is
no ambient giant host namespace or dependency-injection framework.

## First contract target

The first future proving slice is deliberately collected and bounded:

```text
explicit execution.process capability
             +
bounded direct execution request
             ↓
one host execution attempt
             ↓
Outcome<ProcessResult>
```

The likely minimum request concerns `executable`, structured `args`, and
`timeout_ms`; these are concerns, not approved source syntax or finalized value
shapes. The later contract must specify:

- direct executable invocation with structured argv and no implicit shell;
- a finite timeout, bounded collected stdout/stderr, and deterministic child
  cleanup on timeout;
- host-side draining of stdout and stderr safely/concurrently enough to avoid
  pipe deadlock, without implying a public concurrency or streaming API;
- nonzero child exit as an execution result rather than automatically a Genia
  runtime failure;
- launch, transport, or provider failure as distinct from child exit status;
- reuse of ordinary Outcome conventions.

The current R16 conformance runner is concrete evidence for this shape: its
host-adapter path invokes an executable, waits, captures stdout and stderr,
observes exit status, and classifies timeout or process failure. It remains
bootstrap infrastructure, not an `execution.process` implementation, and is
not changed by this record.

## Security and authority

Process argv or future environment values must not bypass R10 protection:

> Protected values may cross the external-process boundary only through an
> explicitly authorized sink/declassification path.

Execution handles contain execution identity/state, not undeclassified
protected payloads. **Resolved by the approved v1 contract** (rejection
before any resolution or provider effect, via R10's existing machinery,
with no sink and no authority argument in this phase) — see
`GENIA_STATE.md` section 9.40 for the implemented mechanism. A later
contract would need its own sink/purpose/non-leak proof to add one,
exactly like R14's protected-HTTP-header sink required its own.

The process capability must not silently grant access to the complete parent
environment. Environment behavior is deferred and remains subject to R10;
existing configuration environment snapshots are separate and unchanged.

## Deferred boundaries

### Executable resolution

This record does not promise that `"git"` means “search host `PATH`.” `PATH` is
ambient state and differs or may be absent across POSIX, Windows, containers,
sandboxes, browser/WASM hosts, remote workers, and allowlisted providers. A
later contract may choose provider-specific resolution or an explicit resolver.

### Working location

External-process `cwd` is not Genia Store/Location merely because both may use
path-like values. It is deferred until R35 establishes the portable storage and
resource boundary and that relationship can be evaluated.

### Lifecycle and cancellation

R14 provides lifecycle ownership and cleanup; it does not provide general
external-process cancellation. **Resolved by the approved v1 contract and
now implemented** as bounded, timeout-driven cleanup (not general
cancellation) — see `GENIA_STATE.md` section 9.40 for the exact timeout
bound and termination guarantee. General `cancel`, `kill` as a public
operation, signal identity, and process handles remain deferred.

### Flow and internal concurrency

Current Flow remains lazy, pull-based, and single-use. Public streaming process
output, including whether it could later compose through Flow, is deferred. The
collected first slice avoids prematurely defining concurrent multi-port Flow
semantics. Internal concurrent pipe draining does not imply a public streaming
API.

### Shell execution

`execution.process` and a possible future `execution.shell` are distinct.
Structured `executable + argv` can have portable direct-execution semantics;
shell text delegates quoting, pipelines, expansion, redirection, globbing, and
builtins to a shell dialect. Genia must not silently turn structured invocation
into shell command text. This record neither contracts `execution.shell` nor
designs a portable shell language. **Resolved by the approved v1 contract and
now implemented:** `execution.process` remains a distinct, permanently
separate surface from the pre-existing Python-host-only shell pipeline
stage `$(...)` (`GENIA_STATE.md` section 3), which it does not wrap or
supersede — see section 9.40 for the launcher's exact no-shell,
no-PATH-search guarantee.

## First-slice non-goals

- shell interpretation, shell pipelines, globbing, quoting, or redirection;
- public streaming output, interactive processes, or TTY semantics;
- signals or general cancellation;
- remote execution, actor or scheduler integration;
- durable jobs or generalized process supervision;
- Core IR changes.

## Roadmap relationship

This capability is cross-cutting architecture, implemented in the Python
reference host without a new numbered release and not implemented by an
earlier completed or C++ bring-up release (`m0smith/genia-cpp`/R24 does
not implement it). R35 still owns the still-deferred portable
working-location (`cwd`) decision this capability does not touch. External
direct execution is not R36 location-independent Genia execution: a local
process provider may later sit beneath broader execution architecture, but
R36 describes bounded Genia computation independent of physical placement,
and R36 remains entirely unimplemented future architecture — nothing here
changes that. R37 (Genia-native conformance tooling, also unimplemented)
remains a concrete future dogfooding consumer, now with a real, already-
implemented primitive available to consume once R37 itself begins;
`execution.process` is not thereby part of R37 and R37 is not thereby
started. Any numbered release placement requires separate approval.

## Current status

The contract is approved and merged
([`docs/design/execution-process-contract.md`](../design/execution-process-contract.md)),
its implementation design is approved
([`docs/design/execution-process-design.md`](../design/execution-process-design.md)),
and the Python reference host implements it — see `GENIA_STATE.md` section
9.40 for the authoritative implemented contract. This architecture record
remains a planning document; it is not re-litigated by the completed
implementation, and any further evolution (protected sinks, environment,
cwd, streaming, signals, provisioning ergonomics, R16 registration) is new,
separately scoped work.
