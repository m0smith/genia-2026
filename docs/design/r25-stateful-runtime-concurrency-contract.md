# R25 Stateful Runtime and Concurrency Contract

Status: **Approved portable contract for E25-0.** This contract defines the
bounded Ref, Cell, and local Process observations that R25 may promote to
multi-host conformance. It does not claim that the C++ host implements them.
`GENIA_STATE.md` remains final authority for implemented behavior.

Issue: #1001

## 1. Purpose and approval boundary

R25 is explicitly approved multi-host portability infrastructure after R24.
It does not expand Genia's product surface: it promotes the already-implemented
Python reference-host Ref, Cell, and local Process observations into a small
portable contract and adds a faithful C++ realization.

The release is ordered as E25-0 contract/evidence, E25-1 Ref, E25-2 Cell,
E25-3 Process, E25-4 hardening, and E25-5 truth synchronization/audit. A host
may claim a capability only after every shared case applicable to that claim
passes through the R16 external-host protocol.

## 2. Hard boundary: Actor is excluded

R25 defines no Actor or ActorRef behavior. It adds no actor mailbox,
supervision, restart policy, placement, distribution, observability, protocol,
or Flow integration. Portable actors belong exclusively to R38. Process in
this contract is the existing local `process.*` primitive and must not become a
disguised Actor abstraction.

Also excluded are a language scheduler, async/await, events/pub-sub,
distributed messaging, mailbox capacity/backpressure policy, selective
receive, timeouts, HTTP, resource IO, Flow parity, concurrent lifecycle scopes,
and new syntax or Core IR nodes.

## 3. Common portable boundary

Ref, Cell, and Process are identity-bearing opaque runtime values exposed by
ordinary calls. Their identity/equality behavior remains the R18 behavior.
They add no Core IR node. Host thread identity, queue representation, locks,
condition variables, scheduler decisions, and allocation strategy never cross
the portable boundary.

Handles keep the referenced runtime entity valid for every operation made
through that handle. A host must prevent use-after-free while an accepted
operation is executing. The contract does not require one thread per entity,
unbounded entity creation, a particular destructor, or a portable resource
limit. A host may reject creation because of a host resource limit only through
its normalized host boundary; it must not expose native exception text or
native thread/process identifiers.

No fairness, wake-latency, wall-clock completion bound, thread count, or
inter-entity ordering is portable. Portable liveness statements below mean
that an accepted causally enabled operation is not deliberately lost; tests
bound a hung adapter only as harness safety, never as the semantic definition.

## 4. Ref contract (`refs`)

### 4.1 Surface

- `ref()` creates an unset Ref.
- `ref(value)` creates a set Ref containing the exact value.
- `ref_is_set(ref_value)` reports whether a value is currently installed.
- `ref_get(ref_value)` returns the installed value.
- `ref_set(ref_value, value)` installs and returns the exact value.
- `ref_update(ref_value, updater)` atomically replaces the installed value with
  the result of one updater invocation and returns that replacement.

### 4.2 Synchronization observations

`ref_get` and `ref_update` on an unset Ref wait until a `ref_set` installs a
value. A `ref_set` makes that value visible to every waiter. There is no
portable timeout. Operations on one Ref are serialized. Concurrent successful
updates therefore have a serial order and no successful replacement is lost.

The portable contract is the exclusive read/update/write observation, not a
particular mutex rule. The updater is invoked exactly once for an accepted
update. Re-entering the same Ref from its updater is outside the supported
contract; a program must not depend on whether a host deadlocks or rejects
that misuse. Calls on other Refs remain ordinary independent operations.

### 4.3 Misuse

The Ref argument to `ref_get`, `ref_set`, `ref_is_set`, and `ref_update` must be
a Ref. The second `ref_update` argument must be callable. Misuse raises a
normalized Genia-facing type error and performs no Ref mutation.

## 5. Cell contract (`cell_primitives`)

Cell is independently claimable from Ref. `cell_primitives` is therefore the
R25 capability gate; `refs` does not imply Cell support.

### 5.1 Surface and normal operation

- `cell(initial)` creates a ready Cell with an internal state Ref.
- `cell_with_state(state_ref)` creates a ready Cell over the supplied Ref.
- `cell_send(cell, update)` accepts an asynchronous state update.
- `cell_get(cell)` and `cell_state(cell)` return the latest committed state.
- `cell_status`, `cell_alive?`, `cell_failed?`, and `cell_error` expose the
  documented ready/stopped/failed observations.
- `cell_stop(cell)` requests graceful stop.
- `restart_cell(cell, new_state)` starts a new Cell generation.

Accepted updates are processed FIFO within one Cell, with at most one update
callable in flight for that Cell. A successful update commits its returned
state exactly once. `cell_send` returning means accepted, not completed;
`cell_get` is an observation of the latest committed state and is not a queue
barrier.

### 5.2 Failure

If an update raises, its state replacement and its staged nested Cell/Process
sends are discarded. The Cell preserves its last successfully committed state,
enters `"failed"`, caches a normalized Genia-facing error string, discards
later queued work from that generation, and rejects later `cell_send` and
`cell_get`/`cell_state`. `cell_failed?` is true and `cell_error` is
`some(error_string)`. The cached text must not expose a native exception class,
implementation path, address, thread identifier, or raw host exception text.

Nested `cell_send` and Process `send` calls made during an update are staged in
program order. They become accepted only after the enclosing update succeeds;
they are all discarded if it fails. This is a transaction boundary only for
those documented nested sends, not for arbitrary side effects such as Ref
mutation.

### 5.3 Restart and stop

`restart_cell(cell, new_state)` increments the logical generation, installs
`new_state`, clears failed/stopped/error state, discards all queued work from
older generations, and ensures a worker realization is available. Work already
executing from an older generation may finish its callable, but none of its
state or staged-send effects may commit after restart.

`cell_stop` marks the Cell stopped immediately, rejects later sends, drains
already accepted updates in the current generation, then ends its worker
realization. `cell_get` still returns the last committed state of a stopped
Cell. Repeated stop of a stopped or failed Cell is a no-op. Restart may make a
stopped Cell ready again.

### 5.4 Misuse

Cell operations require a Cell; `cell_with_state` requires a Ref; `cell_send`
requires a callable update. Misuse raises a normalized Genia-facing type error
before accepting work.

## 6. Local Process/mailbox contract (`process_primitives`)

### 6.1 Surface and ordering

`spawn(handler)` creates a local opaque Process. `send(process, message)`
accepts the exact message into that Process mailbox and returns nil. Within one
Process, accepted messages are handled FIFO and at most one handler invocation
is in flight. There is no ordering promise across Processes.

`process_alive?`, `process_failed?`, and `process_error` expose the documented
state. A healthy Process has no error. Process has no restart or graceful
shutdown surface in R25.

### 6.2 Failure

If the handler raises, that invocation causes a permanent fail-stop transition:
the normalized error is cached, the worker realization stops, queued messages
are not handled, `process_failed?` becomes true, `process_alive?` becomes false,
and `process_error` becomes `some(error_string)`. Later `send` calls raise and
do not enqueue. No raw host exception detail may cross the boundary.

Process failure is not supervision and creates no propagation, linking,
monitoring, restart, dead-letter, or retry behavior.

### 6.3 Misuse

`spawn` requires a callable handler. All other Process operations require a
Process. Misuse raises a normalized Genia-facing type error without creating or
accepting work.

## 7. Executable conformance obligation

The authoritative boundary is this contract plus `GENIA_STATE.md`; the runtime
values and ordinary calls are the representation. Shared cases use `refs`,
`cell_primitives`, and `process_primitives` in `requires:`. Python and C++ must
pass every applicable case before the matching capability is supported.

Ordinary one-phase `eval` can prove synchronous Ref behavior and successful
causal paths by blocking on explicit Ref acknowledgements. It cannot
deterministically observe the state *after* an asynchronous Cell/Process
failure: the worker records failure only after the throwing callback returns,
and the language has no join/await operation. Sleeps, polling deadlines, or
scheduler-lucky final evaluation are forbidden substitutes.

E25-0 may therefore extend the existing R16 `eval` input with one optional,
host-neutral arrange/settle/observe fixture. It must keep the same runner,
operation, capability registry, comparison, outcome taxonomy, and evidence
format. Settling means only that causally accepted R25 work preceding the
observation has reached a documented terminal/idle boundary; it adds no public
Genia function and no program-visible timing or scheduler guarantee. Hosts
without the required capability remain unsupported through normal `requires:`
gating.

## 8. Truth synchronization

E25-0 records the portable contract and Python evidence without claiming C++
support. E25-1 through E25-3 update host support only after external-host
evidence passes. E25-5 synchronizes `GENIA_STATE.md`, rules, REPL/README,
host-interop docs, capability matrix, roadmap, semantic guards where useful,
and `docs/releases/R25.md` with the exact implemented floor.

