# R25 E25-0 Contract and Evidence Skeptical Audit

Status: **PASS after repair.** Audit of issue #1001 only; this is not an R25
release-completion verdict and claims no C++ Ref, Cell, or Process support.

## Scope audited

- portable Ref/Cell/local Process contract and Actor/R38 boundary
- `refs` / `cell_primitives` / `process_primitives` applicability
- R16 `r25_concurrency` fixture design and implementation
- Python reference-host in-process and external-host evidence
- current-state documentation through E25-0

## Falsification checks

### R16 duplication

No second runner, operation, protocol version, outcome taxonomy, evidence
format, registry, profile, semantic manifest, or Core IR node was added. The
only extension is one permitted fixture value forwarded in the existing v1
`eval.input` mapping after normal `requires:` applicability.

### Timing dependence

The six R25 cases contain no sleep, clock read, poll interval, duration
assertion, thread identifier, or thread-count assertion. The fixture waits on
condition predicates over causally accepted/completed work. The adapter timeout
remains only the existing crash/hang classification boundary.

### Missed work and nested sends

The fixture snapshots weakly registered live Cells/Processes, waits for each
accepted target, and repeats to a fixed point. A committed nested send increases
the target entity's accepted sequence and prevents early return. A failed
generation marks queued work discarded, matching the contract. Healthy Process
workers waiting for future messages count as idle rather than requiring exit.

The shared cases were repeated 30 times in aggregate with zero comparison
failure. Focused Ref/Cell/Process/R16 regression recorded 102 passing tests;
the E25-0 doc/evidence battery recorded 143 passing tests.

### Fixture privacy

`_r25_await_idle` is installed only by the dedicated fixture subprocess and is
undefined in an ordinary global environment. It has no prelude registration,
help/reference entry, syntax, Core IR, or manifest capability.

### Capability honesty

Cell received the independent `cell_primitives` gate; grouping it under `refs`
would overclaim for a Ref-only host. The blocking Ref case declares both `refs`
and `process_primitives`; nested Cell-only evidence declares only what it uses.
Python passes every new applicable case through the external-host adapter. C++
remains unsupported and no current document claims otherwise.

### Actor and later-release leakage

Actor/ActorRef, supervision, placement, distribution, events, backpressure,
mailbox capacity policy, Flow integration, HTTP/resource IO, R26, and R38
behavior are absent. The stale R24 deferred-surface sentence that grouped Actor
under R25 was corrected to reserve it for R38.

### Diagnostics and host mechanics

The contract excludes raw native exception/class/path/thread detail and keeps
locks, condition variables, worker topology, scheduling, fairness, wake latency,
and resource strategy nonsemantic. Shared evidence asserts only normalized
failure presence/status in E25-0; exact diagnostic cases remain owned by the
primitive implementation/hardening epics.

## Finding and repair

The first documentation scan found three genuine E25-0 truth-sync defects:

1. `docs/cheatsheet/core.md` had the newly inserted Ref/Process/Cell portability
   descriptions attached to the wrong headings because repeated prose was
   replaced positionally.
2. `GENIA_REPL_README.md` retained two older Python-only Ref/Process statements.
3. `capabilities.md` still cited `process_primitives` as an example with zero
   shared cases while the same branch had added those cases.

All three were repaired and the focused documentation tests rerun. No runtime
semantic defect was found.

## Verdict

**PASS.** E25-0 resolves the causal-evidence ambiguity with the smallest R16
extension, Python passes the new host-neutral evidence, Actor remains excluded,
and no document claims C++ support. E25-1 may begin after issue #1001 is merged.
