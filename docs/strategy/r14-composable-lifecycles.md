# R14 — Composable Lifecycles

Status: **In progress; E14-0 contract approved (`docs/design/r14-composable-lifecycle-contract.md`)
and E14-1/E14-2/E14-3/E14-4 implemented (issues #621, #692, #693, #694).**
E14-5 through E14-15 remain planned, not implemented. This document
records approved release direction; `GENIA_STATE.md` remains final
authority for implemented behavior.

## Theme

> Make lifecycle an execution-scope model that composes vertically and
> horizontally, then prove it around repeated records and inbound/outbound HTTP.

R14 is the first release to execute the portable lifecycle vocabulary prepared
in R4 beyond R8's one dedicated server consumer. It must reveal one coherent
model rather than adding an HTTP framework, an AWK mode, or a second pipeline
state machine.

## Problem

R4 defines inert lifecycle plans, scope trees, annotation bindings, cleanup, and
failure vocabulary. R8 implements one focused server lifecycle, but it is not a
general lifecycle-plan runner. Real applications now need three forms of
composition that the implemented surface does not provide:

1. a long-lived scope creating shorter-lived child scopes;
2. multiple independent lifecycle concerns surrounding the same work unit; and
3. one lifecycle stack being entered repeatedly for elements consumed from a
   list or lazy Flow.

HTTP supplies the first vertical proving case:

```text
execution
└── server
    └── request
        └── http-client
```

Record processing supplies the horizontal and repeated proving case:

```text
pipeline/session
└── element #42
    ├── record-context
    ├── metrics
    └── diagnostics
```

Without a locked common model, R14 risks acquiring three unrelated lifecycle
systems, mutable ambient state, or lifecycle wrappers that duplicate
`map`/`filter`/`scan`/`refine`/`rules`.

## Approved release boundary

R14 is limited to six connected concerns:

1. lifecycle instances and parent/child execution scopes;
2. deterministic peer lifecycle attachment on one scope;
3. repeated element-scoped execution over eager and lazy sources;
4. lifecycle-owned binding of one explicit R10/R13 configuration provider;
5. one common outbound HTTP operation and client lifecycle over a narrow host
   transport capability; and
6. record-oriented and Bible-proxy proving applications plus cross-cutting
   hardening and truth synchronization.

The E14-0 contract must make every public call shape and observable result
explicit. Roadmap examples in this document are conceptual and do not authorize
syntax or implementation.

## One lifecycle model

R14 must keep three concepts separate:

```text
LifecycleDefinition
  inert description of phases, scopes, bindings, and policy

ExecutionScope
  one entered lifetime with optional parent, ordered attachments,
  context layers, owned resources, result, and failure

LifecycleInstance
  one active attachment of a definition to exactly one execution scope
```

Definitions do not execute themselves. Annotations remain metadata until an
explicit activation or invocation consumes them. Loading or importing a module
must not enter a lifecycle, bind a listener, acquire a provider, or perform
network IO.

R14 may implement the smallest explicit executor required by its contracted
definitions/scopes/instances. It must not imply that arbitrary R4 plan data or
action identifiers become a general programmable phase-graph runner unless
E14-0 explicitly contracts that behavior.

## Vertical composition

A parent execution scope may create a child scope while remaining active.
E14-0 must lock:

- the exact entered/active/completed/failed state model;
- child creation and result-return boundaries;
- which child failures are returned as Outcomes versus lifecycle failures;
- whether and how a caller chooses to propagate a child failure;
- child and parent resource ownership;
- cleanup eligibility and ordering;
- inherited context visibility and write ownership; and
- cancellation/shutdown behavior limited to the minimum needed by R14.

Required default invariants:

- no global mutable `current lifecycle` switch exists;
- a child cannot silently mutate parent state, context, or resources;
- child completion returns control and a result to the parent;
- child failure does not implicitly terminate the parent;
- child-owned resources finalize with the child; and
- parent-owned resources remain parent-owned.

## Horizontal composition

One execution scope may own multiple peer lifecycle attachments. Attachment
order is not parentage. The default ordering target is middleware-style nesting:

```text
A.before
B.before
C.before
work
C.after
B.after
A.after
```

E14-0 must lock partial-entry, work-failure, unwind-failure, and combined-failure
matrices. Only attachments that crossed the contracted entered/ownership
boundary receive cleanup or finalization. Cleanup failures never erase the
primary failure.

Peers may expose inward-readable context according to contract, but a peer
cannot silently mutate another peer's owned context, state, resources, or
configuration binding. Priority graphs, dependency resolution, and concurrent
peer execution are outside R14.

## Repeated element-scoped execution

R14 must distinguish:

- pipeline/session lifetime;
- one fresh element lifetime for each consumed element; and
- shorter nested-operation lifetimes created while processing an element.

The repeated executor surrounds existing transformation work; it does not
replace or reinterpret that work. Existing list/Seq-compatible and Flow laws
remain authoritative, including lazy pulling, bounded consumption, single-use
Flow behavior, and source finalization.

E14-0 must lock:

- the exact eager and lazy source boundary;
- when an element scope becomes entered;
- how work receives permitted lifecycle context without mutable lexical
  injection;
- result and failure shapes;
- behavior for filtering/absence/Outcome values if applicable;
- finalization on success, failure, short circuit, and bounded early stop; and
- what happens if work attempts to retain a context-dependent callable or lazy
  value beyond element-scope exit.

Element-local lifecycle context expires with its owning scope. Data that must
survive is copied into an ordinary Genia value. Lifecycle execution state is
not application accumulator state; applications continue to use ordinary
values and `scan` for that purpose.

## AWK-like future-regret pressure test

R14 does not add an AWK execution mode or special identifiers such as `NR`,
`NF`, `$0`, or `$1`. It must prove that a future ordinary lifecycle can own
record-execution context such as:

```text
record-context.record
record-context.fields
record-context.nr
record-context.nf
```

Future convenience projections would read scoped lifecycle context; they would
not become mutable lexical bindings or fundamental lifecycle concepts. The
record proving case must use existing Flow/Seq and Outcome semantics and must
not replace the existing AWK prelude helpers.

## Lifecycle-owned configuration binding

R13 intentionally deferred lifecycle/provider binding. R14 promotes candidate
C-1 from `docs/parking-lot/post-r13-configuration-followups.md` and gives it an
explicit issue owner.

One already-constructed immutable R10/R13 provider may be bound to an approved
execution scope. The binding is visible inward according to the E14-0 contract
so participating work can construct ordinary `config_view` and `secret_view`
values without repeatedly threading the provider through every call.

This is not dependency injection or ambient lookup. R14 must not change provider
identity, precedence, snapshots, Outcomes, purposes, protected carriers, sinks,
audit, or declassification. It must not introduce bare configuration names,
implicit process-environment reads, provider refresh, or mutable provider
replacement.

## HTTP operation and lifecycle

One common operation model must underlie all supported methods:

```text
HttpOperation {
  method
  base_url
  path
  headers
  query
  body
  response
}
```

E14-0 must lock the exact closed/open shape, supported methods, URL/path/query
construction, header normalization, body forms, response representation,
redirect policy, size/time limits if any, failure reasons, and protected-field
positions. Construction and inspection perform no network IO.

The conceptual client lifecycle is:

```text
prepare
→ authorize
→ send
→ receive
→ decode
→ finalize
```

Portable semantics belong to Genia. The Python reference host supplies only the
narrow outbound transport capability required to touch the network. Python
library types, exceptions, resource objects, and policy must not define the
portable contract.

Method annotations such as `@get` may land only after the common operation and
client lifecycle exist. They are inert operation descriptors using the current
annotation metadata model, not self-executing IO or separate verb runtimes.
Static operation policy belongs in metadata; dynamic request values remain
ordinary arguments and values as contracted.

## Protected HTTP sinks

Credential-bearing fields may be explicit authorized protected sinks. A
protected API key may cross that narrow transport boundary without becoming an
ordinary printable or serializable value and without ad hoc application-level
declassification.

R10 remains authoritative. R14 must prove non-leakage through printing,
display/debug formatting, logging, diagnostics, errors, JSON/CSV/Sheet/report
serialization, generic representation operations, inbound responses, and test
failure output.

## Proving applications

### Repeated record proof

One generic record pipeline must demonstrate:

- one pipeline/session scope;
- fresh element scopes;
- at least two peer lifecycle attachments per element;
- deterministic enter/work/reverse-unwind order;
- record, fields, record number, and field-count style context;
- no cross-element or post-scope context leakage;
- ordinary captured result values; and
- correct cleanup on failure and bounded early Flow termination.

### HTTP vertical proof

One Genia REST service must:

- accept an array of canonical Bible references;
- resolve a configured YouVersion base URL, Bible/version ID, and protected API
  credential through R13/R10;
- perform outbound client child lifecycles from an R8 request scope;
- decode upstream responses and return structured JSON; and
- contain child failures without killing the long-lived server lifecycle.

Automated tests use a controlled local upstream and fake credentials. CI must
not depend on YouVersion, public network availability, or a real credential.
The example proves composition only; it adds no Bible-specific semantics or
human-reference parser.

## Core semantic guardrails

- lifecycle surrounds execution; Flow/Seq continues to carry and transform values
- lifecycle context is distinct from lexical bindings
- context reads inward only as contracted; writes remain owned by the creating
  scope or lifecycle instance
- attachment order and parent/child ownership remain separate relationships
- no global mutable current lifecycle exists
- annotations remain inert until explicitly consumed
- import/load is never activation
- cleanup applies only to entered and owned boundaries
- cleanup never hides the primary failure
- lazy values do not implicitly retain expired element context
- no second Outcome, Template, representation, configuration, validation,
  server/routing/CORS, HTTP, or error model is introduced
- the R8 server primitives and R10/R13 configuration/protection semantics remain
  authoritative
- no parser, AST, or Core IR change is presumed; E14-0 must justify any exception

## Killer-workflow alignment

R14 is explicitly approved infrastructure with one direct killer-workflow proof.
Repeated element scopes let independent record context, metrics, tracing, and
diagnostic concerns surround Outcome-aware record transformations while leaving
values and `scan` in charge of data state. The record proving case protects
bounded lazy processing, diagnostic fidelity, and cleanup at the exact point
where production pipelines encounter partial failure.

The HTTP slice is indirect infrastructure. It demonstrates the same lifecycle
model at application/request/operation scope and proves that validated pipeline
applications can use configured protected upstream services without leaking
credentials or inventing host-specific semantics.

## Non-goals

R14 does not include:

- an AWK language mode or `$0`/`$1`/`NR`/`NF` syntax
- mutable lifecycle injection into lexical bindings
- lifecycle as a replacement for `map`, `filter`, `scan`, `refine`, or `rules`
- implicit context capture by lazy values
- a general arbitrary lifecycle-plan/action registry unless separately locked
  by E14-0
- async/await syntax, scheduler, actor supervision, or distributed execution
- concurrent server guarantees
- WebSockets, SSE, streaming APIs, or HTTP/2-specific semantics
- connection-pool configuration, retries, circuit breakers, cookies, or an auth
  framework
- dependency injection or service containers
- a second server/routing/CORS or configuration system
- human-language Bible-reference parsing or YouVersion-specific language APIs
- a browser runtime
- multi-host implementation

## Portability posture

- **Portability zone:** mixed portable lifecycle/HTTP semantics and one Python
  reference-host transport capability
- **Core IR impact:** none expected; planned source-visible behavior should use
  existing calls, values, functions, maps, annotations, representations, and
  Outcomes
- **Portable obligations:** scope/instance states, parent/child behavior, peer
  ordering, context ownership, repeated-element semantics, cleanup/failure
  results, HTTP operation normalization, client lifecycle, and protected sinks
- **Python reference-host obligations:** narrow outbound network acquisition and
  resource handling behind the advertised capability
- **Shared-spec impact:** eval/flow/error/parse/IR coverage where portable
  observations fit existing categories; live transport remains focused
  Python-host testing
- **Future hosts:** must implement the same advertised transport boundary or
  report it unavailable; they may not redefine lifecycle or HTTP policy

This posture is planning guidance. E14-0 must complete the current mandatory
portability analysis in `docs/process/extensions/portability-analysis.md`.

## Release sequence

Every behavior issue runs its own complete repository phase workflow. The
release epic is #619.

1. **#620 — E14-0: composable lifecycle and HTTP contract**
   - Complete current preflight and lock every portable/runtime/capability
     boundary. Contract only; no tests or implementation.
2. **#621 — E14-1: lifecycle instance and parent/child execution scopes — implemented**
   - Implemented the smallest HTTP-free instance/scope core:
     `lifecycle_scope`, `lifecycle_child`, `lifecycle_context`, the entry/
     work/unwind algorithm, and the scope lifetime state machine.
3. **#692 — E14-2: peer lifecycle attachment and deterministic unwind — implemented**
   - Proved horizontal composition (multi-peer attachment, deterministic
     enter/reverse-unwind order, the partial-entry/failure matrix at
     three-or-more peers, peer isolation) without encoding peers as parents
     and with no runtime-code change over the E14-1 core.
4. **#693 — E14-3: repeated element-scoped lifecycle execution — implemented**
   - Integrated fresh element scopes with eager (List) and lazy (Flow)
     sources via the new `lifecycle_repeat` builtin, composing the
     unchanged E14-1/E14-2 algorithm with existing Flow/Seq laziness and
     finalization — no new list/Flow mechanism.
5. **#694 — E14-4: lifecycle-owned configuration provider binding — implemented**
   - Promoted R13 follow-up C-1 without ambient lookup or DI: a pure
     `lifecycle_config(provider)` factory over the unchanged peer
     machinery, with reserved-name non-shadowing inherited entirely from
     the existing mechanism (no new code path).
6. **#622 — E14-5: common HTTP operation representation**
   - Implement inert normalized HTTP operation values without IO.
7. **#623 — E14-6: Python host outbound HTTP transport capability**
   - Supply the narrow host-only network boundary.
8. **#624 — E14-7: outbound HTTP client lifecycle**
   - Compose operation, child lifecycle, transport, decoding, and finalization.
9. **#625 — E14-8: protected HTTP credential sinks**
   - Extend R10 authorized sinks narrowly and prove non-leakage.
10. **#626 — E14-9: declarative outbound HTTP annotations**
    - Bind inert method metadata to the common operation/lifecycle.
11. **#627 — E14-10: server/request/outbound-client composition**
    - Integrate the R8 server path with nested R14 scopes.
12. **#695 — E14-11: repeated record lifecycle proving case**
    - Prove multiple peer lifecycles per pipeline element without AWK syntax.
13. **#628 — E14-12: YouVersion Bible proxy proving application**
    - Prove the configured, protected vertical HTTP path.
14. **#696 — E14-13: cross-mode lifecycle and HTTP hardening**
    - Prove inertness, cleanup/failure matrices, laziness, diagnostics,
      protection, capability normalization, and parse/Core IR preservation.
15. **#629 — E14-14: release examples and implemented-truth synchronization**
    - Publish only tested landed behavior; no runtime changes.
16. **#630 — E14-15: release truth audit and distillation**
    - Skeptically audit the complete boundary before closing #619.

Supporting documentation infrastructure issue **#697** publishes the roadmap
to the MkDocs site from this repository's single roadmap source. It may proceed
independently of #620, adds no R14 behavior, and must preserve the roadmap's
planning/non-authoritative status.

## Dependency shape

```text
#620
├── #621 → #692 → #693 → #695
│             └── #694
└── #622 → #623
          #621 + #622 + #623 → #624 → #625 → #626
          #692 + #624 + #626 → #627
          #694 + #627 → #628

#693 + #694 + #627 + #628 + #695 → #696 → #629 → #630
```

Parallelism is allowed only where the approved E14-0 contract makes the slices
independent. Issue numbering does not override dependency order.

## Ticket acceptance baseline

Every R14 ticket must:

- classify itself as **Current release: R14** only after E14-0 approval; until
  then it remains blocked planned work
- name #620 and all earlier dependencies
- distinguish portable semantics from Python reference-host capability work
- preserve R4 vocabulary, R8 server behavior, Flow/Seq laws, R9 composition,
  R10 protected semantics, and R13 provider/view semantics
- state context ownership, entry, cleanup, primary/cleanup failure, inert
  annotation, and import/load boundaries where relevant
- name affected shared specs, focused tests, core docs, book/cheatsheets,
  host-capability docs, release docs, and composability-matrix review
- use separate preflight, contract where applicable, design, failing-test,
  implementation, documentation, audit, and distillation phases
- commit failing tests before implementation and reference that commit from the
  implementation phase
- avoid claiming planned behavior in `GENIA_STATE.md` or public docs before it
  is implemented and verified

## Dependencies and gate

- R4 lifecycle vocabulary/support: complete and preserved
- R8 server execution mode: complete and preserved
- R9 Templates/representations: complete and reused
- R10 configuration/protected values: complete and authoritative
- R13 configuration-resolution ergonomics: complete and reused
- existing Flow/Seq semantics: implemented in the Python reference host and
  preserved by R14
- R11/R12: complete but not semantic dependencies of the lifecycle core

**GO for E14-5 preflight only**, now that #621, #692, #693, and #694 have
each completed their own preflight, design, failing-test, implementation,
and documentation phases: #621 implemented the instance/scope core, #692
proved horizontal peer-attachment breadth over it, #693 implemented
`lifecycle_repeat` over both, and #694 implemented `lifecycle_config` as a
pure factory requiring no change to any of the three, all against the
contract in `docs/design/r14-composable-lifecycle-contract.md`.
Implementation of E14-5 and later tickets remains blocked until each
completes its own preflight, design, failing-test, implementation,
documentation, and audit phases. The supplied `GENIA-PRE-FLIGHT.txt` is an
older template and must not replace the repository's current process
prompt.

## Exit criterion

R14 is complete only when tested Genia programs can use one coherent lifecycle
model to:

1. execute parent/child scopes with contained failure and correct ownership;
2. attach multiple peers to one scope with deterministic enter/unwind behavior;
3. repeat fresh element scopes over eager and lazy pipelines without context
   leakage or over-pulling;
4. bind an explicit immutable provider without ambient lookup or weakening R10;
5. perform protected/configured outbound HTTP as a request child while the R8
   server remains healthy;
6. demonstrate the record and Bible-proxy proving applications without AWK
   syntax, external-network CI, or real credentials; and
7. publish truthful release documentation after cross-mode hardening and a
   final audit.
