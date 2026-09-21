# External Process Execution — Implementation Design

Status: **Approved and implemented.** This document designed *how* the
approved [`execution.process` contract](execution-process-contract.md)
(merged in PR #977, commit `7df2c890`) should be implemented and tested,
and that design has since been implemented in the Python reference host
(PR #980) with the failing-test suite this design anticipated (PR #979)
now green — see `GENIA_STATE.md` section 9.40 for the authoritative
implemented contract.

This document remains the frozen design text below, preserved as the
approved implementation plan; it is not rewritten into a live status
report. A small number of implementation-detail adjustments were made
while preserving this design's observable requirements — most notably,
process ownership/cleanup uses a local, directly-managed launcher
function rather than the R14 `lifecycle_runtime.py` peer/unwind machinery
this document originally proposed reusing (§7), because a local
try/cleanup-style resource owner proved clearer for this specific
synchronous single-attempt shape; the observable guarantee ("no owned
child survives the attempt") is unchanged and is what `GENIA_STATE.md`
documents as implemented truth. Where this document's own internal API
proposals (module names, exact function signatures, the
`_bindings`/`_authorized`/`_launcher` field names) differ from the final
implementation in incidental ways, `GENIA_STATE.md` section 9.40 and the
source under `src/genia/process_*.py` are authoritative — this design
document is not re-litigated by such details, per its own §25 "Open
questions/blockers," which already flagged most of them as non-binding.

This document does not reopen any decision already settled by the contract.
Where the contract leaves a choice open (provisioning API naming, host
storage of bindings), this document proposes the smallest workable answer
for the Python reference host without promoting that answer to portable
status.

## 1. Status and scope

In scope: the internal capability/provider representation needed to
implement `execution.process(capability, request)`; symbolic executable
resolution; validation ordering; process ownership and cleanup; timeout;
bounded stdout/stderr capture; result and failure normalization; protected-
value handling; the Python reference-host module decomposition; Core IR
impact; testability/fixture design; race/deadlock analysis; security
analysis; rejected alternatives; and the next-phase plan.

Out of scope (contract-deferred, not designed here): provisioning API/
bootstrap naming, protected argv/environment sinks, user-specified
environment, cwd, child stdin, shell execution, streaming output, TTY,
signals, general cancellation, process handles, supervision, retries, remote
execution, R36 location-independent execution semantics. This document does
not silently solve any of these.

## 2. Contract reference

Baseline: [`docs/design/execution-process-contract.md`](execution-process-contract.md)
(approved, merged PR #977). Architecture record:
[`docs/architecture/external-process-execution.md`](../architecture/external-process-execution.md).
Taxonomy: [`docs/architecture/host-capability-taxonomy.md`](../architecture/host-capability-taxonomy.md).

```text
execution.process(capability, request) -> some(ProcessResult) | err(reason, context)
request = { executable: symbol, args: [string, ...], timeout_ms: integer }
ProcessResult = { exit_code: integer, stdout: bytes, stderr: bytes }
```

## 3. Architectural boundaries

Per `AGENTS.md`'s Future Execution-Realization Guardrail and
`docs/architecture/execution-realization.md`, three layers apply:

```text
logical computation        Genia source calling execution.process
execution realization      one bounded synchronous local attempt (this design)
infrastructure realization Python subprocess.Popen, OS pipes, signals — never portable
```

The fundamental rule restated: **portable semantics above the host
boundary; mechanism below it.** None of `subprocess.Popen`, `subprocess.run`,
Python threads, Python exceptions, Python file descriptors, Python signal
APIs, Python process objects, or Python PATH lookup become normative. A
future C++ host must reach the identical observable contract using unrelated
native mechanisms (e.g. `posix_spawn`/`CreateProcess`, `poll`/`IOCP`,
`waitpid`/`WaitForSingleObject`). Every design choice below is phrased as an
*observable requirement* first and a *Python reference-host mechanism*
second, and the two are kept in clearly labeled subsections.

## 4. Capability/provider model (Design Question 1)

**Runtime object.** A new opaque Python class, `GeniaProcessCapability`,
following the exact precedent already used for `GeniaModelProvider`
(`src/genia/model.py:267-285`) and `GeniaConfigProvider`
(`src/genia/values.py`, R10): `__slots__`-based, no public fields, no
`__eq__`/`__hash__` (mirroring `GeniaProtected`, `src/genia/values.py:117`,
which deliberately omits both to avoid an equality oracle). Genia source
cannot construct, copy, serialize, compare, or render it meaningfully — this
matches the contract's §3 requirement verbatim.

Internally it holds exactly three private fields:

- `_bindings: Mapping[str, ProcessTarget]` — immutable symbol → provider-
  native target mapping, built once at construction;
- `_authorized: Callable[[str], bool]` — a policy predicate consulted at
  execute time, kept as a distinct field from `_bindings` even though v1
  policy may simply be `lambda s: True`. This separation exists because the
  contract distinguishes "unbound" (`process-executable-unavailable`) from
  "bound but denied" (`process-unauthorized`) as two different failure rows;
  collapsing binding-presence and authorization into one map would make that
  distinction unrepresentable without a later reshape;
- `_launcher: ProcessLauncher` — the private adapter callable that performs
  the actual host launch/drain/timeout/cleanup attempt (§13 below). This is
  the "provider realization" half of the capability, exactly analogous to
  `GeniaModelProvider._handler` (`src/genia/model.py:267-285`).

**Who creates it.** Only privileged host-side Python code, via a private
factory (e.g. `create_process_capability(bindings, authorized, launcher)`),
never Genia source — mirroring `create_fixture_model_provider`
(`src/genia/model.py:360-365`), which itself validates its `handler`
argument and raises `TypeError` on misuse before ever handing back an opaque
value. The contract's deferred "source-level bootstrap operation" (§3) is
exactly the caller of this private factory; this document does not name or
design that bootstrap API, only the factory it will eventually call.

**How it is injected.** As the first ordinary positional argument to
`execution.process(capability, request)`, identical in shape to how
`provider` flows into `model(provider, config, credential, authority)`
(`src/genia/model.py`). Until a bootstrap API exists, the only way to obtain
one is the private factory used by Python-host tests, exactly like the R11
deterministic model fixture (`model.deterministic-fixture`,
`docs/host-interop/capabilities.md`) is "injected only for eval, error,
Flow, or CLI cases explicitly declaring `fixtures: [...]`" with "no ambient
fixture" in ordinary execution.

**Symbol → target mapping.** A plain Python `dict[str, ProcessTarget]`
frozen at construction; one dictionary lookup per call, no aliasing, no
extension search, no current-directory candidates, no PATH — matching
contract §6 exactly ("one lookup ... never tries aliases ... PATH ...
another provider").

**Authorization.** A separate predicate call, `self._authorized(symbol)`,
consulted only after the symbol resolves to a bound target. This keeps
"unavailable" (never bound) and "unauthorized" (bound, policy denies)
observably distinct per contract §6/§12, without requiring policy logic to
duplicate the bindings map.

**Capability identity/compatibility.** Not needed. Nothing in the contract
requires comparing two capabilities, serializing one, or checking version
compatibility between one capability and a request. Python object identity
is sufficient; no `identity`/`revision` field is added. (Contrast with R12's
opaque index handle, which *does* need compatibility identity because
`retrieve` pairs two independently-issued handles — no analogous pairing
exists here.)

**Unsupported reporting.** Per contract §3, "unsupported is discovered
during provisioning, not rediscovered by each call." `execution.process`
itself therefore never returns `process-unsupported` — that reason belongs
entirely to the deferred provisioning boundary. This design's `execution_process`
callable only ever sees either a valid `GeniaProcessCapability` (misuse
otherwise, per contract §4) or nothing at all; it has no unsupported path of
its own to design.

**Anti-goals honored.** No global process singleton (capability is an
explicit argument, never ambient). No ambient PATH authority (bindings are
capability-private and immutable). No DI-framework machinery (three private
fields, one private factory — the same shape as three other R10-R14
providers already in the codebase).

## 5. Symbolic executable resolution (Design Question 2)

```text
symbolic executable (Genia symbol)
        |  dict lookup in capability._bindings
        v
ProcessTarget (opaque, provider-native, never Genia-visible)
        |  capability._authorized(symbol) predicate
        v
authorized host execution target, handed to the launcher
```

- **Where the mapping lives.** Entirely inside the opaque
  `GeniaProcessCapability._bindings`, private Python state. No Genia value
  ever contains it.
- **When resolution occurs.** After all request-shape/misuse validation
  (§6) completes and after the protected-value scan (§10), and before any
  launch attempt — exactly the ordering contract §5 requires ("Validation
  occurs completely ... before resolution, declassification, launch, or any
  provider effect").
- **Unknown symbol failure.** `err("process-executable-unavailable",
  {executable})` — dict miss, one deterministic path.
- **Unavailable vs. launch-failure, disambiguated.** This is a subtlety this
  design resolves explicitly, since the contract names only "unbound
  symbol" for `process-executable-unavailable` (§6) and separately names
  "the bound target could not be started" for `process-launch-failure`
  (§12), without stating how a host should treat a *bound* target whose
  provider-native binary happens to be missing. This design's own choice —
  not a contract requirement — is to keep resolution failure strictly to
  "no binding exists for this symbol" (a pure dict-miss) and to treat a
  bound-but-non-executable target as `process-launch-failure`, discovered
  only when the launcher actually tries to start it. This keeps the two
  rows deterministic and independent of whether a given host chooses to
  probe existence separately from launching (a probe-then-launch host and a
  launch-and-fail host would otherwise disagree on which row applies for
  the same underlying condition if resolution were allowed to anticipate
  launch failures).
- **Authorization vs. availability.** Availability is a pure dict-membership
  fact; authorization is a policy decision consulted only for bound
  symbols. They are structurally different fields (§4) precisely so a host
  can express "this symbol is a known concept but this particular
  capability instance may not use it" without conflating it with "no such
  symbol exists at all."
- **Resolution occurs before child creation.** Yes — resolution (dict
  lookup + authorization check) is a pure, side-effect-free step that must
  fully succeed before the launcher is invoked at all. No partial process
  creation is attempted to "test" a symbol.
- **Safe error context.** Only the field `{executable}` — the requested
  *symbol*, which the caller already supplied and which is therefore not
  new information leaked by the host. The provider-native target string and
  any host path are never included (contract §6: "never appear in ordinary
  values, results, diagnostics, or failure contexts").

## 6. Validation ordering (Design Question 3)

Contract-required (from §5 of the contract, must hold for every conforming
host):

1. `executable` field validated (present, correct kind, valid non-empty
   symbol).
2. `args` field validated (present, correct kind, ordered list).
3. `timeout_ms` field validated (present, correct kind, in range).
4. All of the above (plus the closed-map shape check and the protected-value
   rejection, per contract §13, which explicitly says the recursive
   protected check happens "before resolution or launch") complete with
   **zero provider effects** before symbol resolution, declassification (there
   is none in v1), or launch.

Recommended implementation ordering (not independently observable — a
conforming host may validate in a different relative order among these
sub-checks as long as the contract-required constraints above hold, but this
order is straightforward to implement and test):

1. capability type check (`isinstance(capability, GeniaProcessCapability)`) —
   misuse if not, matching contract §4 ("a value that is not an opaque
   provisioned process capability is runtime misuse"); this check
   necessarily precedes everything else because there is no request to
   validate meaningfully without a capability to validate it against.
2. request shape: exactly the closed map `{executable, args, timeout_ms}`,
   no missing/extra keys.
3. `executable` kind/non-emptiness.
4. `args` list-ness, each element's string-ness, NUL-byte rejection.
5. `timeout_ms` integer-ness and `1..300000` range, boolean rejection.
6. recursive protected-value rejection over `executable` and every `args`
   element (§10 below).
7. symbol resolution: bound? → authorized? (§5).
8. host launch attempt (§8-9).

Non-observable implementation detail: whether steps 2-6 are one pass or
several, whether the closed-map check is structural (key set) before or
interleaved with per-field kind checks, and whether the protected-value scan
runs before or after the `timeout_ms` range check. The contract fixes the
relative order of `executable`/`args`/`timeout_ms` as *fields* (§5) and fixes
that protected-rejection precedes resolution/launch (§13); it does not fix
protected-rejection's position relative to `timeout_ms` validation, and this
design does not invent that ordering as observable — a test suite must not
assert on it.

## 7. Process ownership state machine (Design Question 4)

```text
validate → resolve → launch → capture → wait → cleanup → normalize → return
```

The mechanism-agnostic ownership guarantee: **no child ever escapes the
attempt.** The Python reference host achieves this by treating the launch
attempt as a single R14 lifecycle peer (`src/genia/lifecycle_runtime.py`,
`_run_scope`, lines 183-291), the same pattern `web.http_send` already uses
around its one transport attempt (`src/genia/http_client.py:139-195`,
`run_lifecycle_scope` entered at line ~190). `_run_scope`'s algorithm —
peers entered in order, work runs only if entry succeeded, and **exit runs
in reverse order over only the peers that actually entered, each exit
independently exception-guarded** (lines 205-264) — gives "cleanup always
runs for whatever partially started" for free, without inventing a new
mechanism. Concretely: `enter` = launch the child and record its handle;
`work` = drain + wait with the deadline; `exit` = ensure termination/reap +
close owned pipes, unconditionally.

Ownership per terminal case:

| Case | Child disposition on return | Notes |
|---|---|---|
| normal exit (0 or nonzero) | already exited; reaped in `exit` | `wait()` on an already-terminated child is immediate |
| launch failure | no child was ever created, or a partially-created one is killed in `exit` | e.g. `Popen()` raised before a PID exists → nothing to reap; a failure after PID assignment but before full setup → `exit` kills it |
| timeout | killed + reaped in `exit` before returning `process-timeout` | contract §8: deadline expires only once both output channels are EOF *or* cleanup forces that |
| stdout limit exceeded | killed + reaped in `exit`, partial output discarded | contract §10 |
| stderr limit exceeded | killed + reaped in `exit`, partial output discarded | contract §10 |
| simultaneous stdout/stderr overflow | whichever the draining loop observes crossing its bound first wins; child is killed either way | see §11 race analysis — this is a non-observable race, not a contract violation |
| provider failure (host API error mid-wait) | best-effort kill + reap attempted in `exit`; if that itself fails, contract §12's "cleanup details remain host-local" applies | primary reason stays `process-provider-failure` |
| unexpected host error | same as provider failure | no new reason invented |

No general process handle ever becomes Genia-visible: `GeniaProcessCapability`
never exposes the child; `ProcessResult` (contract §11) excludes PID and
process handle entirely. No supervision is introduced — the peer's `exit`
is a one-shot cleanup, not a supervisor.

## 8. Timeout design (Design Question 5)

- **When it begins.** Immediately before provider resolution (contract §8),
  i.e. the deadline clock starts right after validation succeeds and before
  the launcher is invoked at all — so a slow *resolution* (dict lookup is
  effectively instant, but a future host's resolution might not be) is
  itself covered.
- **What phase it covers.** Resolution, launch, execution, pipe draining,
  and collection — everything up to the point both output channels have
  reached end-of-stream and the child has terminated.
- **What constitutes timeout.** The deadline elapses before that "both
  streams EOF and child terminated" condition holds.
- **Cleanup before returning.** The provider must stop the owned child,
  reap/finalize all provider-owned resources, and close owned output
  channels *before* `process-timeout` is returned — no owned child may
  remain running after the call returns (contract §8). This is the same
  unconditional-exit guarantee from §7.
- **Cleanup-itself failure.** Contract §12: the primary reason stays
  `process-timeout`; any host failure encountered while cleaning up stays
  host-local and is never surfaced as a different error reason. If a host
  genuinely cannot force-terminate a child (cannot guarantee no-owned-child-
  left-running), contract §12 says plainly that such a host "is not a
  conforming implementation of this capability" — this design does not
  invent a softer fallback for that case.
- **Timeout vs. provider-failure precedence.** Not contract-specified as an
  observable race outcome; see §11.
- **Conformance-testable without wall-clock fragility.** Tests should assert
  *behavior*, not *timing precision*: (a) request a short `timeout_ms`
  (e.g. 50) against a fixture that deliberately sleeps far longer (e.g. 5s)
  and assert the result is exactly `err("process-timeout", {timeout_ms:
  50})`, never asserting the elapsed wall time beyond a generous upper bound
  (e.g. "returned within N seconds, not 5"); (b) assert that after a timeout
  result, no leaked child process remains (checked via `Popen.poll()` on the
  reference host, not via any cross-host-portable mechanism); (c) never
  assert an exact number of milliseconds elapsed. This avoids the fragile
  "millisecond-perfect scheduling" trap the contract explicitly warns
  against.

## 9. Stdout/stderr capture design (Design Question 6)

Observable requirement (host-agnostic): both streams must be drained
concurrently enough that neither can block collection of the other, each
channel independently bounded at exactly `1,048,576` bytes, complete byte-
exact capture on success, and no unbounded memory growth regardless of how
much the child actually writes.

- **Draining strategy.** The reference host reads both `stdout` and
  `stderr` pipes concurrently — via two reader threads (or, equivalently, a
  single `select`/`poll` loop cycling both file descriptors) — so that one
  stream filling its OS pipe buffer never stalls collection of the other.
  This is the same obligation the R16 host-adapter subprocess call already
  satisfies operationally via `subprocess.run(..., capture_output=True,
  timeout=...)` (`tools/spec_runner/protocol.py:226-282`), except this
  design must also enforce a *hard byte ceiling* mid-stream, which
  `subprocess.run`'s built-in buffering does not do on its own — so the
  reference-host adapter reads in bounded chunks itself rather than
  delegating fully to `subprocess.run`.
- **Byte counting.** A running counter per channel, incremented on every
  chunk read (not just totalled at EOF), checked incrementally after each
  read — never by first buffering unboundedly and checking length at the
  end.
- **Limits checked incrementally.** Yes — as soon as a channel's running
  total would exceed `1,048,576` bytes on the *next* read, that read is the
  one that trips overflow; a channel of exactly `1,048,576` bytes succeeds
  (contract §10).
- **Immediately after overflow.** Stop reading further from both channels,
  initiate the same unconditional child-kill-and-reap cleanup as timeout
  (§7-8), discard *all* partial output from both channels (not just the
  overflowing one), and return `err("process-output-limit", {limit_bytes:
  1048576})`.
- **Partial output in the error.** Never. Contract §10 is explicit; the
  normalization boundary (§12 below) must not carry buffered bytes into the
  error context under any circumstance.
- **Memory bound.** Each channel's buffer is capped at `limit_bytes + 1`
  (the one extra byte needed to detect overflow) — total worst case just
  over 2 MiB per attempt, independent of how much the child would have
  written if unbounded.
- **Host divergence allowed.** Threads vs. `select`/`poll` vs. async I/O vs.
  a native platform I/O completion mechanism are all conforming choices;
  the contract only constrains the *observations* (bounded, complete,
  non-blocking-on-the-other-stream, no truncation-without-error), not the
  drain mechanism. Nothing here is normative Python.
- **Bytes, not text.** No decoding occurs anywhere in this path; `stdout`/
  `stderr` in `ProcessResult` remain the existing opaque Bytes wrapper value
  (same family as `utf8_encode`'s output, `bytes.utf8-encode` capability),
  never implicitly UTF-8-decoded the way the shell stage does
  (`src/genia/evaluator.py:1182-1189`, `errors="replace"` — explicitly
  **not** the model to follow here).

## 10. Result normalization (Design Question 7)

Preserve: normal exit — 0 or nonzero — is always `some(ProcessResult)`;
only a failure to *attempt* execution (or a failure during the attempt) is
`err(...)`.

**Python APIs whose default behavior would violate this if used carelessly**
— explicitly flagged as forbidden in the implementation phase:

- `subprocess.run(..., check=True)` — raises `CalledProcessError` on
  nonzero exit. **Must not be used**; the reference-host launcher must use
  `check=False` (the default) or manage the child directly via `Popen` and
  read `returncode` itself.
- `subprocess.check_call` / `subprocess.check_output` — same problem by
  construction (they always raise on nonzero exit). **Must not be used.**
- Any careless `try/except CalledProcessError` re-raise path that maps a
  caught `CalledProcessError` back into `err(...)` would be *accidentally
  correct in effect but architecturally wrong* — it would depend on
  `check=True` ever being used in the first place, which this design
  forbids outright rather than relying on a catch-and-repair pattern.

`exit_code` is normalized into `0..4294967295` (contract §11); a native
termination that yields no portable normal-exit status (e.g. killed by an
unrepresentable signal on some future host) is treated as a provider
failure in this slice, not squeezed into a fabricated exit code.

## 11. Failure normalization (Design Question 8)

**Internal host failure representation.** A small closed Python dataclass,
mirroring `HttpTransportFailure(kind: str)` (`src/genia/http_transport.py:41-46`)
exactly: e.g. `ProcessTransportFailure(kind: Literal["launch", "timeout",
"output-limit", "provider"])` plus whatever *closed* extra field each kind
needs (`timeout_ms` for timeout, nothing extra for output-limit beyond the
constant, `executable` for launch). No raw exception, exception type name,
or traceback is ever stored in it — the launcher's boundary function catches
`Exception` once (mirroring `http_transport.py`'s `send_http_request`,
lines 96-108: "exactly one synchronous ... attempt" wrapped in a single
`try/except Exception`) and classifies immediately, the same shape as
`http_transport.py`'s `_classify(exc)` (lines 79-93) mapping specific
exception types to a closed kind set.

**Normalization location.** One boundary function in the composition module
(`process_execution.py`, §13), analogous to `http_client.py`'s
`_failure_reason(kind, timeout_ms)` (lines 120-123), which maps the
transport-layer closed `kind` into the Genia-level `(reason_string,
context_map)` pair from contract §12's table. This is the *only* place a
`ProcessTransportFailure` becomes a Genia `err(...)` value.

**Allowed error context.** Exactly the closed fields contract §12
enumerates per row (`capability`, `operation`, `executable`, `timeout_ms`,
`limit_bytes`) — nothing else, ever.

**Prohibited leakage.** Raw exception text, native error numbers, native
paths, command echoes, stack traces, PIDs, partial output, provider
identity — all explicitly named in contract §12, all excluded by
construction because the boundary function only ever sees the closed
`ProcessTransportFailure.kind` plus the caller-supplied `executable`/
`timeout_ms`, never the original exception object.

**Precedence when multiple conditions occur.** The contract does not define
an observable race outcome between timeout and output-limit conditions that
become true "at the same time" from the host's perspective (see §11 of
this document's race analysis below for the mechanism). This design does
not invent a contract-level precedence rule; it documents, as a
*Python-reference-host implementation choice*, that whichever condition the
single drain-and-wait loop detects first (an incremental byte-limit check
happening on every read, a deadline check happening on every loop
iteration) is authoritative, and the other condition is simply never
observed for that call. This is consistent with contract §15's allowance
that "cleanup mechanisms ... may differ only because the explicitly
supplied capability differs" is about mechanism, and with there being no
contract text requiring one condition to always take precedence over the
other — if a future contract revision wants a fixed precedence, that is a
contract change, not something this design should decide silently.

**Unrepresentable host conditions.** If the Python reference host encounters
a native condition that does not cleanly fit any of the seven rows (e.g. a
platform-specific spawn restriction with no obvious taxonomy slot), the
correct move is `process-provider-failure` (the explicit "not covered
above" catch-all, contract §12) — never a new eighth reason. If, during
implementation, a real condition is found that *cannot* be faithfully
represented even by `process-provider-failure` without losing meaning
needed for the contract's guarantees, that is a contract problem to escalate
for human review, not something to solve by broadening the taxonomy here.

## 12. Protected-value handling (Design Question 9)

Reuse, do not reinvent: `src/genia/configuration.py`'s existing
`contains_protected(value, _seen=None) -> bool` (lines 422-458) and
`reject_protected(value, operation: str) -> None` (lines 461-463) already
implement exactly the recursive-walk-with-cycle-guard machinery the R10
contract requires, and are already reused directly (not reimplemented) by
`host_bridge.py`, `retrieval.py`, `sheet.py`, `model.py`, and `builtins.py`.
`execution.process` should call `reject_protected(request_value,
"execution.process")` the same way, over the full closed `request` map
(covering `executable` and every element of `args` recursively — contract
§13's "Recursive request validation rejects a `GeniaProtected` leaf before
resolution or launch"), before symbol resolution or launch (§6 step 6).

`reject_protected` already raises `TypeError` carrying only the `operation`
label string, never the payload — matching contract §13's "no point at
which a protected value is revealed" and this document's own
non-leak requirement. No parallel taint/protection logic is introduced;
`GeniaProcessCapability` and its private `ProcessTarget`/`ProcessLauncher`
never see or need to see `GeniaProtected` at all, because rejection happens
strictly before resolution.

Because this is *rejection*, not a sink, there is nothing analogous to
`web.http_send`'s one-time `declassify(authority, value)` call
(`src/genia/http_client.py`'s `_resolve_headers`, lines 81-95): v1 has no
authority argument and no declassification point, exactly per contract §13.
Diagnostics, debug output, exception messages, normalized error context, and
logs never see the payload because the recursive check runs before any of
those paths could observe it.

## 13. Python reference-host decomposition

```text
Genia-visible ordinary callable    execution_process(capability, request)   -- new builtin
        |
portable validation/normalization   perform_process_execution(...)         -- new: src/genia/process_execution.py
        |
opaque execution capability         GeniaProcessCapability                 -- new: src/genia/process_capability.py
        |
Python host execution adapter       launch_process(...) -> Result|Failure  -- new: src/genia/process_transport.py
        |
OS process primitive                subprocess.Popen (check=False) + pipes -- bottom layer, never normative
```

**New files (proposed, subject to normal implementation-phase judgment):**

- `src/genia/process_capability.py` — `GeniaProcessCapability`, `ProcessTarget`
  (private target descriptor), and the private construction factory. Mirrors
  the shape of `GeniaModelProvider` in `src/genia/model.py`.
- `src/genia/process_transport.py` — the Python-host adapter: `Popen`-based
  launch, concurrent bounded drain, deadline enforcement, kill+reap
  cleanup, and the `ProcessTransportResult`/`ProcessTransportFailure`
  closed dataclasses. Mirrors `src/genia/http_transport.py` exactly in
  spirit ("one narrow Python-host capability", "no Genia-visible surface of
  its own", "normalized ... kind ... never the underlying exception's
  message").
- `src/genia/process_execution.py` — validation ordering (§6), the
  `reject_protected` call (§12), symbol resolution (§5), the R14-lifecycle-
  scoped composition of capability + transport (§7), and the failure-to-
  Outcome normalization boundary (§11). Mirrors `src/genia/http_client.py`.

**Existing files to modify:**

- `src/genia/builtins.py` — register `execution_process` (or however the
  final namespaced call dispatches; the exact `import execution` / module
  resolution mechanics used by `web`/`res` need confirming against
  `src/genia/evaluator.py`'s import machinery at implementation time — this
  is a mechanical detail, not a design decision, and is listed as an open
  item in §22).

**Public vs. private.** Only the `execution.process` callable itself (and
whatever namespace form the deferred bootstrap eventually exposes for
*obtaining* a capability) is Genia-visible. `GeniaProcessCapability`,
`ProcessTarget`, `ProcessLauncher`, `ProcessTransportResult`,
`ProcessTransportFailure`, and the private construction factory are all
Python-internal, unreachable from Genia source, exactly like
`GeniaModelProvider`, `HttpTransportRequest/Response/Failure`, and
`GeniaConfigProvider` today.

No unnecessary layer is added merely to match the diagram: three new files
is the same count R14's HTTP slice used (`http_operation.py` equivalent
folded into `process_capability.py`'s target descriptor, since there is no
separate inert-value-construction step comparable to `HttpOperation` here —
the request map itself is already the closed inert value, validated inline).

## 14. R16 integration

No second capability registry is created. Per the existing mechanism
(`spec/manifest.json`'s `required_capabilities`/`optional_capabilities`
arrays, read at runtime by `tools/spec_runner/capabilities.py::known_capabilities()`,
which has no capability-specific code of its own — adding a name is a
manifest-only change plus documentation), the future implementation phase
must:

1. add `execution.process` (or the exact registered name chosen then) to
   `spec/manifest.json`'s `optional_capabilities`;
2. add a formal entry to `docs/host-interop/capabilities.md` (name,
   `genia_surface`, input/output, errors, portability — `Python-host-only`
   for the first host);
3. add a row to `docs/host-interop/HOST_CAPABILITY_MATRIX.md`;
4. have the Python adapter's `capabilities` protocol response
   (`hosts/python/protocol_adapter.py`) advertise `supported` once actually
   implemented.

**This design does not perform any of the four steps above now** — contract
§0 explicitly states the contract itself "adds no ... capability-registry
entry," and this document, being design-phase, does the same. A host that
has not implemented `execution.process` continues to correctly declare it
`unsupported` via the existing R16 `supported`/`partial`/`unsupported`
vocabulary; `execution.process` being optional means such a host remains
conforming (contract §3). Shared spec cases exercising this capability must
declare `requires: [execution.process]` (or whatever the registered name
becomes) so `tools/spec_runner`'s existing `--host` applicability logic
(`case_is_applicable`, `tools/spec_runner/capabilities.py:61-77`) reports
`UNSUPPORTED` rather than silently skipping or falsely passing on a host
that hasn't implemented it.

## 15. R35/R36/R37 boundaries

Per `docs/strategy/roadmap/r35-r37.md` (Planned, non-authoritative,
`GENIA_STATE.md` remains final authority):

- **R35 — Portable Storage and Resource Semantics.** Not started; no
  `docs/design/r35-*.md` exists yet. Relevant here only because it will
  eventually inform the deferred `cwd`/working-location question this
  design explicitly does not touch (§4/§16 of the contract).
- **R36 — Location-Independent Genia Execution.** Not started. Its own
  roadmap text states it "builds on R14 lifecycle ownership, R16 host
  protocol/capability/revision lessons, R18 identity/opaque equality, and
  R35 storage authority" and plans "one local execution provider as the
  first vertical proof." The hard boundary this design preserves:
  `execution.process` is one bounded, explicit-capability, synchronous
  local execution attempt; R36 concerns *where Genia computation itself is
  placed and realized* (potentially remote/distributed), independent of
  physical location. R36 may *later* implement one of its execution
  providers on top of `execution.process` as a mechanism, but
  `execution.process` is not thereby redefined as remote execution, actor
  spawning, job scheduling, container orchestration, worker placement, SSH,
  or cloud execution — none of those appear anywhere in this design.
- **R37 — Genia-Native Conformance Tooling.** Not started; its own roadmap
  text (`docs/strategy/roadmap/r35-r37.md`) states it "depends on R18, R35,
  and R36" for the *full migration*, but also explicitly frames
  `execution.process` as the immediately relevant primitive: "invoke host
  adapters through approved execution boundaries rather than ad hoc
  host-local subprocess APIs: collected `execution.process` is the concrete
  direct-execution need, while R36 remains the broader location-independent
  Genia-execution abstraction." §16 below expands on what R37 should
  eventually be able to do with this capability; this design does not
  implement, migrate, or specialize anything for R37 now, and confirms — by
  direct search of `docs/design/r16-multi-host-conformance-infrastructure-contract.md`
  — that no R16 contract text currently anticipates this integration
  either; the connection exists only in roadmap/architecture prose today,
  which this design treats as aspirational context, not evidence of an
  already-approved integration.

No portable working-location, remote-execution, or R37-specific field is
added to the `execution.process` request or result anywhere in this design.

## 16. R37 relationship in detail

The likely conceptual path, restated from the task and cross-checked
against the current R16 subprocess mechanism (`tools/spec_runner/protocol.py::run_adapter_request`,
lines 226-282, which already does "spawn via structured argv, wait with a
timeout, capture stdout/stderr, classify timeout vs. crash" from the
*Python tooling side*, today, outside Genia):

```text
Genia-native conformance runner (future R37)
        |  execution.process(capability, {executable, args, timeout_ms})
        v
configured host adapter executable (the process a would-be conformance run invokes)
        |
R16 subprocess protocol (unchanged; the adapter's own stdin/stdout envelope contract)
```

This design demonstrates the primitive is *sufficient* for that path
without specializing anything toward it: `execution.process`'s bounded
argv/timeout/dual-1MiB-output shape is already structurally identical to
what `run_adapter_request` does today in Python tooling — a future
Genia-native runner would provision a capability binding a symbol (e.g.
`quote(candidate_host)`) to one R16 adapter command, then call
`execution.process` once per adapter invocation, parsing the returned
`ProcessResult.stdout` as the existing protocol-v1 envelope exactly as
`validate_envelope` does today (`tools/spec_runner/protocol.py`, lines
271-275). No R37-specific behavior is added to `execution.process`; if a
future R37 needs something this contract doesn't provide (e.g. streaming
large eval outputs past 1 MiB), that is a future extension-seam problem
(contract §17), not something to solve now by widening this contract.

## 17. R35 boundary in detail

The `executable` symbol resolves to a `ProcessTarget` that is entirely
private provider state (§5); whatever native OS path a provisioner uses to
realize that target is never exposed as a portable OS path, a portable cwd
assumption, or a portable filesystem-lookup guarantee. `ProcessTarget` is
not, and must not become, an R35 `Location`/`Store` value — R35 has not
defined those concepts yet, and coupling this design to them now would
create a forward dependency the contract does not require (contract §9:
"Portable cwd remains deferred pending R35"). If R35 later defines portable
working-location semantics, that would be a *new, separately contracted*
extension to the request shape (contract §17), not a retrofit of this
design.

## 18. Core IR analysis

**No new Core IR is required.** This matches contract §15's explicit
statement ("requires no parser, AST, lowering, evaluator special form, Core
IR, Flow, Seq, or pattern change... adds none of `IrProcess`,
`IrSpawnExternal`, `IrHostCall`, a shell AST, or provider-specific IR") and
is independently confirmed by this design's own decomposition: every
comparable host-backed capability already implemented in this codebase
(`model/4`, `config_provider`, `lifecycle_config`, `web.http_send`) is an
*ordinary call* over an *opaque host value*, normalized to an *existing
Outcome* — none of them required a new IR node, and `execution.process`
follows the identical shape. There is no architecture blocker here; this
conclusion does not require STOPping for human review.

## 19. Testability/fixture design

(Test *layers* are identified here for the next phase; no test file is
written in this design phase.)

**Pure/unit tests** (no subprocess involved): closed-map/misuse validation
for each field in isolation; `timeout_ms` boundary values (`0`, `1`,
`300000`, `300001`, negative, boolean `True`/`False` even on a host where
booleans subtype integers); capability-type mismatch (`TypeError` on a
non-`GeniaProcessCapability` first argument); symbolic resolution
unbound-vs-unauthorized distinction using a fixture capability built with
the private factory; error-context field-set exactness per taxonomy row;
recursive protected-value rejection for a protected `executable`, a
protected element buried in `args`, and a protected value nested inside a
non-protected structure the request otherwise wouldn't normally contain
(defense-in-depth, since the closed request shape already limits nesting,
but the recursive check must still not assume shape).

**Deterministic host-adapter tests** (Python-host only, using controlled
child fixtures, §20): exit 0; exit nonzero (e.g. 1, 137-range values,
confirming `exit_code` normalization); exact stdout byte sequences
including non-UTF-8 bytes; exact stderr byte sequences including non-UTF-8
bytes; simultaneous stdout+stderr writes (interleaved, to exercise
concurrent draining); timeout (child sleeps past `timeout_ms`, verify no
leaked child afterward); stdout overflow (writes `limit_bytes + 1` bytes,
verify discard + `process-output-limit` + no leaked child); stderr overflow
(same); launch failure (capability bound to a genuinely non-executable
target).

**Shared semantic/conformance cases.** Any case exercising observable
contract behavior (validation ordering results, nonzero-exit-is-`some`,
closed failure taxonomy, protected-value rejection) belongs in
`spec/` with `requires: [execution.process]` so `tools/spec_runner`'s
existing applicability logic reports it `UNSUPPORTED` rather than skipped
or falsely passed on any host — including the Python reference host until
implementation lands. **Prerequisite gap, stated plainly rather than
faked:** genuinely portable conformance evidence needs each future host to
supply its *own* equivalent deterministic child-fixture mechanism; nothing
in this repo can fabricate cross-host evidence for a host that doesn't
exist yet (only `m0smith/genia-cpp`'s narrow R24 slice exists as a second
host today, and it does not yet implement this capability). Shared cases in
this phase can only accumulate real evidence against the Python reference
host; this is recorded as a known prerequisite for genuine multi-host
conformance, not solved here.

**Security/non-leak tests.** A protected sentinel value placed in
`executable`/`args` never appears in any raised `TypeError` message, any
normalized error context, or (trivially, since the call never launches) any
captured output. A raw Python exception's message/type name never appears
in a normalized `err(...)` context (assert by checking context key sets
match exactly the closed per-row shape in contract §12). A host path/native
target string never appears anywhere in a success or failure result. A host
that reports `execution.process` unsupported must not silently behave as if
it passed a `requires: [execution.process]` case — this is an existing R16
behavior (`case_is_applicable`) to be exercised, not re-invented.

## 20. Fixture design

Distinguish, per the task's own instruction, two different things:

- **Python test fixture implementation** (host-specific, test-only, not
  part of the portable contract): tiny, deterministic child programs
  invoked via `sys.executable -c "<inline script>"` or small helper scripts
  under a test fixtures directory (e.g. `tests/fixtures/process_fixtures.py`
  generating parameterized argv), each capable of: exiting with a chosen
  code; writing an exact byte sequence to stdout; writing an exact byte
  sequence to stderr; writing to both; writing more than `1,048,576` bytes
  to one stream; sleeping past a given duration; or (for launch-failure)
  simply not existing as a target, bound deliberately to a bogus path by
  the test's private capability factory call.
- **Portable conformance fixture concept** (not defined by this design):
  the *abstract* notion that a future host needs some equivalent way to
  produce controlled child behavior for shared conformance cases. This
  design explicitly does not invent that mechanism for other hosts — doing
  so would exceed a design document's scope and risks inventing
  cross-host infrastructure ahead of need. It is named here only so the
  prerequisite gap from §19 is visible rather than silently assumed away.

Python is not made part of the portable semantic contract by any of this —
the fixtures exist purely to drive the Python reference-host adapter's
tests.

## 21. Race/deadlock analysis (skeptical)

| Scenario | Analysis |
|---|---|
| stdout fills while stderr unread | Deadlock risk if reading is sequential (block on stdout while child blocks on a full stderr pipe buffer). Avoided by concurrent draining (§9) — both streams are read on independent schedules (threads or a shared poll loop) so neither read can starve the other. |
| stderr fills while stdout unread | Symmetric to above; same mitigation. |
| output limit reached while child continues writing | Once the incrementally-checked counter trips, the reader stops reading from that channel and the child is killed (§7/§9); the child's further writes either block on a full OS pipe buffer or are discarded once killed — no deadlock, because nothing waits for the child to stop writing on its own. |
| timeout while output is being captured | The drain loop's deadline check runs on the same cadence as the reads (bounded-wait `select`/`poll` or a periodically-checked thread), so a hung child cannot cause an unbounded wait; kill+reap fires as soon as the deadline check trips. |
| child exits while cleanup starts | `wait()`/reap on an already-terminated child returns immediately; cleanup is written to be idempotent regardless of whether the child had already exited by the time cleanup runs. |
| cleanup failure | Primary reason (timeout/output-limit/etc.) stays authoritative per contract §12; a host that cannot guarantee cleanup is, per the contract's own words, non-conforming — flagged as an implementation risk to verify on the actual target platform (Linux, via `SIGKILL` + `waitpid`, which is achievable), not waved away. |
| process creation succeeds but stream setup fails | Normalizes to `process-launch-failure` after the launcher ensures the partially-created child is killed — fits the existing taxonomy row ("the bound target could not be started"), no new reason needed. |
| host errors during wait | Normalizes to `process-provider-failure` (the explicit catch-all) after best-effort cleanup. |
| output exactly at the limit | Succeeds — contract §10 is explicit that exactly `1,048,576` bytes on a channel is not overflow. |
| output one byte above the limit | Overflow — the very next read past the limit trips it; discard-and-`process-output-limit` (§9). |

**Deadlock/memory-safety rule stated explicitly for implementation:** never
read one output stream to EOF before starting to read the other, and never
buffer a stream unboundedly before checking its length — both reads must be
interleaved (thread-per-stream or a shared readiness-polling loop) and
checked incrementally, with each buffer hard-capped at `limit_bytes + 1`.

## 22. Security analysis

- **Command injection / shell injection.** Structurally impossible — no
  layer parses a command string or invokes a shell (`shell=True` is
  forbidden by this design; contrast the shell stage,
  `src/genia/evaluator.py:1156-1193`, which does use `shell=True` and is
  explicitly *not* reused here — see §23).
- **PATH substitution.** Impossible in the portable contract because
  resolution is a private static dict lookup (§5), never a PATH search;
  the Python adapter's launcher must invoke the resolved native target
  directly (e.g. via an absolute path or an explicit command the
  provisioner chose), not rely on `Popen`'s own ambient PATH-search
  fallback for `argv[0]`.
- **Executable spoofing.** Mitigated by bindings being provisioner-
  controlled, immutable for the capability's lifetime, and never
  Genia-writable.
- **Unauthorized executable access.** Enforced by the `_authorized`
  predicate at resolution time (§5), tested independently from the
  unbound-symbol case (§19).
- **Protected-value leakage.** Covered by §12: recursive rejection before
  any provider effect, reusing `reject_protected`, which never echoes the
  payload.
- **Diagnostic leakage.** The normalization boundary (§11) only ever
  passes closed context fields; no code path has access to a raw exception
  object once past the transport-layer boundary function.
- **Environment inheritance.** The contract deliberately supplies no
  environment field; whatever the Python reference host's launcher actually
  runs the child with is *entirely private provisioner state*, set once by
  whoever calls the private capability factory — this design does not add
  a portable environment-inheritance guarantee or control, and flags
  clearly that the reference host's default private environment content is
  an implementation/test decision each provisioning call makes for itself,
  not a portable behavior Genia programs can observe or rely on.
- **cwd implications.** Same treatment — private, provisioner-fixed, not
  Genia-observable or configurable in v1 (§17).
- **Resource exhaustion.** Bounded by the fixed 1 MiB-per-channel captures
  and the `1..300000` ms timeout ceiling; this design adds no further
  process-count or CPU/memory throttling — that remains outside this
  contract's scope, same as any other host-level resource limit.
- **Child escape (orphaned processes).** The single highest-risk guarantee
  in this design is "no owned child left running," delivered via the R14
  lifecycle peer's unconditional reversed-order exit (§7). This should be
  directly tested (assert no live child remains after every failure path,
  not just the happy path) rather than assumed from the mechanism alone.
- **Output amplification.** Bounded strictly by the two independent 1 MiB
  caps; no shell expansion or globbing exists to amplify a small input into
  a large command.

User-specified environment and cwd remain deferred per the contract; this
design does not silently add environment or cwd controls to address any of
the above — where host-private state exists (environment, cwd), it is
documented as implementation-private, non-portable, and not Genia-visible,
which is the correct resolution given the contract's own deferral rather
than inventing new portable controls to "solve" it now.

## 23. Rejected alternatives

- **Reusing the shell-stage subprocess code
  (`src/genia/evaluator.py:1156-1193`, `_eval_shell_stage`).** Rejected
  outright: it uses `shell=True`, has no timeout, has no output-size limit,
  and raises a raw `RuntimeError` on both spawn failure and nonzero exit —
  every one of those is exactly what contract §10/§16 says
  `execution.process` must not be a portable wrapper around. Sharing code
  with it would risk entangling the new contract's careful failure taxonomy
  with the shell stage's raise-based semantics.
- **A global ambient process-capability singleton**, for programmer
  convenience. Rejected — contract §3 requires explicit provider/authority
  acquisition, and the task's own instructions explicitly call out avoiding
  a global process singleton and ambient PATH authority.
- **A general dependency-injection-style capability registry** (e.g. a
  named-lookup service locator for capabilities). Rejected — mirrors
  exactly what the task instructs to avoid, and every existing analogous
  capability (`GeniaModelProvider`, `GeniaConfigProvider`, HTTP transport)
  already gets by with a three-field opaque value and a private factory;
  no registry framework is needed.
- **Adding `cwd`/environment/stdin fields now** to simplify the Python
  adapter's implementation. Rejected — contract §9/§16 defers all three
  explicitly; adding them would be "silently solving a deferred feature,"
  which this design must not do.
- **Including a `channel` name in the output-limit error context** to make
  debugging easier. Rejected — contract §10 explicitly omits it so
  simultaneous or closely-ordered overflow on either channel cannot produce
  host-dependent classification; adding it back would reopen a decision
  §977 already settled.
- **Sharing a low-level pipe-reader utility between the shell stage and
  `execution.process`** for code reuse. Considered, then rejected/deferred:
  the shell stage's error semantics (raise on nonzero exit, no timeout) are
  fundamentally incompatible with this contract's semantics (nonzero exit
  is `some(...)`, timeout is mandatory), so any shared low-level reader
  would need careful isolation from those higher-level behaviors to avoid
  behavioral coupling; a small, fresh reader implementation for
  `execution.process` is cheaper and safer than that entanglement risk.

## 24. Implementation plan for the next phase

This design does not perform any of the following; it only scopes them for
the separately authorized next phase(s), per repository phase discipline
(`AGENTS.md` "Prompt Discipline"):

1. **Failing-test phase.** Write failing pure-validation unit tests (§19),
   failing deterministic-adapter tests against the fixtures in §20 (all
   necessarily failing since nothing is implemented), failing protected-
   value/security-non-leak tests, and at minimum one shared spec case
   skeleton declaring `requires: [execution.process]` that is expected to
   report `UNSUPPORTED` until implementation lands. No runtime code changes
   in that phase beyond test/fixture files, per this repo's own phase
   discipline (design and implementation must not mix).
2. **Implementation phase.** Create `process_capability.py`,
   `process_transport.py`, `process_execution.py`; register the builtin;
   make the failing tests pass; reference the failing-test commit SHA per
   `AGENTS.md`'s workflow rule.
3. **Docs phase.** Update `docs/host-interop/capabilities.md`,
   `docs/host-interop/HOST_CAPABILITY_MATRIX.md`, `spec/manifest.json`, and
   `GENIA_STATE.md` to describe the now-implemented behavior — never before
   implementation lands.
4. **Audit phase.** A skeptical release-truth audit, as every other release
   in this repository has required.

## 25. Open questions/blockers

None of the following block proceeding to the failing-test phase; they are
implementation-time details to resolve when writing code, not architecture
problems requiring human resolution now:

- The exact Genia-facing import/namespace mechanics for reaching
  `execution.process` (how a module named `execution` resolves, mirroring
  `import web`/`import resource as res`) need confirming against
  `src/genia/evaluator.py`'s import machinery during implementation; this
  is mechanical, not architectural.
- The two-part `_bindings`/`_authorized` capability representation (§4) is
  this design's proposal, not contract-mandated; an implementer could
  choose a single map of `symbol -> (target, authorized: bool)` instead
  with identical observable behavior. Either is acceptable; this design
  recommends the two-part form for future policy-layering flexibility, but
  flags it as a non-binding implementation choice.
- Timeout-vs-output-limit race precedence (§11) is deliberately left as a
  documented-not-mandated implementation choice; if this ever needs to
  become observable/portable, that requires a contract revision, not a
  silent design decision.
- Whether the Python reference host can *always* guarantee no-owned-child-
  left-running on the actual deployment platform (Linux, via `SIGKILL` +
  `waitpid`) should be verified directly during implementation; expected to
  be low-risk given POSIX signal semantics, but not yet empirically
  confirmed by this design phase.

## Portability and compatibility requirements (cross-check)

Every requirement contract §15 lists as needing host agreement (validation,
symbolic lookup semantics, exact argv boundaries, no-shell behavior,
timeout range/cleanup, byte capture/limits, result shape, Outcome
reasons/contexts, nonzero-exit treatment, protected-value rejection) is
addressed by a specific section above (§6, §5, §7, §23, §8, §9, §10, §11,
§10, §12 respectively) and none of them is left to Python-specific
mechanism where the contract requires portability.
