# R28 E28-3 — `genia_run` Tool: Design (decision-gated)

Status: **Design draft; blocked on the decisions in section 6. Nothing here is
implemented.** `GENIA_STATE.md` remains final authority (E28-1: section 9.41;
E28-2: section 9.42; `execution.process`: section 9.40). Governing contract:
`docs/design/r28-genia-mcp-contract-threat-model.md` sections 2.5, 3, 4, 5, 6, 7.1.
Findings: `docs/analysis/r28-host-dependency-inventory.md` (cited as `[H##]`).
Issue: #704 (E28-3). This is the first R28 phase where the contract's mandatory
isolation, deadline, cancellation, and policy requirements meet real Genia surfaces.

## 1. What the contract requires (summary)

Source-only, one fresh disposable worker per call, command-source evaluation
semantics, value rendered by the canonical debug renderer (not scraped from stdout),
stdout/stderr/value as separate channels, fixed 5,000 ms deadline, incremental 1 MiB
channel limits, 3,276,800-byte result, `policy_denied` / `runtime_error` /
`parse_error` / `timeout` / `cancelled` / `result_limit` envelopes, no partial data on
failure, layered defense (pre-execution policy **and** restricted runtime **and**
OS restrictions), cancellation that terminates and reaps the worker.

## 2. Reconnaissance (probed on `main` after E28-2)

| Fact | Evidence | Consequence |
|---|---|---|
| Command-source evaluation is `run_source(source, env, filename="<command>")` then `_resolve_program_result` and `_emit_result` (`format_debug`) in `src/genia/interpreter.py` | code | the worker can reuse these without scraping CLI stdout; `make_global_env(stdout_stream=, stderr_stream=, output_handler=)` already lets a host capture sink writes separately |
| The default global environment is **not** restricted: `read_file`, `write_file`, `_http_send`, `_spawn`, `_execution_process`, `zip_*`, `resource_*`, config/secret/model/retrieve bindings, `sleep` all exist | `read_file("/etc/hostname")` returned `"vm\n"` in command mode; 241 bindings, ~45 authority-bearing | policy must **remove** authority; there is no "restricted profile" in Genia [H24] |
| Authority also arrives through autoloaded prelude modules (`file`, `web`, `process`, `execution`, `resource`, `io`) | `src/genia/std/prelude/*.genia`, `register_autoload` | denial must cover autoloads and `import`, not only global names |
| The normalized AST cannot carry policy facts: `read_file("x")` -> `{kind: Call}`, `import web` -> `{kind: ImportStmt}`, calls lose their callee | `parse_and_normalize` probes (ledger H23) | contract section 3 "native policy over normalized parse data" is impossible with the current normalization; policy needs the raw parser AST, inside the host [H25] |
| `execution.process` cannot launch the worker: stdin is `DEVNULL`, argv-only (128 KiB per element vs a 262,144-byte source), executable is a symbol bound by a host capability, one blocking call | STATE 9.40; `process_transport.py` | ledger H04 ("reuse unchanged") does not hold for this use; a worker supervisor is a new narrow host module [H26] |
| The server's single-threaded `stdin |> lines` loop cannot see `notifications/cancelled` while a blocking call runs | E28-1 design, ledger H08/H09 | cancellation cannot be honored natively [H27] |
| `unshare -rn` (user + network namespace) works on this host; `prlimit`, `setpriv` exist; availability on other hosts is unverified | probe | OS-level network denial is possible but must be best-effort and honestly reported |

## 3. Proposed architecture (smallest design consistent with the contract)

```text
MCP client --stdio--> mcp.genia  (native: decode, validate, dispatch, limits, envelopes)
                        |  run(source) -> reply text      (explicit `run` capability)
                        v
              hosts/python/mcp_run_capability.py    (supervisor, intrinsic host)
                        |  one fresh process per call; source over a stdin pipe
                        v
              hosts/python/mcp_worker.py            (worker, intrinsic host)
                 restricted env -> parse -> policy (raw AST) -> evaluate -> render
```

- `mcp.genia` keeps the source byte check, argument validation, envelope construction,
  and the result-size check. It receives one closed reply and builds the envelope; the
  host never builds MCP envelopes (same split as E28-2).
- The supervisor spawns `python -m hosts.python.mcp_worker` with `shell=False`, a fixed
  environment allowlist, an empty private cwd, no inherited fds, `prlimit` limits, and
  best-effort namespace isolation; it sends the source on stdin (solves H06/H07 for this
  worker only, without changing `execution.process`), enforces the monotonic deadline,
  counts bytes incrementally per channel, and kills and reaps the worker on timeout or
  limit.
- The worker builds a **pruned** global environment (authority bindings and autoloads
  removed, `import` rejected), parses with the real parser, rejects prohibited constructs
  from the **raw** AST (`policy_denied`), evaluates with command-source semantics under
  captured sinks, renders the value with `format_debug`, and writes one closed JSON line.
- Reply shape (closed): `completed{value_rendered, stdout, stderr}` |
  `parse_error{offset|null}` | `policy_denied` | `runtime_error{message}` |
  `internal_error`; the supervisor adds `timeout` and `result_limit`.

## 4. Native vs host ledger (E28-3 slice, provisional)

| # | Responsibility | Class | Note |
|---|---|---|---|
| H24 | No restricted-authority evaluation profile in Genia | B (host prunes in worker) | evidence above; candidate general "capability-restricted environment" facility, audit decides |
| H25 | Normalized AST too coarse for policy | N/B | follow-up candidate is parse-contract expansion (H23); E28-3 uses the raw AST in the worker |
| H26 | Worker supervisor cannot reuse `execution.process` | A | new narrow host module; refines H04/H06/H07 |
| H27 | Cancellation vs the native single-threaded stdin loop | B | decision required (section 6) |
| H04 | OS isolation, deadline, kill/reap | A | now realized by the supervisor, not by `execution.process` |

## 5. Failing-test plan (once section 6 is decided)

1. CLI mode (no `run` capability) does not advertise `genia_run`; launcher mode advertises `[genia_capabilities, genia_parse, genia_run]` with the exact closed schema.
2. Completed run: `value.rendered` equals `format_debug` of the same source via command mode; `stdout`/`stderr` separate; `exit_code: 0`; `none("nil")` is a present rendered value.
3. Output cannot corrupt framing: stdout containing newlines, `}`, JSON, or MCP-looking lines stays inside `stdout`; the server's own stdout carries only frames.
4. Failures carry no partial data: `runtime_error`, `parse_error` (offset only), `policy_denied` for each denied class (file, env, config/secret, network, process/shell, import, interop).
5. Layered denial: each denied authority is denied both by pre-execution policy and by the pruned runtime (a policy bypass test using indirect access still fails closed).
6. Limits: source over 262,144 bytes -> `input_limit` before any worker; stdout/stderr/value over 1 MiB -> `result_limit`, worker reaped; result over 3,276,800 -> `result_limit`.
7. Deadline: infinite loop, recursion, sleep, and Flow consumption -> `timeout` at 5,000 ms with no surviving process.
8. Freshness: no state, binding, file, or environment carries between calls; the worker sees no user environment variables, empty argv, stdin at EOF.
9. Protected values never reach `rendered`/stdout/stderr/messages (`policy_denied`, fixed message).
10. Drift guards: host modules contain no MCP literals; changing only the revision changes only revision bytes; no new Genia builtin; R9 JSON unchanged.

## 6. Decisions required before failing tests or implementation

These are significant architectural choices the approved contract and E28-2 pattern do
not settle; none has been implemented.

**D1 — Policy source of truth.** Contract section 3 puts policy composition in native
`mcp.genia` over normalized parse data, but the normalized AST cannot express policy
(H25). Options: (a) *recommended*: policy runs in the worker over the raw parser AST,
`mcp.genia` only maps the closed reply to `policy_denied` (clarification A4 would amend
section 3/4: policy is evaluated at the host boundary because the normalized parse
surface lacks the information); (b) first expand the shared parse normalization to carry
callee/import facts (a parse-contract change owned by the parse-spec process, outside
R28) and keep policy native.

**D2 — Worker supervisor.** Confirm a new narrow host supervisor module (section 3)
rather than extending `execution.process` (which would add Genia-visible semantics that
R28 must not introduce).

**D3 — Cancellation.** The contract requires `notifications/cancelled` to terminate and
reap the worker. With a single-threaded native stdin loop that is not implementable
natively. Options: (a) *recommended for E28-3*: ship the fixed 5,000 ms timeout and keep
the E28-1 behavior (a cancel notification is accepted and ignored because the call is
synchronous), recording the gap as an explicit contract clarification (A5: cancellation
is deferred to E28-4/E28-5 together with a transport/supervisor design); (b) move stdin
reading into a host reader thread that detects cancellation (this transfers the stdin
loop out of native Genia and contradicts E28-1 ownership); (c) block E28-3 until a
cancellable-process facility exists (H08).

**D4 — OS isolation floor.** Contract requires restrictions "where available". Confirm:
process-level controls always (fixed env, private empty cwd, `prlimit`, no inherited
fds), plus network/user-namespace isolation when `unshare` works, with `genia_capabilities`
reporting the profile honestly and never advertising a sandbox.

## 7. Out of scope

Resources, prompts, additional tools, C++ MCP, streamable HTTP, execution modes,
parser or normalization changes, new Genia builtins or syntax, any R9/R23 change.
