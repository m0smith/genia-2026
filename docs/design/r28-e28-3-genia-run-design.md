# R28 E28-3 — `genia_run` Tool: Design

Status: **Final design (decisions D1-D4 approved; contract Clarification A4 merged
into the contract).** Nothing here is implemented until the implementation phase;
`GENIA_STATE.md` remains final authority (E28-1: section 9.41; E28-2: section 9.42;
`execution.process`: section 9.40). Governing contract:
`docs/design/r28-genia-mcp-contract-threat-model.md` sections 2.5, 3, 4, 5, 6, 7.1 and
Clarification A4 (section 17). Findings: `docs/analysis/r28-host-dependency-inventory.md`
(cited as `[H##]`). Issue: #704.

## 1. What the contract requires

Source-only; one fresh disposable worker per call; value rendered by the canonical
debug renderer (never scraped from stdout); `stdout`, `stderr`, and `value.rendered`
as separate channels; fixed 5,000 ms deadline; 1 MiB per channel and value; 3,276,800
bytes per result; envelope kinds `parse_error`, `policy_denied`, `runtime_error`,
`timeout`, `cancelled`, `input_limit`, `result_limit`, `internal_error`; no partial data
on any failure; layered defense (pre-execution policy **and** restricted runtime **and**
OS restrictions); cancellation that terminates and reaps the worker; fixed server-owned
messages (section 2.2).

## 2. Approved decisions

| # | Decision | Where it lands |
|---|---|---|
| D1 | Pre-execution policy runs in the worker over the **raw parser AST** (Clarification A4). The shared normalized parse surface is not expanded. | `hosts/python/mcp_worker_profile.py` |
| D2 | A narrow MCP worker supervisor; `execution.process` is not extended; no Genia builtin, prelude API, syntax, or Core IR. | `hosts/python/mcp_run_capability.py` |
| D3 | Cancellation is honored, not ignored: a host line multiplexer feeds the native stdin loop and lets native Genia interpret lines that arrive while a run is in flight. Host owns only the select/terminate/reap mechanism. | `hosts/python/mcp_stdin.py` + native `is_cancel` predicate (section 4) |
| D4 | Mandatory worker floor plus stronger OS isolation only where verified; never described as a sandbox. | section 5 |

## 3. Reconnaissance (probed on `main` at `602cda01`)

| Fact | Evidence | Consequence |
|---|---|---|
| Command-source evaluation is `run_source(source, env, filename="<command>")`; the CLI then calls `_resolve_program_result` (which dispatches `main`) and `_emit_result` (`format_debug`) | `src/genia/interpreter.py` | the worker uses `run_source` and `format_debug` directly. Contract section 2.5 says "no implicit entrypoint", so `main` is **not** dispatched, although STATE's `-c` mode does dispatch it [H29] |
| `make_global_env(stdin_provider=, stdout_stream=, stderr_stream=, environment_snapshot_provider=, dotenv_snapshot_provider=)` already exist | `src/genia/builtins.py` | sinks can be captured and the stdin source replaced without any Genia change |
| The default environment is unrestricted: 241 bindings plus 234 autoloads include file, zip, resource, HTTP, server, config, secret, model, retrieval, `input`, `stdin_keys`, and spawn bindings | probes | the worker prunes by an explicit default-deny classification [H24] |
| A shell stage `$(cmd)` calls `subprocess.run(shell=True)` inside the evaluator, not through a global binding | `_eval_shell_stage` | pruning the environment cannot remove it; it needs policy plus a runtime stub plus the OS layer [H28] |
| `import` loads modules through `env.load_module` | evaluator `IrImport` | the worker replaces `load_module` with a denial; `import` is also rejected by policy |
| Normalized AST cannot carry policy facts (`Call`, `ImportStmt` lose names) | ledger H23/H25 | policy uses the raw AST (A4) |
| `GeniaStdinSource` reads items from an iterator factory and strips trailing `\r\n` | `src/genia/values.py` | a host iterator can feed the native loop unchanged |
| Prototype (scratchpad, not committed): a Python line multiplexer + select + a Genia closure called by the host during a blocking call honored a cancel line queued with the request, honored one arriving mid-run, and preserved non-cancel lines in order | prototype run recorded in the ledger (H27) | cancellation needs no A5 |
| Genia returns a closure from a function only through a call argument (`keep((line) -> ...)`); `f(x) = (y) -> ...` is arm sugar | prototype | native predicate construction detail |
| `unshare --user --map-root-user --net` works on this host; availability elsewhere is not assumed | probe | probed and verified at runtime, best effort |

## 4. Architecture

```text
MCP client --stdio--> hosts/python/mcp_stdin.py  (raw line multiplexer: split on \n only)
                        |  lines (unchanged native loop: stdin |> lines |> ...)
                        v
                      mcp.genia  (decode, validate, dispatch, limits, envelopes)
                        |  run(source, is_cancel)   (explicit `run` capability)
                        v
              hosts/python/mcp_run_capability.py   (supervisor)
                        |  fresh process per call; source over a stdin pipe
                        v
              hosts/python/mcp_worker.py           (worker)
                 limits -> parse -> policy(raw AST) -> pruned env -> evaluate -> render
```

### 4.1 Native `mcp.genia` (class C, unchanged ownership)

- advertises `genia_run` only when the host provisions `run` (tool order stays
  `genia_capabilities`, `genia_parse`, `genia_run`); CLI mode never advertises it;
- validates `{source: string}` exactly (closed schema, `-32602` otherwise); source over
  262,144 UTF-8 bytes is `input_limit` before any worker starts;
- builds `is_cancel` natively: a closure that returns true only for a
  `notifications/cancelled` message whose `params.requestId` equals the active request id;
- decodes the closed worker reply and builds every envelope; the aggregate result limit
  is measured on the encoded envelope exactly as for `genia_parse`.

### 4.2 Closed worker reply (one ASCII-only JSON line)

| `status` | Payload | Envelope |
|---|---|---|
| `completed` | `value` (rendered), `stdout`, `stderr` (strings) | `ok`, `result: {kind: "completed", value: {rendered}, stdout, stderr, exit_code: 0}` |
| `parse_error` | `offset` (int or null) | `parse_error`, phase `parse`, message `Genia source failed to parse at character offset N` (E28-2 wording) |
| `policy_denied` | none | `policy_denied`, phase `policy`, message `source requests a capability unavailable in the MCP v1 profile` |
| `runtime_error` | none | `runtime_error`, phase `execution`, message `Genia source failed during evaluation` |
| `timeout` | none | `timeout`, phase `execution`, message `Execution exceeded the 5000 ms limit` |
| `cancelled` | none | `cancelled`, phase `execution`, message `Execution was cancelled` |
| `result_limit` | none | `result_limit`, phase `adapter`, message `Result exceeds a 1048576-byte channel limit` (channel/value overflow); aggregate overflow keeps the E28-2 message |
| `internal_error` or any unreadable reply | none | `internal_error`, phase `adapter`, message `Internal error while executing` |

Every message is fixed and server-owned (contract section 2.2): no Genia diagnostic text,
no source fragment, no rendered value, no path. `isError` is true for every non-`completed`
outcome and no partial `stdout`, `stderr`, or value accompanies a failure. The reply has
no `exit_code`; native fixes it to `0`.

### 4.3 Cancellation mechanism (D3)

`hosts/python/mcp_stdin.py` owns fd 0 only when the `run` capability is provisioned. It
reads raw bytes, splits on `\n` only, decodes UTF-8 with `surrogateescape` (the same
decoding the existing stdin source yields), and supplies the line iterator to
`make_global_env(stdin_provider=...)`. The native loop is unchanged (`stdin |> lines |>
...`). While a run is in flight the supervisor `select`s over the worker pipes **and** the
multiplexer's fd. For every raw line that is already queued or newly arrives it calls the
native `is_cancel(line)`; on true it drops that line, kills the worker's process group,
reaps it, and returns `{"status": "cancelled"}`. Other lines stay queued in order for the
native loop. The host does no JSON decoding, method matching, or id comparison; that is
native Genia. Back-pressure: while more than 8 MiB of unread input is pending the
multiplexer stops reading, so a flooding client cannot grow server memory without bound
(and then cannot be observed for cancellation: best effort, recorded in H27). EOF during a
run lets the run finish; the server then exits at EOF as before.

Races resolve by the first terminal state recorded by the supervisor: a worker reply
already read wins over a later cancel; a cancel seen first wins over a late reply.

### 4.4 Supervisor responsibilities (D2; all listed in ledger H26)

fresh process per call; private empty temporary working directory, removed after reap;
fixed environment allowlist (no `PATH`, no `HOME`, no user variables); `close_fds`,
stdin/stdout/stderr pipes only; own session/process group; source written to the worker
stdin pipe while draining output (solves H06/H07 for this worker only); monotonic 5,000 ms
deadline from spawn; incremental byte caps with kill on excess; kill and reap on timeout,
cancel, limit, or any internal failure; worker `stderr` drained and discarded (never
forwarded); reply validated only for shape (single ASCII line, bounded) before native
decoding; any exception becomes `internal_error`. It contains no MCP literals, no envelope
construction, and no JSON interpretation of the reply.

Removable/generalizable code: the whole supervisor if a general cancellable
process-with-stdin capability lands (H05-H08); the multiplexer if Genia gains a
non-blocking/bounded stdin source (H09).

### 4.5 Worker (class A, intrinsic)

1. Self-imposed limits: `RLIMIT_AS`, `RLIMIT_CPU`, `RLIMIT_FSIZE = 0`, `RLIMIT_CORE = 0`,
   `RLIMIT_NOFILE`; Python-level stubs for `subprocess`, `os.system`, `os.exec*`,
   `os.fork`, `os.spawn*`, `os.popen`, and `socket` connect/bind (a runtime layer under
   policy and the pruned environment, for shell stages and anything else that bypasses
   bindings).
2. Reads the source from stdin (at most 262,144 bytes), decodes strictly.
3. Parses with the real parser. `SyntaxError` is `parse_error` with the same offset rule
   as the E28-2 capability; any other failure is `internal_error`.
4. **Policy over the raw AST** (A4): reject `ImportStmt`, `ShellStage`, open/extend/use
   forms that import modules, annotation forms that bind server/route authority, and any
   reference to a prohibited name. Conservative: a user-defined name equal to a prohibited
   binding is also rejected.
5. Builds the environment with `cli_args=[]`, an empty stdin iterator (immediate EOF),
   bounded in-memory `stdout`/`stderr` streams, empty environment/dotenv snapshot
   providers, then **prunes by default-deny**: only names in the explicit allowlist
   survive (bindings and autoloads); `env.load_module` is replaced by a denial.
6. Evaluates with `run_source(source, env, filename="<command>")` (no `main` dispatch).
7. Renders with `format_debug` (the canonical debug renderer); rejects a protected carrier
   with `policy_denied`; enforces the 1 MiB value limit; writes one reply line.

A channel write that crosses 1,048,576 bytes sets an overflow flag, aborts evaluation, and
yields `result_limit` with all partial data discarded, even if the program swallowed the
abort. Rendering cannot be bounded incrementally (`format_debug` returns a finished
string), so a pathological value is bounded by the deadline and `RLIMIT_AS` and then
checked; recorded in H30.

## 5. Isolation: guarantees versus best effort (D4)

Mandatory floor, every call, on any host that runs the Python reference host:
fresh process; fixed minimal environment; private empty working directory; only the three
pipes inherited; empty argv; program stdin at EOF; `RLIMIT_FSIZE`/`AS`/`CPU`/`CORE`/`NOFILE`;
monotonic 5,000 ms deadline; kill of the process group and reap; pruned Genia environment
and rejected policy forms.

Best effort, used **only if verified at runtime**: a user + network namespace
(`unshare --user --map-root-user --net`). The supervisor probes once per process by running
a check inside the namespace; if the probe fails the worker runs without it, and nothing
claims it. Not provided and not claimed: filesystem namespaces, seccomp, memory or CPU
cgroups, a PID namespace, protection against kernel or interpreter bugs, or isolation from
other processes owned by the same user. This is a defense-in-depth profile, **not a security
sandbox and not production multi-tenant isolation**.

`genia_capabilities.execution_profile` keeps its closed shape and meaning (Clarification A1:
governed policy). Its `filesystem`, `environment`, `configuration`, `secrets`, and `network`
flags stay `false` because no such Genia authority is provisioned; they do not assert an OS
mechanism. The OS layer is described in STATE and this document only.

## 6. Native vs host ledger (E28-3 slice)

| # | Responsibility | Class | Note |
|---|---|---|---|
| H24 | Restricted Genia profile | B -> host prune | default-deny classification of 475 names |
| H25 | Policy over raw AST | resolved by A4 | worker-side |
| H26 | Worker supervisor | A | refines H04, H06, H07 |
| H27 | Cancellation | resolved mechanism | multiplexer + native predicate; host does no protocol work |
| H28 | Shell stage bypasses bindings | A | runtime stub + OS layer + policy |
| H29 | Contract "no implicit entrypoint" vs STATE `-c` main dispatch | N | contract wins for MCP; recorded |
| H30 | Value rendering cannot be bounded incrementally | B | deadline + `RLIMIT_AS` + post check |

## 7. Failing-test plan (written next, before any implementation)

New files: `tests/unit/test_r28_mcp_run.py` (wire behavior through the launcher),
`tests/unit/test_r28_mcp_run_worker.py` (worker, policy, profile),
`tests/unit/test_r28_mcp_run_supervisor.py` (supervisor, multiplexer, cancellation);
shared helpers in `tests/fixtures/r28_mcp_helpers.py`. Required coverage:

1. Discovery: CLI mode lists only `genia_capabilities`; launcher mode lists exactly
   `[genia_capabilities, genia_parse, genia_run]` with the closed schema only because
   `genia_run` is implemented; `genia_capabilities.tools` agrees.
2. Source-only: extra/missing/non-string arguments are `-32602`; no mode, argv, stdin,
   filename, environment, timeout, or limit argument is accepted.
3. Command-source parity: for a corpus of side-effect-free sources the rendered value equals
   the output of ordinary `-c` command mode (same renderer), including `none("nil")`
   present, and a source defining `main` does not dispatch it.
4. Channel separation: value, stdout, and stderr distinct; stdout containing newlines,
   braces, JSON, and MCP-looking lines never corrupts framing; the server's stdout carries
   only frames.
5. Fresh worker: no binding, file, environment variable, or random state carries across
   calls; each call sees empty argv, stdin at EOF, an empty working directory.
6. Denial matrix, each class asserted at the policy layer and again at the restricted
   runtime layer (worker run with policy disabled in a unit test): filesystem, environment,
   configuration, secrets, network, process/shell (`$(...)` must not create a marker),
   `import`, spawn of external commands, `input`, `stdin_keys`; plus a bypass attempt via
   `eval`/indirection that fails closed.
7. Limits: source at 262,144 bytes runs and 262,145 is `input_limit` with no worker
   started; stdout, stderr, and value each at the limit succeed and one byte over is
   `result_limit` with the worker reaped; aggregate result over 3,276,800 is `result_limit`.
8. Deadline: infinite loop, deep recursion, sleep, and unbounded Flow consumption return
   `timeout` near 5,000 ms and leave no surviving process.
9. Cancellation: cancel queued with the request, cancel mid-run, cancel for a different
   request id (ignored), cancel after completion (ignored), non-cancel lines during a run
   answered in order afterward; worker reaped each time; the `cancelled` envelope carries no
   partial data.
10. Failures carry no partial data and fixed messages: `runtime_error`, `parse_error`
    (offset only), `policy_denied`, `internal_error` (worker crash, malformed reply);
    messages contain no source, path, class name, or Genia diagnostic text.
11. Protected values never reach `value.rendered`, stdout, stderr, or messages
    (`policy_denied`, fixed message; injected carrier in a worker unit test).
12. Drift guards: host modules contain no MCP literals; no new Genia builtin, prelude
    function, syntax, or Core IR node; normalized parse output and ordinary CLI output
    unchanged; R9 JSON unchanged; changing only the revision changes only revision bytes;
    the profile classification covers every binding and autoload (a new unclassified
    binding fails the test).

## 8. Out of scope

Resources, prompts, additional tools, C++ MCP, streamable HTTP, execution modes, parser or
normalization changes, new Genia builtins or syntax, any R9/R23 change, VS Code
configuration, the final demo (E28-5), and the release audit (E28-6).
