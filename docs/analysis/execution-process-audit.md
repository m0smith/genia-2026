# `execution.process` Skeptical Audit

Status: **PASS.** This is the audit gate for the `execution.process`
cross-cutting change sequence (contract PR #977, merged; design PR #978;
failing-test PR #979; implementation PR #980; documentation-sync PR #981 —
all four later PRs stacked and open at the time of this audit). It
re-derives, from the actual source at `audit/execution-process-v1` (parent
commit `cd07a27`, on top of implementation commit `5757f0d`/`1c4d1f0`),
whether the contract's requirements actually hold — not from PR
descriptions or prior phase reports taken on faith.

Three independent skeptical review passes were run in parallel, each
instructed to assume the change was wrong and verify every claim against
the actual contract text, source code, and test files rather than trusting
documentation:

- **Track 1** — contract traceability (24-row requirement matrix) and R16
  capability-advertisement truth.
- **Track 2** — process-launch security, ownership/timeout/cleanup, stream
  concurrency, memory bounds, byte-exactness, exit-code handling, and
  protected-value rejection ordering.
- **Track 3** — documentation truth (overclaim and under-documentation),
  scope-creep search across all deferred fields, and Core IR/portability
  reproducibility.

All three tracks independently re-derived their conclusions by reading
`docs/design/execution-process-contract.md` (the frozen approved contract),
`src/genia/process_capability.py`, `src/genia/process_transport.py`,
`src/genia/process_execution.py`, `src/genia/std/prelude/execution.genia`,
the full `tests/unit/test_execution_process_*.py` suite, and the relevant
sections of `GENIA_STATE.md`, `GENIA_RULES.md`, `GENIA_REPL_README.md`,
`README.md`, `docs/host-interop/capabilities.md`,
`docs/host-interop/HOST_CAPABILITY_MATRIX.md`,
`docs/architecture/external-process-execution.md`,
`docs/architecture/host-capability-taxonomy.md`, and
`docs/strategy/roadmap/r35-r37.md`. Test run confirmed independently by two
of the three tracks: `uv run pytest tests/unit/test_execution_process_*.py -q`
→ **115 passed**.

## 1. Contract traceability matrix

Every normative requirement in the contract was traced to an implementation
site, a test, and a documentation location. All 24 items verified
**EXACT** — no MISSING or PARTIAL row was found.

| # | Requirement | Implementation | Test evidence | Doc location | Verdict |
|---|---|---|---|---|---|
| 1 | Explicit capability, no ambient | `process_execution.py::_require_capability` raises `TypeError` on non-`GeniaProcessCapability`; no global singleton in `process_capability.py` | `test_execution_process_capability_and_validation.py` | STATE §9.40, RULES §27 | EXACT |
| 2 | Capability opacity | `GeniaProcessCapability`: `__slots__`, no `__eq__`/`__hash__`/Genia constructor, `__repr__` → `"<process-capability>"` | same file | STATE §9.40 | EXACT |
| 3 | Symbolic executable identity | `_require_executable` requires `GeniaSymbol`; resolution is a dict lookup in `_bindings`, never a path | `test_no_portable_path_search_fallback_at_resolution` | capabilities.md, STATE §9.40 | EXACT |
| 4 | Structured argv, no shell | `process_transport.py::launch_process` — `subprocess.Popen(argv, shell=False, ...)` | `test_execution_process_shell_separation.py` incl. real command-injection-marker-file proof | capabilities.md, STATE §9.40 | EXACT |
| 5 | Timeout range `1..300000` | `_require_timeout_ms` | boundary tests at 1, 300000, 300001, booleans | STATE §9.40 | EXACT |
| 6 | Independent stdout bound `1,048,576` | `_StreamDrain` (one instance per channel) | `test_execution_process_output_limits.py` | contract §10, STATE §9.40 | EXACT |
| 7 | Independent stderr bound `1,048,576` | second `_StreamDrain` instance | same file | same | EXACT |
| 8 | Byte-valued capture | `_to_process_result` wraps in `GeniaBytes`; no decode anywhere in `process_transport.py` | `test_execution_process_byte_capture.py` | STATE §9.40 | EXACT |
| 9 | Normal exit (0) → `some(...)` | `launch_process` returns `ProcessTransportResult` unconditionally on clean exit | `test_execution_process_exit_behavior.py` | STATE §9.40 | EXACT |
| 10 | Nonzero exit → `some(...)`, never `err` | same function; no `check=True`-equivalent anywhere | `test_nonzero_exit_is_still_a_successful_result_not_a_failure` (parametrized 1, 2, 17, 127, 255) + `test_nonzero_exit_does_not_raise_calledprocesserror` | STATE §9.40 | EXACT |
| 11 | Owned-child cleanup/reap | `_kill_and_reap` (`Popen.kill()` → SIGKILL on POSIX, unblockable), called on every failure path, poll-guarded and `ProcessLookupError`-safe against races | `test_execution_process_cleanup.py`, PID-liveness probe (`os.kill(pid, 0)`) across every terminal path incl. a SIGTERM-ignoring fixture | STATE §9.40 | EXACT |
| 12 | `process-unsupported` reserved, never emitted by this call | `_normalize_transport_failure` has no such branch; only 6 emittable reasons exist at this layer | `test_execution_process_itself_never_returns_process_unsupported` | contract §3/§12, STATE §9.40 | EXACT |
| 13 | `process-unauthorized` | `is_authorized` check → `GeniaOptionErr("process-unauthorized", {operation, executable})` | `test_execution_process_capability_resolution.py` | STATE §9.40 | EXACT |
| 14 | `process-executable-unavailable` | `is_bound` dict-miss path | same file | STATE §9.40 | EXACT |
| 15 | `process-launch-failure` | `launch_process` catches `OSError` from `Popen()` | `test_launch_failure_for_a_target_that_does_not_exist` | STATE §9.40 | EXACT |
| 16 | `process-timeout` | monotonic-deadline poll loop in `launch_process` | `test_execution_process_timeout.py`, incl. SIGTERM-ignoring fixture proving SIGKILL use | STATE §9.40 | EXACT |
| 17 | `process-output-limit` | incremental byte-counter overflow path, checked before append, re-checked once more after the normal-exit branch (closes the race where overflow and natural exit are detected in the same loop iteration) | `test_execution_process_output_limits.py` (exact-at-limit, one-byte-over, endless-writer) | STATE §9.40 | EXACT |
| 18 | `process-provider-failure` | catch-all in `_normalize_transport_failure`; also the negative-`exit_status` (signal-terminated, unrepresentable) path in `launch_process` | `test_execution_process_failure_normalization.py` | STATE §9.40 | EXACT |
| 19 | Protected-value rejection, recursive, before resolution/launch | `reject_protected(request, "execution.process")` called immediately after request-shape validation, strictly before symbol resolution and the launcher call — reuses R10's real `contains_protected`/`reject_protected` | `test_execution_process_protected_values.py` (executable, args element, nested-in-list, launcher-never-invoked) | contract §13, STATE §9.40 | EXACT |
| 20 | No process declassification sink | No authority argument accepted; `perform_process_execution(..., *extra)` raises `TypeError` on any extra positional argument | `test_protected_capability_authority_argument_is_not_accepted` | contract §13, STATE §9.40, capabilities.md | EXACT |
| 21 | No shell semantics | `shell=False` hardcoded; no `shlex`/`os.system`/secondary shell path anywhere in `process_transport.py` | `test_execution_process_shell_separation.py` | STATE §9.40 | EXACT |
| 22 | No portable PATH lookup | Resolution is dict-only; `launch_process` performs no PATH search of its own | `test_no_portable_path_search_fallback_at_resolution` | STATE §9.40 | EXACT |
| 23 | No new Core IR node | Direct IR walk confirms `execution.process(...)` lowers to only the existing minimal-portable node family, identical in shape to an arbitrary unrelated dotted call | `test_execution_process_core_ir_regression.py` (also cross-checks `spec/manifest.json`'s frozen node-family list so the two can't silently drift) | contract §15, STATE §9.40 | EXACT |
| 24 | No `cwd`/`env`/`stdin`-beyond-EOF/streaming/signals/cancellation/handles/supervision/retries/remote fields | Grep of all four implementation files for these keywords found only the one mandated `stdin=subprocess.DEVNULL` and explanatory comments about the excluded signal-terminated-exit case — no such field exists in `request`, `ProcessResult`, or any function signature | `test_execution_process_capability_and_validation.py` explicitly rejects `cwd` as an extra closed-map key | contract §16, STATE "Explicit limitations" | EXACT |

One nuance was raised and reconciled, not logged as a finding: the
protected-value scan (`reject_protected`) runs immediately after the
closed-map/key-set check but before the individual
`executable`/`args`/`timeout_ms` kind checks. The contract fixes field
order among `executable`/`args`/`timeout_ms` and fixes
protected-rejection-before-resolution/launch, but the design document (§6)
explicitly states the *relative* position of the protected scan against
field-kind checks is non-observable and that "a test suite must not assert
on it." No test asserts a specific precedence here, so this is consistent
with the design's own disclaimer, not drift.

## 2. Process-launch security

- `subprocess.Popen(argv, shell=False, ...)` is the only process-spawning
  call in `process_transport.py`; no `os.system`, `subprocess.run`,
  `check_call`, or `check_output` appears anywhere in the file. `argv` is
  always a Python list (`[executable, *args]`), never a joined/concatenated
  string.
- The command-injection test (`test_shell_metacharacter_argv_element_cannot_perform_command_injection`)
  genuinely calls the production `launch_process` function (no mock) with a
  `"; touch <marker> ; echo pwned"` argv element and proves both byte-exact
  echo-back and that the marker file is never created — this would
  genuinely fail under a `shell=True` (even `shlex.quote`-guarded)
  implementation.
- **PATH note (informational, not a defect):** nothing in
  `process_transport.py` prevents a provisioner from binding a symbol to a
  bare command name (e.g. `"python3"`) instead of an absolute path; if that
  happened, the OS-level `execvp`-family call `Popen` makes on POSIX would
  perform its own kernel PATH search — real behavior, but it is *not*
  performed by any Genia code, and the contract's own §6 wording ("never
  tries... PATH... a portable promise to search PATH") is about Genia-level
  resolution, which is confirmed dict-only. This is a provisioning-policy
  concern below the portable boundary by design, correctly and precisely
  described in the code's own comment and never overclaimed by any doc as
  "cannot happen at the OS level." Not a repairable defect or a blocker.

## 3. Process ownership, timeout, and cleanup

- `_kill_and_reap` (SIGKILL via `Popen.kill()`, unblockable even by a
  SIGTERM-trapping child) is called unconditionally on every path that sets
  a timeout/output-limit/provider failure, and again — harmlessly, since
  `poll()` guards it — on the late-overflow-after-natural-exit path. The
  `poll()`-then-`kill()` sequence is wrapped against the
  `ProcessLookupError` race (child exits between the check and the kill).
  `proc.wait()` is bounded (5s, retried once), never indefinite.
- The `test_no_leaked_child_after_timeout_even_when_child_ignores_sigterm`
  fixture genuinely traps and ignores SIGTERM before looping, and passes —
  a real proof that cleanup escalates strongly enough.
- Reader threads are always joined with a bounded timeout (5s) and marked
  daemon, so a stuck thread cannot hang `launch_process` or block process
  exit.
- The overflow-vs-natural-exit race is closed explicitly: after the main
  loop breaks believing the child exited cleanly, the code re-checks both
  drain threads' `overflowed` flags before ever constructing a
  `ProcessTransportResult` — a child that both overflows and exits in the
  same polling iteration cannot produce a successful result.

## 4. Stream concurrency and memory bounds

- stdout and stderr are drained by two genuinely independent
  `threading.Thread` instances, each blocking only on its own pipe; nothing
  in the polling loop makes one wait on the other. The concurrent-stream
  tests use payloads sized past a typical 64 KiB OS pipe buffer specifically
  to make a naive sequential-drain implementation deadlock/hang (bounded by
  a 15s wall-clock kill in the test helper) — a real proof, not a
  tautology.
- Overflow detection happens strictly before the crossing chunk is
  appended to the buffer, so per-channel buffer content never exceeds the
  1,048,576-byte limit at the moment of detection; the discarded
  overflow-triggering chunk is not retained. Computed worst-case retained
  memory across both channels: exactly `2 × 1,048,576 = 2,097,152` bytes,
  matching the contract's own stated combined bound, plus transient
  (non-accumulating) per-iteration chunk allocations of at most 65,536
  bytes.
- The endless-writer test (`write_forever`, a genuine infinite loop with no
  self-termination) can only pass via `launch_process` itself detecting the
  overflow and returning — the test's own 60s outer bound would surface as
  a test *failure* (`AssertionError`), not a passing `output-limit` result,
  if the implementation ever fell back to "read until EOF." This confirms
  incremental checking is real, not incidentally satisfied.

## 5. Bytes and exit-code handling

- Grep for `.decode`, `universal_newlines`, `text=True`, `encoding=` across
  `process_transport.py` and `process_execution.py`: zero matches. `Popen`
  is constructed with default binary mode; `_StreamDrain.buffer` is a
  `bytearray`; results are wrapped as `GeniaBytes`.
- No code path checks `exit_status != 0`; the only check is
  `exit_status < 0` (signal-terminated, normalized to
  `process-provider-failure` per contract §11, since this slice defines no
  signal identity to expose).

## 6. Protected values

- `reject_protected(request, "execution.process")` runs immediately after
  request-shape validation and strictly before symbol resolution
  (`is_bound`/`is_authorized`) and the launcher call — confirmed by direct
  code reading, not test inference alone.
- `reject_protected`'s raised message (`src/genia/configuration.py`) is
  exactly `"protected-value: <operation>"` — a fixed literal plus the
  caller-supplied label, never the protected payload or a representation
  of it.

## 7. Documentation truth

All fourteen overclaim/under-documentation checks came back clean:

- No doc anywhere claims C++ or any non-Python host implements this
  capability; `docs/architecture/external-process-execution.md` explicitly
  states `m0smith/genia-cpp`/R24 does not.
- The portable-contract / Python-implementation / multi-host-conformance
  distinction is stated explicitly and consistently across
  `docs/host-interop/capabilities.md`, `GENIA_STATE.md` §9.40, and
  `docs/architecture/host-capability-taxonomy.md` — none of the three ever
  blur it.
- No fake Genia-facing capability constructor exists in any doc or example;
  every substantive description states plainly that no such constructor
  exists.
- PATH lookup, shell parsing, text decoding, and "nonzero exit is failure"
  are all explicitly and correctly denied everywhere they could plausibly
  be implied.
- Every substantive description of the capability states both independent
  1,048,576-byte bounds and the `1..300000`ms timeout range; brief
  cross-reference mentions correctly omit detail and point back to
  `GENIA_STATE.md` §9.40 instead of repeating it.
- No doc implies protected/secret values can currently be passed safely to
  a child process; all explicitly state no sink/authority exists in v1.
- `_execution_process` (the private raw builtin) is mentioned only as an
  internal implementation detail alongside its public `execution.process`
  wrapper — never presented as public API on its own.
- No new Core IR is claimed anywhere; R36/R37 are explicitly and
  consistently described as unimplemented, not started, and not implied to
  be advanced by this change.
- The frozen contract and design documents' numbered bodies remain intact
  aside from their status headers — direct reading confirms present-tense
  requirement/design language throughout, not retrofitted "here is what we
  built" narration.
- Every "Resolved by the approved v1 contract" claim added to
  `docs/architecture/external-process-execution.md` during the
  documentation-sync phase (protected values, lifecycle/cancellation, shell
  execution) was independently cross-checked against the actual contract
  text and implementation and found true in each case.

## 8. Scope-creep search

Grep of all four implementation files for `cwd`, `env=`, `stdin=`,
`signal`, `cancel`, `retry`, `handle` found only the one mandated
`stdin=subprocess.DEVNULL` and comments describing the excluded
signal-terminated-exit case. `GeniaProcessCapability` has exactly three
private slots. No cwd, environment, cancellation/retry API, exposed process
handle, or supervision mechanism exists anywhere in the four files, and
`GENIA_STATE.md`/`GENIA_RULES.md` enumerate the same deferred list, matching
the code exactly.

## 9. Core IR and portability

- `grep -n "IrProcess\|IrSpawn\|IrHostCall" src/genia/ir.py` — no matches.
- `test_execution_process_core_ir_regression.py`'s three tests are genuine
  structural assertions over actual lowering output (not vacuous): they
  parse and lower real `execution.process(...)` source, walk the resulting
  IR tree reflectively, assert the node-type set is a subset of the frozen
  minimal-portable allowlist and disjoint from a forbidden speculative set,
  compare against an arbitrary unrelated dotted call for identical
  IR-shape, and cross-check the allowlist against `spec/manifest.json` so
  the two cannot silently drift apart.
- `process_transport.py` relies on no CPython-specific runtime property for
  any safety guarantee: the two drain threads never share mutable state
  with each other (each writes only its own private buffer/flag), cleanup
  uses ordinary process-kill/wait semantics, and all exceptions are
  normalized to a closed `kind` string before ever reaching a Genia value —
  no Python exception identity or message is part of the observable
  contract. A hypothetical C++ host could reproduce every observable
  behavior with native threads/mutexes, `posix_spawn`/`CreateProcess`, and
  `poll`/IOCP.

## 10. R16 capability-advertisement truth

Independently re-derived from code, not trusted from documentation:

1. `hosts/python/protocol_adapter.py::_python_claimed_capabilities()`
   reads `tools/spec_runner/capabilities.py::known_capabilities()` (the
   union of `spec/manifest.json`'s `required_capabilities` +
   `optional_capabilities`) and self-declares every name `supported`
   except those in `_PARTIAL_CAPABILITIES` (currently only
   `shared_spec_runner`). `execution_process` is in `optional_capabilities`
   and not partial, so it is self-declared `supported`. Confirmed by direct
   trace.
2. `grep -rn "requires:.*execution_process"` across `spec/` and `tests/`:
   zero matches. No shared-spec case exercises this capability yet.
3. The documentation's claimed precedent — that `shell_stage`,
   `debugger_stdio`, and `process_primitives` are already registered this
   same self-declared, zero-shared-spec-coverage way — was independently
   verified true (zero `requires:` references to any of the three anywhere
   under `spec/`), not merely asserted.
4. `case_is_applicable`/`validate_capability_claims` only check that
   claimed names are in the known vocabulary and gate purely on string
   equality against a case's own `requires:` list; there is no independent
   verification anywhere that a self-declared "supported" claim is
   actually true beyond that gate. This means `execution_process`'s
   self-declaration currently has zero live conformance effect, since no
   case requires it.
5. `GENIA_STATE.md` §9.40 and `docs/host-interop/capabilities.md`'s entry
   both explicitly and accurately state: the capability is registered; the
   registration is a self-declaration with no independent verification
   mechanism; zero shared-spec cases currently exercise it; this is not
   cross-host conformance evidence; and this matches the pre-existing
   `shell_stage`/`debugger_stdio`/`process_primitives` pattern rather than
   being a special exception invented for this capability. No overstatement
   or understatement found in either document.

**Conclusion:** manifest registration is an existing, pre-established R16
architectural pattern (self-declared capability names with no independent
proof requirement until a shared-spec case actually requires them) — not a
new defect introduced by this change, and not overstated by its
documentation.

## 11. Known unrelated parity failure

`tests/spec/test_python_protocol_adapter_parity_762.py::test_full_shared_spec_suite_matches_in_process_path_through_subprocess_protocol`
fails on this branch with a stale pinned shared-spec count
(`total=740 passed=722` hardcoded vs. the actual `total=755 passed=737`).
This was independently reproduced in PR #979 with every `execution.process`
file removed from the branch, and reconfirmed unchanged in PR #980 and PR
#981's own validation runs. This audit reconfirms it once more below and
treats it as **pre-existing baseline debt, unrelated to and not worsened
by `execution.process`** — `unsupported=18` is unchanged across all runs
in this change sequence, confirming the `execution_process` manifest
registration did not silently flip any case's classification. No GitHub
issue for this staleness was found in this session's scope; filing one is
reasonable follow-up work but is explicitly out of scope for this audit,
per the task's own instruction not to repair it here.

## 12. Audit verdict

**PASS.**

- Contract satisfied: all 24 traceability rows EXACT, no MISSING/PARTIAL.
- Tests adequate: 115/115 passing, and the specific tests that matter
  (command-injection, SIGTERM-resistant cleanup, endless-writer,
  concurrent-stream deadlock pressure, nonzero-exit, protected-value
  non-leak) were confirmed to be real proofs, not tautologies, by direct
  code tracing.
- Implementation correctly bounded: no shell, no Genia-level PATH search,
  bounded memory, unconditional cleanup, byte-exact capture, no scope
  creep into any deferred field.
- Docs truthful: no overclaim found in fourteen independent checks; the
  portable-contract/Python-implementation/multi-host-conformance
  distinction is preserved everywhere; R16 registration is honestly
  characterized as self-declared with zero conformance evidence.
- No unresolved semantic or architectural defect found by any of the three
  independent review tracks.

No repairs were required. No repairable findings were logged in Sections
2-10 — every item traced to OK on direct inspection.
