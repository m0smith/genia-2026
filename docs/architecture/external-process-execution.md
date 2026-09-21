# External Process Execution Architecture

Status: Architecture and planning record — not implemented and not a language
contract. This document fixes boundaries for a later contract; it adds no
syntax, builtin, runtime behavior, host adapter, Flow behavior, subprocess API,
Core IR node, or capability-registry entry. `GENIA_STATE.md` remains final
authority.

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
execution.process  = planned external executable/process execution
```

An implementing host will use R16's existing `supported`, `partial`, or
`unsupported` declaration vocabulary. Absence of this optional capability will
not by itself make a host generally nonconforming. The future contract may add
`execution.process` to the existing registry; this record does not add it or
create another registry.

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
protected payloads. The future contract must reconcile exact authority purpose,
sink behavior, and declassification with R10.

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
external-process cancellation. The first slice requires finite timeout plus
deterministic child cleanup. General `cancel`, `kill`, and signal behavior
remain deferred.

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
designs a portable shell language.

## First-slice non-goals

- shell interpretation, shell pipelines, globbing, quoting, or redirection;
- public streaming output, interactive processes, or TTY semantics;
- signals or general cancellation;
- remote execution, actor or scheduler integration;
- durable jobs or generalized process supervision;
- Core IR changes.

## Roadmap relationship

This capability is cross-cutting planned architecture, not a new numbered
release and not implemented by an earlier completed or C++ bring-up release.
R35 may inform the deferred working-location decision. External direct
execution is not R36 location-independent Genia execution: a local process
provider may later sit beneath broader execution architecture, but R36
describes bounded Genia computation independent of physical placement. R37 is
a concrete dogfooding consumer because Genia-native conformance tooling must
eventually invoke host adapters. Any numbered release placement requires
separate approval.

## Next phase

After review of this record, the next phase is **PROCESS EXECUTION CONTRACT**,
not implementation.
