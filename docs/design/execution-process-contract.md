# External Direct Process Execution Contract

Status: **Approved and implemented.** This contract was approved
(independent contract review passed, PR #977, merged) and is now
implemented in the Python reference host per
[`docs/design/execution-process-design.md`](execution-process-design.md)
— see `GENIA_STATE.md` section 9.40 for the authoritative implemented
contract and `docs/host-interop/capabilities.md` for its registry entry.

This document remains the frozen contract text below, preserved as the
approved baseline; it is not rewritten into an implementation document.
Where this document says a behavior is not yet implemented (capability-
registry entry, shared spec, runtime test, Core IR node, etc.), read that
against `GENIA_STATE.md` for current implemented truth — this file
describes what the contract *requires and permits*, not a live status
report.

## 1. Scope

The first slice lets ordinary Genia code consume an already-provisioned process
capability, request one bounded direct executable attempt, and observe an
Outcome containing a closed result or a normalized failure:

```text
explicit execution.process capability
             +
closed direct-execution request
             |
             v
execution.process(capability, request) -> some(ProcessResult) | err(reason, context)
```

It is sufficient for a future conformance runner to invoke one adapter with
structured arguments, wait within a finite deadline, collect bounded stdout and
stderr, and inspect the exit status. The conformance runner is the proving
consumer, not the definition of the abstraction.

The namespaces are permanently distinct:

```text
process.*          = Genia logical processes and mailboxes
execution.process  = external direct executable execution
```

## 2. Architecture dependencies

This contract specializes, without reopening, these existing boundaries:

- the host-capability taxonomy: optional portable semantics, explicit
  provider/authority acquisition, and a portable Genia semantic surface;
- R10 protected carriers and explicit authorized sinks;
- R14 synchronous ownership and cleanup, without general cancellation;
- R16 `supported` / `partial` / `unsupported` host declarations, which report
  support but never grant program authority;
- current lazy, pull-based, single-use Flow and synchronous source
  finalization, which this collected operation does not change;
- the frozen ordinary-call Core IR boundary; and
- the separation of logical computation, execution realization, and
  infrastructure realization.

R35 may later define portable working-location concepts. R36 concerns
location-independent execution of Genia computation and is not this direct
process facility. R37 is the first intended dogfooding consumer. This
cross-cutting contract has no release number.

## 3. Capability classification and provisioning

`execution.process` is classified as follows:

```text
Portability:      optional portable
Acquisition:      explicit provider/authority
Semantic surface: portable bounded direct-execution semantics
Core IR:          unchanged ordinary call/value behavior
```

The first public argument is one opaque, host-supplied process capability. It
contains both the provider realization and the authority/policy to use the
symbolic executable identities provisioned into it. Source cannot construct,
copy, serialize, compare, render meaningfully, or derive this value. It is not
a process handle and contains no child execution state.

The source-level bootstrap operation that obtains this capability is deferred.
Provisioning must combine an R16 host-support claim with application policy and
must have this portable result:

```text
some(process_capability)
| err("process-unsupported", {capability: quote(execution_process)})
| err("process-unauthorized", {operation: quote(provision)})
| err("process-provider-failure", {operation: quote(provision)})
```

Unsupported is discovered during provisioning, not rediscovered by each call.
A host that declares `execution.process` unsupported remains conforming because
the capability is optional. A host declaration never creates authority. No
file, command, pipe, import, REPL, test, or server mode provisions this
capability implicitly, and there is no global `host` object or ordinary
`host.supports(...)` operation.

Design may choose the bootstrap API but may not alter the consumption contract
or make provisioning ambient.

## 4. Public operation

The exact first-slice callable is:

```text
execution.process(capability, request) -> some(ProcessResult) | err(reason, context)
```

It is an ordinary synchronous call. A valid call makes at most one launch
attempt. It performs no retry, fallback resolution, shell invocation, detached
execution, or background continuation.

A value that is not an opaque provisioned process capability is runtime misuse.
A capability that was validly provisioned but whose policy does not authorize
the requested symbolic executable returns the normalized authorization Outcome
defined below; it is not misuse.

## 5. Closed request shape

`request` is exactly this closed ordinary map:

```text
{
  executable: symbol,
  args: [string, ...],
  timeout_ms: integer
}
```

Validation occurs completely, in field order `executable`, `args`,
`timeout_ms`, before resolution, declassification, launch, or any provider
effect. Missing or extra keys, wrong value kinds, an invalid symbol, an invalid
argument element, or an invalid timeout are runtime misuse and cause zero
provider attempts.

The request deliberately has no environment, cwd, stdin, shell, capture,
encoding, output-limit, TTY, signal, or retry field. Providers cannot interpret
extra keys as extensions while claiming conformance to this operation.

## 6. Executable identity and resolution

`executable` is a non-empty Genia symbol, for example `quote(candidate_host)`.
It is a portable symbolic identity in the supplied capability, not a host path,
command string, URI, package name, or portable promise to search `PATH`.

Provisioning binds each authorized symbol to exactly one provider-native
executable target. The binding is immutable for the capability's lifetime.
One call performs exactly one lookup in that mapping and never tries aliases,
extensions, current-directory candidates, `PATH`, shell builtins, or another
provider. Two independently provisioned capabilities may deliberately bind the
same symbol differently; portable program behavior depends on the supplied
capability just as other explicit provider behavior does.

An unbound symbol returns:

```text
err("process-executable-unavailable", {executable})
```

An existing binding that policy denies returns:

```text
err("process-unauthorized", {operation: quote(execute), executable})
```

The provider-native target and any host path used to realize it never appear in
ordinary values, results, diagnostics, or failure contexts.

## 7. Argument semantics

`args` is an ordered list of ordinary strings. Each list element becomes
exactly one child argument after the provider-native executable's argument-zero
convention. The executable symbol itself is not inserted into `args`.

No layer in `execution.process` performs whitespace splitting, quoting,
unquoting, glob expansion, variable interpolation, command substitution, path
expansion, metacharacter handling, or text-to-argv parsing. Thus strings
conceptually equal to `"a b"`, `"*"`, and `"$HOME"` remain three exact
arguments. Any later interpretation belongs solely to the invoked executable.

NUL in an argument is runtime misuse because it cannot be represented
consistently by common native process interfaces. Empty strings and all other
valid Genia string contents are preserved exactly through the provider's
platform encoding boundary. A provider unable to represent a valid Genia
string returns `process-launch-failure`; it must not replace or lossy-convert
the value.

## 8. Timeout and cleanup

`timeout_ms` is a plain Integer in `1..300000`, matching the existing bounded
provider-call convention. Boolean values are rejected even on hosts where a
boolean is represented as an integer subtype. Zero, negative values, and values
above `300000` are runtime misuse.

The deadline covers resolution after request validation, launch, execution,
pipe draining, and collection. It begins immediately before provider resolution
and ends only when the child has terminated and both output channels have
reached end-of-stream.

When the deadline expires, the provider must stop the owned child execution,
reap or otherwise finalize all provider-owned child resources, and close its
owned output channels before returning:

```text
err("process-timeout", {timeout_ms})
```

No owned child may remain running indefinitely after the call returns. The
mechanism is host-specific and creates no portable signal or kill semantics.
Partial stdout and stderr are discarded on timeout and never enter the error
context.

Timeout cleanup is not general user-driven cancellation. This contract adds no
`cancel`, `kill`, `signal`, handle, or supervision operation.

## 9. Child stdin, environment, and working location

The child receives an immediate end-of-input on its standard input. The
caller's ambient Genia `stdin` is never forwarded, read, or consumed. There is
no child-stdin request data and no streaming input in this slice.

The request supplies no environment. Portable semantics neither inherit nor
expose the Genia host process environment. A provider runs the target in the
controlled environment fixed when that capability was provisioned. That
environment is immutable for the capability's lifetime, is not observable
through this API, and contains no ambient parent entry unless provisioning
policy deliberately supplied it below the Genia boundary. Existing R10/R13
configuration snapshots remain separate.

The request supplies no cwd. A provider may own a fixed execution root as part
of its private provisioned target, but Genia receives no host path semantics and
cannot vary or observe that root. Portable cwd remains deferred pending R35.

## 10. Output capture and bounds

The operation collects stdout and stderr as independent byte channels. It does
not decode them. Each channel has an independent fixed maximum of exactly
`1,048,576` bytes. A channel of exactly that size succeeds; observing one more
byte is overflow. The combined successful result can therefore contain at most
`2,097,152` captured bytes.

On overflow of either channel, the provider must stop and finalize the child by
the same no-owned-child-left-running guarantee used for timeout, discard all
partial output, and return:

```text
err("process-output-limit", {limit_bytes: 1048576})
```

The context intentionally omits a channel name so simultaneous or closely
ordered writes cannot produce host-dependent classification. Output limits are
contract constants, not provider options in v1.

A conforming host must drain bounded stdout and stderr without permitting one
full child-output channel to indefinitely block collection of the other. The
contract does not prescribe threads, async APIs, `communicate()`, or OS pipe
primitives.

Collected output is returned for every normal child exit, including nonzero
exit. It is never returned for resolution failure, launch failure, timeout,
overflow, provider failure, or any other `err` result. Consumers may explicitly
apply existing byte-decoding operations after success.

## 11. ProcessResult

Normal child termination returns:

```text
some({
  exit_code: integer,
  stdout: bytes,
  stderr: bytes
})
```

This is a closed map with exactly those keys. `exit_code` is a non-negative
Integer in `0..4294967295`. A provider must normalize its native normal-exit
status into that range without changing the value. A native termination that
does not yield a portable normal-exit status is a provider failure in this
slice; signal identity is not exposed.

A child that starts and normally exits with status `1` is therefore
`some({exit_code: 1, ...})`, not `err(...)`. Genia failure describes inability
to perform the requested execution attempt; a program's nonzero status is the
program's result.

The result excludes executable identity, PID, process handle, signal, duration,
timestamps, environment, cwd, provider identity, truncation flags, and retry
metadata. Output is never truncated: the call either returns the complete
bounded channels or `process-output-limit`.

## 12. Misuse and normalized failures

Malformed Genia arguments are runtime misuse and raise before any provider
effect. Misuse includes a non-capability first argument, a non-closed request,
invalid request fields, any protected leaf anywhere in the request, or any
opaque authority/provider value embedded in it. Diagnostics use only structural
field positions and value kinds; they never echo executable-native targets,
arguments, provider state, or protected payloads.

After successful validation, recoverable failures are exactly:

| Reason | Exact context | Meaning |
|---|---|---|
| `process-unsupported` | `{capability: quote(execution_process)}` | provisioning found no host support |
| `process-unauthorized` | `{operation: quote(provision)}` or `{operation: quote(execute), executable}` | provisioning or an existing capability policy denied the operation |
| `process-executable-unavailable` | `{executable}` | the capability has no target bound to the symbol |
| `process-launch-failure` | `{executable}` | the bound target could not be started or an argument could not be represented exactly |
| `process-timeout` | `{timeout_ms}` | the deadline expired and cleanup completed |
| `process-output-limit` | `{limit_bytes: 1048576}` | either collected channel exceeded its independent bound and cleanup completed |
| `process-provider-failure` | `{operation: quote(provision)}` or `{operation: quote(execute)}` | normalized provider/internal failure not covered above |

Contexts are closed maps. Raw exception text, native error numbers, native
paths, command echoes, stack traces, process identifiers, partial output, and
provider identities never cross the boundary. An implementation must not add a
new reason for native errors that fit an existing row.

If cleanup itself encounters a host failure after timeout or overflow, the
primary reason remains `process-timeout` or `process-output-limit`; cleanup
details remain host-local. The provider may not return until it has satisfied
the no-owned-child-left-running guarantee. A host unable to guarantee that is
not a conforming implementation of this capability.

## 13. Protected values and authority

V1 does not define a protected process sink. `executable` must be an ordinary
symbol and every argument must be an ordinary string. Recursive request
validation rejects a `GeniaProtected` leaf before resolution or launch. The
capability authorizes process execution policy; it is not an R10
declassification authority and cannot reveal protected payloads.

Consequently, this operation has no authority argument, no declassification
purpose, and no point at which a protected value is revealed. This is a
deliberate first-slice restriction: it prevents argv, diagnostics, process
listings, child echo behavior, and captured output from becoming an accidental
secret-exfiltration path. A later explicit protected argv or environment sink
requires its own contract and purpose, late declassification boundary, and
non-leak proof.

Child output is ordinary bytes supplied by an external program; it never gains
R10 protection implicitly. Applications must not pass secrets to a child by
first declassifying them in ordinary code and then treating this operation as a
protected sink.

## 14. Lifecycle relationship

The operation owns one synchronous execution lifetime. Resolution, launch,
execution, output collection, timeout/overflow cleanup, and provider-resource
finalization all complete before the Outcome is returned. An implementation may
reuse R14 lifecycle machinery internally, but no lifecycle handle or context is
part of this contract and no new R14 semantics arise.

This contract does not claim concurrent peer execution, async work, public
process ownership, general cancellation, or Flow finalization. Internal
concurrent pipe draining is only an implementation obligation needed to satisfy
the collected result.

## 15. Portability and compatibility requirements

Conforming implementations must agree on request validation, symbolic lookup
semantics, exact argv boundaries, no-shell behavior, timeout range and cleanup,
byte capture and limits, result shape, Outcome reasons and contexts, nonzero
exit treatment, and protected-value rejection.

Provider-native executable bindings, controlled environment contents, fixed
execution roots, and cleanup mechanisms remain below the boundary and are not
portable observations. They may differ only because the explicitly supplied
capability differs; they may not change the public operation contract.

The feature uses existing symbols, lists, strings, integers, bytes, maps,
ordinary calls, opaque host values, and Outcomes. It requires no parser, AST,
lowering, evaluator special form, Core IR, Flow, Seq, or pattern change. In
particular it adds none of `IrProcess`, `IrSpawnExternal`, `IrHostCall`, a shell
AST, or provider-specific IR.

## 16. Explicit non-goals

V1 does not define:

- shell execution or `execution.shell`;
- command text, quoting languages, pipelines, redirection, substitution,
  globbing, shell builtins, POSIX shell, PowerShell, or `cmd.exe`;
- public streaming stdout/stderr, multi-port Flow, backpressure, or Flow
  terminal changes;
- interactive stdin, streaming stdin, TTYs, consoles, or terminal control;
- environment request values or parent-environment inheritance;
- cwd or portable path/location semantics;
- protected argv, protected environment, or a declassification sink;
- signals, signal numbers, kill, general cancellation, process handles, PIDs,
  discovery, detached/background execution, supervision, durable jobs,
  schedulers, retries, or restart policy;
- remote execution, R36 Genia-computation execution, actor integration, or
  logical `process.*` changes;
- timing metadata, provider metadata, host-native diagnostics, or output
  truncation; or
- new syntax or Core IR.

`execution.process != execution.shell` is a contract invariant.

## 17. Future extension seams

Later contracts may add separate operations or versioned request shapes for an
explicit executable resolver, bounded child input, protected sinks,
environment, R35-based working locations, collected limits chosen below a
portable ceiling, streaming output, or host-specific shell facilities. They
must not reinterpret this closed request, make its symbolic identity mean
`PATH` lookup, weaken its bounds, or change nonzero exit into an Outcome error.

General cancellation, signals, TTYs, and remote/location-independent execution
remain separate semantic problems rather than optional flags on this request.

## 18. Proving target

A future R37-oriented proof should provision a capability binding such as
`quote(candidate_host)` to one R16 adapter target and demonstrate, without
special cases in this contract:

1. exact structured adapter argv;
2. finite timeout and owned-child cleanup;
3. complete bounded stdout and stderr bytes;
4. an observed normal exit status, including nonzero status as `some`;
5. normalized unavailable, authorization, launch, timeout, overflow, and
   provider failures; and
6. absence of shell, ambient stdin/environment, cwd, and protected-value
   leakage.

The proof may provision a private fixed execution root. It must not add cwd to
the portable request merely because the current Python spec runner accepts one.

## 19. Contract review result and open questions

This contract intentionally leaves no semantic choice to the future test
author for an in-scope behavior. The remaining questions are design/bootstrap
questions only:

- what source-visible or application-launch boundary names the provisioning
  operation; and
- how each host stores its private immutable symbol-to-target bindings and
  controlled environment.

Neither question may change the operation, request, result, or failure contract
above. The next phase is **independent contract review**, followed only after
approval by design, failing tests, implementation, documentation sync, and a
skeptical audit.
