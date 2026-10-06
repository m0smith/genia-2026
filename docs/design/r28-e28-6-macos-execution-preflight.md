# GENIA Change Pre-Flight: macOS portability of the governed `genia_run` execution profile

Status: **Pre-flight** (issue #707, epic #700, ledger R28-H47, with R28-H39 and R28-H43). This follows the R26+
gate (`docs/process/run-change.md`). `GENIA_STATE.md` remains final authority for implemented behavior.
(Historical pre-flight; R28 completed later, `GENIA_STATE.md` section 9.49.) No code in this change alters Genia syntax, semantics, the MCP surface, the A5
negotiation, the parse path, authority policy, or the output envelopes.

## Change identity

- **Change name:** make the governed worker's process limits platform-aware so `genia_run` works on macOS,
  and make the conformance test infrastructure portable
- **Release / issue:** R28 / #707 (E28-6); branch `claude/bold-euler-jb7uoy` (PR #1082)
- **Starting SHA:** `66b505949cb17a4a017291115efb8a1cc5970cab`

## Trigger: authentic run 2 (2026-10-05, macOS Darwin x64 24.6.0, VS Code 1.138.0, Copilot Chat 0.66.0)

On the A5 branch head the owner's VS Code discovered `.mcp.json`, started Genia (it stayed Running), reported
`Discovered 3 tools`, called `genia_capabilities`, rejected the broken source through `genia_parse` with
`parse_error` at offset 171, and parsed the corrected source. The amendment's goal (H36) is therefore met in
authentic VS Code. The canonical `genia_run` then returned the sanitized adapter failure
`{"kind":"internal_error","message":"Internal error while executing","phase":"adapter"}`. On the same Mac,
`uv run pytest tests/unit/test_r28_mcp_run.py` gave **53 failed, 17 passed, 3 skipped**, in two classes:

- **A. Execution failure.** Nearly every execution test (pure expression, channels, `none`, direct-parity cases,
  runtime/parse/policy/limit failures through run, fresh runtime) got `internal_error`. The set includes
  outcomes the worker decides before evaluating anything (`parse_error` and `policy_denied` sources), so the
  worker fails **before it reads the source**: during its bootstrap.
- **B. Linux-specific test infrastructure.** `Path("/proc").iterdir()` raises `FileNotFoundError` in the helper
  every lifecycle/cancellation test uses; the namespace tests read `/proc/net/dev`.

Parse is unaffected because `genia_parse` runs in the host process (a different path). Direct invocation of
`mcp_worker.py` as a script (`No module named 'hosts'`) is **not** the production failure: production runs
`python -B -m hosts.python.mcp_worker` with `PYTHONPATH` set by the supervisor (`_worker_environment`).

## What the production path does, and what can fail before the source is read

Supervisor (`RunCapability._run`): `tempfile.mkdtemp`, `Popen(..., cwd=workdir, env=<fixed>, close_fds=True,
start_new_session=True)`, `select` loop, `killpg`, reap. Worker (`main`): install runtime stubs, `apply_limits()`,
write the readiness marker, arm `SIGALRM`, read stdin. Any exception before the reply becomes the closed reply
`{"status":"internal_error"}`, which the supervisor returns unchanged: the symptom is identical for every cause.

`apply_limits()` applies five `setrlimit` calls: `RLIMIT_FSIZE=0`, `RLIMIT_CORE=0`, `RLIMIT_CPU=10`,
`RLIMIT_NOFILE=64`, `RLIMIT_AS=2 GiB`. Linux has no other platform-conditional behavior in the production path
(verified by search: `unshare` and `/proc/net/dev` appear only in the namespace probe, which is already
guarded by `sys.platform.startswith("linux")`; no `prctl`, no parent-death signal, no `preexec_fn`, no
`/proc` read).

## Evidence available and its limits (no guessing)

| Fact | Status |
|---|---|
| Every worker-decided outcome failing with `internal_error` while parse works is the signature of a bootstrap failure | observed on the Mac (run 2 and suite) |
| The same signature set is **reproduced** on Linux by making the worker's `setrlimit(RLIMIT_AS, ...)` raise (as Darwin's kernel does when the requested bound is below the process's current virtual size, which a Python process on macOS exceeds): pure expression, parse error, policy denial, runtime error all become `internal_error` | reproduced here (red test) |
| The *exact* Darwin operation that raises | **not directly observed**: there is no macOS machine in this environment |

To make the next Mac run decisive, this change adds `tools/mcp_diagnostics/worker_probe.py` and a development-only
worker diagnostic (`GENIA_MCP_WORKER_DIAG=1`, never forwarded by the supervisor, written to the worker's own
stderr, which the supervisor discards): the probe applies each limit in its own process, runs the exact
production command, prints the worker's stderr and exit status, and ends with a `VERDICT` line. The MCP wire is
unchanged: clients still receive only the sanitized error.

Working hypothesis (stated as a hypothesis): `RLIMIT_AS` is the only limit that is not portable (Darwin does
not honor an address-space bound that the process already exceeds). The other four limits are POSIX and
standard on Darwin. The fix below is correct if the hypothesis holds, and it fails closed (`internal_error`) for
every other cause, so it cannot widen authority if the hypothesis is wrong; the probe then names the true cause.

## Isolation-mechanism portability table

"Exact" means the same semantics on Linux and macOS. "Contract" is whether the R28 contract (section 4,
section 5, threat model 9) requires it by name. The contract requires fail-closed behavior ("failure at either
layer is `internal_error`; it is never permission to run broadly"), a fresh disposable worker, a fixed minimal
environment, source-only execution, a 5,000 ms deadline, byte limits, forceful kill and reap, protected-value
non-leakage, and "OS isolation where available" for the network. It does not name any rlimit, `/proc`, or
namespaces.

| Mechanism | Purpose | Linux | macOS | Equivalence | In contract? | Disposition |
|---|---|---|---|---|---|---|
| Fresh process per call | no state between calls | `Popen` | `Popen` | exact | yes | unchanged |
| Own session/process group, `killpg` | kill and reap the whole worker tree | `start_new_session`, `killpg` | same (POSIX) | exact | yes | unchanged |
| Fixed minimal environment (no `PATH`, `HOME`) | no ambient authority | `env=` | `env=` | exact | yes | unchanged |
| Private empty working directory, removed after reap | no workspace observation | `mkdtemp` | `mkdtemp` | exact | yes | unchanged |
| Only the three standard pipes inherited | no inherited descriptors | `close_fds` | `close_fds` | exact | yes | unchanged |
| Source on stdin, then EOF; empty argv; no tty | source-only, no input | pipes | pipes | exact | yes | unchanged |
| Monotonic deadline from worker readiness; `select` over pipes | hard time bound | `select`, `monotonic` | same | exact | yes | unchanged |
| Incremental channel and reply byte caps | output bounds | in worker/supervisor | same | exact | yes | unchanged |
| Static policy over the raw AST; pruned default-deny environment; runtime stubs (imports, processes, sockets) | authority denial in three layers | Python | Python | exact | yes | unchanged |
| Protected-value non-leakage | secrets never cross | Python | Python | exact | yes | unchanged |
| `RLIMIT_FSIZE=0` | no file writes even if every other layer failed | `setrlimit` | `setrlimit` (POSIX) | exact (to be confirmed by the probe) | no (defense in depth) | required on every platform; failure is `internal_error` |
| `RLIMIT_CORE=0` | no core dumps | `setrlimit` | `setrlimit` | exact | no | required; fail closed |
| `RLIMIT_CPU=10 s` | bounds a busy worker beyond the deadline | `setrlimit` | `setrlimit` | exact | no | required; fail closed |
| `RLIMIT_NOFILE=64` | bounds descriptors | `setrlimit` | `setrlimit` | exact | no | required; fail closed |
| `RLIMIT_AS=2 GiB` | bounds memory growth within the 5 s window | `setrlimit` | not usable (the limit is rejected or not enforced; hypothesis) | **unavailable** on macOS | no (the contract says only "resource bounds") | **required on Linux (fail closed); not applied on macOS, documented as a weaker bound** |
| User + network namespace (`unshare`) | OS-level network denial | verified probe, best effort | none (`unshare` does not exist) | unavailable | no ("where available") | Linux only; macOS equals "namespace unavailable", already a tested, simulated-denied configuration; network denial rests on the three Python layers |
| `sandbox-exec` / Seatbelt as a namespace substitute | OS-level file/network denial | n/a | deprecated, unverified here | unavailable | no | **not adopted**: would be a new isolation mechanism with its own threat review; not claimed |
| `SIGALRM` orphan backstop (8 s) | bounds a worker whose host died by SIGKILL | `setitimer` | `setitimer` (POSIX) | exact | no | unchanged |
| `SIGTERM`/`SIGHUP` host handlers; launcher signal forwarding | unwind and reap on shutdown | `signal` | `signal` | exact | no | unchanged |
| Parent-death signal (`prctl`) | kill worker when host dies | **not used** | n/a | n/a | no | nothing to port |
| `/proc` inspection | production | not used | n/a | n/a | no | nothing to port |
| `/proc` inspection | **tests only** | process table, cwd, fds | absent | different API | n/a | tests get a platform abstraction (`ps`, `lsof` on macOS; `/proc` kept on Linux) |

## Decision (the smallest defensible solution)

1. **macOS can meet the R28 contract.** Every invariant the contract names is implemented by portable POSIX
   mechanisms or by pure Python layers; the only non-portable pieces are Linux hardening that the contract does
   not require: the `RLIMIT_AS` memory bound and the optional network namespace.
2. **Worker change (the only production change):** `apply_limits()` applies the four portable limits on every
   platform with fail-closed behavior, and applies `RLIMIT_AS` fail-closed on every platform **except
   Darwin**, where a rejected `RLIMIT_AS` is tolerated. No other limit or error is tolerated on any platform.
   Linux behavior is byte-for-byte unchanged. There is one execution model: same worker, same envelopes.
3. **Honest weaker bound on macOS:** without `RLIMIT_AS`, a hostile program can allocate memory for up to the
   5,000 ms deadline (and 10 s CPU) before it is killed; on Linux the 2 GiB bound applies. This is documented as
   a macOS limitation; no capability or document claims an address-space bound there. A supervisor-side memory
   watchdog is a post-R28 follow-up candidate, not part of this change.
4. **No Linux hardening is faked on macOS.** No namespace, no sandbox wording, no `sandbox-exec`.
5. **Tests:** the lifecycle helpers use `/proc` on Linux (unchanged evidence) and `ps`/`lsof` on macOS; the `ps`
   backend is exercised on Linux too so its parsing is proven here. Linux-only facts (namespace network
   interfaces, `/proc/net/dev`) stay Linux-only and are explicitly marked.
6. **If the Mac probe shows a different failing operation** (for example `RLIMIT_NOFILE` or `RLIMIT_FSIZE`),
   stop: a required limit that macOS cannot apply would be a contract question, to be reported, not weakened.

## Red tests first

1. Production-signature reproduction: a worker whose `RLIMIT_AS` is rejected on a simulated Darwin must still
   complete `1 + 2`, give `policy_denied`/`parse_error`/`runtime_error` for the corresponding sources, and
   enforce `RLIMIT_FSIZE`; the same rejection on Linux, or any other limit rejected on Darwin, must be
   `internal_error`.
2. A guard against the exact regression: discovery and parse working while every run is `internal_error`.
3. The `ps`/`lsof` backend finds the governed worker, its cwd, a killed-but-unreaped zombie, and descendants on
   Linux, so the macOS code path's logic is tested before the owner runs it.

## Scope lock

No Genia syntax, builtin, Core IR, MCP tool, resource, prompt, transport, protocol, authority, limit, or envelope
change. No second execution model. No sandbox claim. Python host code changes only in `mcp_worker.py` (limit
application and a development diagnostic that cannot reach the wire). Documentation changes only to state
platform facts.

## Verification plan

Linux: full R28 suite granted and denied, compat suite, authority/protected/timeout/cancel/lifecycle, the
non-loopback and loopback suites, spec runner, parity, official client (all paths), Inspector, lint/docs/gate.
macOS (owner): the probe, `tests/unit/test_r28_mcp_run.py`, the lifecycle suite, then authentic VS Code run 3.

## Addendum: Mac verification of `48467fcd` (owner)

The probe printed `VERDICT OK`; Darwin rejects `setrlimit(RLIMIT_AS, ...)` with `ValueError: current limit exceeds maximum limit`
(the hypothesis is now **confirmed**, and the decision above stands); supervised `1 + 2` returned `3`;
`test_r28_mcp_run.py` gave 64 passed, 5 failed, 4 skipped. The five failures are one test-observation
sub-finding: the `ps` backend never saw the governed worker. Repaired without weakening any lifecycle assertion
(case-insensitive interpreter name for macOS's `Python.app`; `ps -ww` against terminal-width truncation) and
diagnosable with `tools/mcp_diagnostics/process_probe.py`. Second Mac run (`c4cf1743`): `VERDICT OK`; the cause was macOS's interpreter name `Python`; the five tests pass.

## GO / NO-GO

**GO (confirmed on the Mac)** for the worker limit change and the portable test infrastructure, conditional on the Mac probe confirming
that the rejected operation is `RLIMIT_AS`. **NO-GO** (stop and amend the contract) if a limit other than
`RLIMIT_AS` is the cause. R28 stays not complete either way.
