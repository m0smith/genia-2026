# R25 Deterministic Concurrency Evidence Design

Status: **E25-0 implementation design.** This document adds no public Genia
behavior. The portable semantics are defined by
`r25-stateful-runtime-concurrency-contract.md` and `GENIA_STATE.md`.

Issue: #1001

## 1. Finding

The existing R16 `eval` operation, result comparison, `requires:` gating, and
evidence document are sufficient for R25. No new runner, operation, protocol
version, outcome class, evidence format, capability registry, or Core IR node is
needed.

One expressive gap exists in test provisioning. A one-phase program can block
on a Ref acknowledgement and therefore prove successful causal paths, but it
cannot deterministically inspect the state after an asynchronous Cell or
Process callback fails. The worker records failure only after the callback has
raised. Sleeping, deadline polling, or observing immediately after a side
effect inside the callback would introduce a scheduler race.

## 2. Smallest extension: the `r25_concurrency` fixture

Extend the existing `input.fixtures` vocabulary with `r25_concurrency` and
allow that one fixture over the generic external-host `eval` request. The
request stays protocol v1 and uses the existing optional input mapping:

```json
{
  "source": "...",
  "stdin": null,
  "argv": null,
  "fixtures": ["r25_concurrency"]
}
```

The generic runner forwards this fixture only after ordinary `requires:`
applicability succeeds. Other existing injected fixtures remain unavailable to
generic external hosts. A host that does not support the case's R25 capability
is never sent the request.

The fixture injects exactly one private, test-only callable:

```text
_r25_await_idle()
```

It is absent from the ordinary global environment, prelude, help/reference
surface, CLI, parser, Core IR, and capability vocabulary. It must never appear
in user-facing examples or implemented-surface lists.

## 3. Idle observation

Each R25 runtime entity maintains host-private causal accounting:

- accepted sequence: incremented before an asynchronous Cell update or Process
  message becomes visible to its worker;
- completed sequence: advanced after that accepted item either commits,
  is discarded by a documented generation/failure rule, or completes the
  failure transition caused by its callback;
- in-flight state: host-private state needed to distinguish an empty queue from
  a callback currently executing.

`_r25_await_idle()` snapshots every currently live R25 asynchronous entity and
its accepted sequence, then waits until each snapshot target is completed or
discarded according to the contract. If completing snapshot work commits
nested Cell/Process sends, those causally created entities/targets are included
before the fixture returns. The fixed point is reached only when no new staged
send was committed during the preceding observation and all included targets
are complete.

The fixture does not wait for a healthy Process worker to exit; a mailbox
worker blocked awaiting a future message is idle. It does not wait for unset
Refs, because Ref blocking/wakeup is evidenced directly with a causally sent
`ref_set`. It does not invent cancellation or stop any entity.

The host adapter's existing per-request timeout remains a crash/hang guard. It
is not exposed to the program, is not asserted by a case, and supplies no wake
latency or fairness guarantee. A case passes because the exact post-idle value
matches, never because completion was faster than a threshold.

## 4. Python realization

The Python reference host adds weakly held registry entries for live Cells and
Processes. Each entity's existing condition/lock protects accepted/completed/
in-flight accounting and notifies fixture waiters after terminal transitions.
The wait path uses condition predicates, not polling sleeps. Registry snapshots
must not keep otherwise unreachable entities alive after the fixture returns.

The dedicated fixture subprocess creates the normal global environment,
injects `_r25_await_idle`, evaluates the supplied source exactly once, and uses
the existing CLI-compatible stdout/stderr/exit-code projection. No fixture code
changes ordinary evaluation.

## 5. C++ realization obligation

E25-1 may implement Ref without this fixture for synchronous/set-value evidence.
The blocking Ref case also requires `process_primitives`, so it becomes
applicable when E25-3 supplies the producer; until then it remains honestly
unsupported rather than weakened.

E25-2 and E25-3 implement equivalent host-private accepted/completed
accounting as part of their worker state machines. Their adapter recognizes the
fixture only for applicable cases and installs the same private callable. The
accounting mechanism, condition-variable type, thread topology, and registry
container are not portable.

## 6. Capability decisions

- `refs` remains the Ref gate.
- `cell_primitives` is added because Cell is independently implementable and
  claimable; grouping it under `refs` would make a Ref-only host overclaim.
- `process_primitives` remains the local Process gate.
- no fixture capability is added. The fixture is evidence provisioning for
  cases already gated by the semantic capability being proved.

Cross-capability cases declare every dependency. In particular, the blocking
Ref producer case requires both `refs` and `process_primitives`; nested Cell to
Process send cases require `cell_primitives` and `process_primitives`.

## 7. Shared case plan

### Ref

- initial/read and set visibility
- unset Ref unblocked by a Process producer, exact value observed
- atomic updates from multiple Processes with a causal completion Ref
- exact return values and normalized misuse

### Cell

- FIFO serialized success and exact final state after idle
- asynchronous acceptance (a gated first update leaves pre-commit state visible)
- failure preserves last successful state and exposes failed/status/error
- later queued update is discarded after failure
- restart installs a new generation and discards stale work
- nested Cell/Process sends commit in order on success and are discarded on
  failure
- stop rejects later sends, drains accepted work, preserves readable state
- normalized misuse

### Process

- FIFO observations and one handler invocation at a time
- fail-stop alive/failed/error observations after idle
- post-failure send rejection and no queued work after failure
- normalized misuse

Cases assert exact values/stdout/stderr/exit status. They contain no sleep,
clock read, thread identifier, thread count, or timing threshold.

## 8. Validation and audit

E25-0 must prove loader rejection/acceptance, generic request forwarding,
Python adapter round-trip, fixture privacy, condition-based idle behavior,
fixed-point nested-send handling, and deterministic repeated evidence. The
skeptical audit searches specifically for polling, missed in-flight work,
registry lifetime leaks, fixture exposure, capability bypass, and any claim of
C++ support.

