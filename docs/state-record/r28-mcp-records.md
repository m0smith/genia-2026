# R28 MCP record

> **Non-authoritative provenance record.** This file preserves, verbatim and unedited, text that was displaced
> from `GENIA_STATE.md` during the #1099 distillation. It is audit material, not part of the truth hierarchy:
> it does not define Genia behavior, and `GENIA_STATE.md` governs. Start with the release, design, and reference
> documents; open this file only to see the exact displaced wording.
>
> Baseline: `GENIA_STATE.md` at `d401f322c692e8c3620509854065692c2605c61a`. Scope: Sections 9.41-9.47 history and the pre-condensation text of 9.48-9.51.
> Ledger: `docs/analysis/state-distillation-migration-map.json`.

## B293: baseline lines 6308-6326

Moved from GENIA_STATE.md@d401f322, lines 6308-6326 (ledger row B293, moved, sha256 f20e75c10336bbf6)

~~~~~markdown
## 9.41) R28 E28-1 native Genia MCP server skeleton (`apps/mcp/mcp.genia`)

Status: Implemented (Python reference host), **Experimental, intermediate
development surface of the then-incomplete R28 release** (R28, epic #700, is complete as of section 9.49);
this section records only what E28-1 (issue #702) landed under the approved
contract `docs/design/r28-genia-mcp-contract-threat-model.md` (including
Clarification A1) and design `docs/design/r28-e28-1-native-mcp-skeleton-design.md`.
It is not an availability claim for agents or editors: no checked-in MCP client
configuration exists and no VS Code/Copilot acceptance has been demonstrated.

LANGUAGE CONTRACT:

- E28-1 adds no syntax, parser rule, AST or Core IR node, builtin, prelude function,
  evaluator behavior, or host capability claim to Genia. `apps/mcp/mcp.genia` is an
  ordinary Genia program built only from existing behavior (`stdin |> lines`,
  `json_decode`/`json_encode`, `json_schema` Templates, guard/tuple/list/map patterns,
  Outcomes, `writeln(stdout, ...)`). The MCP wire behavior below is that program's
  application contract, not Genia language semantics.

~~~~~

## B294: baseline lines 6327-6341

Moved from GENIA_STATE.md@d401f322, lines 6327-6341 (ledger row B294, moved, sha256 ef626c92e25d8d29)

~~~~~markdown
APPLICATION BEHAVIOR (`apps/mcp/mcp.genia`, MCP `2026-07-28`, local stdio only):

- The program takes exactly one argument, `contract_revision`, which must be exactly
  40 lowercase hexadecimal characters. Any other argument list writes one fixed
  diagnostic to stderr, writes nothing to stdout, and exits nonzero. The rejected
  value is never echoed. Because Genia has no process-exit facility, the nonzero exit
  is produced by a deliberate runtime error (ledger entry R28-H15).
- It reads one JSON-RPC message per stdin line (split on `\n` only) and writes one
  response per request, each on exactly one stdout line. Empty lines are ignored; a
  message without `id` that is a well-formed notification (for example
  `notifications/cancelled`) gets no response. It exits when stdin reaches EOF.
- Implemented methods: `server/discover`, `tools/list`, and `tools/call`. For
  `2026-07-28` there is no `initialize`, no session, and no state carried between
  requests. (Amendment A5, section 9.47, adds the `2025-11-25` compatibility era:
  `initialize`, `ping`, and one process-local state bit.)
~~~~~

## B295: baseline lines 6342-6359

Moved from GENIA_STATE.md@d401f322, lines 6342-6359 (ledger row B295, moved, sha256 19ef4da60f704546)

~~~~~markdown
- The advertised tool set is exactly `["genia_capabilities"]`. `genia_parse` and
  `genia_run` are not implemented and are not advertised; calling them is an
  unknown-tool error (`-32602`).
- `genia_capabilities` takes no arguments (arguments may be omitted or `{}`; anything
  else is `-32602`) and returns a `CallToolResult` with `resultType: "complete"`,
  `isError: false`, one text content item, and `structuredContent` equal to the
  contract envelope `{schema_version: "genia.mcp.v1", status: "ok", result:
  <capabilities>, error: null}`. The capabilities object has exactly the contract
  fields (`server`, `mcp`, `genia`, `tools`, `execution_profile`); `tools` is
  `["genia_capabilities"]` and `contract_revision` is the launch argument. The
  `execution_profile` reports the governed policy only; nothing is executed or
  enforced in E28-1.
- Per-request `params._meta` must carry `io.modelcontextprotocol/protocolVersion` (a
  string) and `io.modelcontextprotocol/clientCapabilities` (an object); results carry
  `_meta["io.modelcontextprotocol/serverInfo"]` of `{name: "genia-mcp", version:
  <contract_revision>}`. Discover and list results use `ttlMs: 0`,
  `cacheScope: "public"`; `server/discover` capabilities are exactly `{tools: {}}`;
  `tools/list` has no pagination (any `cursor` is `-32602`).
~~~~~

## B296: baseline lines 6360-6373

Moved from GENIA_STATE.md@d401f322, lines 6360-6373 (ledger row B296, moved, sha256 7f7e3dd25ef74717)

~~~~~markdown
- Protocol errors use fixed messages that never echo caller text: unparseable JSON
  `-32700`; invalid JSON-RPC object (including an `id` that is not a string or
  integer) `-32600`; unknown method (including `initialize`, resources, prompts)
  `-32601` (an `initialize` carrying the `2026-07-28` `_meta` stays `-32601`; section 9.47);
  missing/malformed `_meta`, bad `tools/call` params, unknown tool, or
  non-empty arguments `-32602`; unsupported version `-32022` with
  `data.supported = ["2026-07-28"]` and `data.requested`.
- Native Genia owns decoding, shape/type validation, dispatch, result and error
  construction, JSON encoding, single-line framing (`json_encode`, split on
  newline, trim, join), and stdout. The program imports no module and references no
  filesystem, network, process, configuration, or secret facility.

PYTHON REFERENCE HOST:

~~~~~

## B297: baseline lines 6374-6388

Moved from GENIA_STATE.md@d401f322, lines 6374-6388 (ledger row B297, moved, sha256 a57231ca128204b5)

~~~~~markdown
- `hosts/python/mcp_launch.py` is build/launch identity plumbing only: it resolves
  `git rev-parse HEAD` for the repository (module-relative; ambient `GIT_*`
  ignored; workspace modifications never described), validates 40 lowercase hex,
  builds the command (`python -c "from genia.interpreter import _main; ..."`, the
  same invocation as `hosts/python/exec_cli.py`), applies a fixed environment
  allowlist, and starts `mcp.genia` with the revision as its only argument. It
  imports no JSON module and contains no tool, envelope, or protocol logic. No MCP
  SDK is used.
- Validated by `tests/unit/test_r28_mcp_skeleton.py` (wire behavior, framing,
  startup), `tests/unit/test_r28_mcp_launcher.py` (launch identity), and
  `tests/unit/test_r28_mcp_architecture.py` (native ownership and Python-drift
  guards, including a differential run proving the host controls only the revision).

Explicit limitations (not implemented in E28-1):

~~~~~

## B298: baseline lines 6389-6397

Moved from GENIA_STATE.md@d401f322, lines 6389-6397 (ledger row B298, moved, sha256 fa4e56caa35a0fc6)

~~~~~markdown
- No `genia_parse`, no `genia_run`, no worker process, no timeout/cancellation/size
  enforcement, no MCP resources or prompts, no MCP client, no HTTP transport, no
  checked-in `.mcp.json`/`.vscode/mcp.json`, no VS Code/Copilot acceptance, and no
  C++ MCP support or parity claim. The `portable_mcp_implementation` field is
  `false`.
- Host dependencies and Genia gaps found while building it are recorded in the
  living ledger `docs/analysis/r28-host-dependency-inventory.md`; recording a gap
  adds no language feature.

~~~~~

## B299: baseline lines 6398-6454

Moved from GENIA_STATE.md@d401f322, lines 6398-6454 (ledger row B299, moved, sha256 0c9e80d4107321cf)

~~~~~markdown
## 9.42) R28 E28-2 `genia_parse` over the native Genia MCP server

Status: Implemented (Python reference host), **Experimental, intermediate development
surface of the then-incomplete R28 release** (R28, epic #700, is complete as of section 9.49; E28-2 is issue #703).
Governing documents: contract `docs/design/r28-genia-mcp-contract-threat-model.md`
(Clarifications A2 and A3) and design `docs/design/r28-e28-2-parse-tool-design.md`.
Section 9.41 still applies; this section records only what E28-2 adds.

LANGUAGE CONTRACT:

- E28-2 adds no syntax, parser rule, AST or Core IR node, builtin, prelude function,
  integer type, JSON facility, or change to R9/R23 `json_decode`/`json_encode`. Genia
  integer semantics and the R9 portable-JSON integer range
  `[-9007199254740991, 9007199254740991]` are unchanged. The behavior below is
  application and host-transport behavior of `apps/mcp/mcp.genia`.

APPLICATION BEHAVIOR:

- `genia_parse` is advertised and callable only when the host launcher provisions the
  `parse` capability as an explicit argument to `serve(revision, host)`. Plain
  `genia apps/mcp/mcp.genia <revision>` (CLI mode) provisions none and keeps the
  section 9.41 surface (`genia_capabilities` only; `genia_parse` is an unknown tool).
- Input is exactly one string `source`; missing, non-string, or extra properties are
  `-32602`. A well-formed `source` over 262,144 UTF-8 bytes is an `input_limit`
  envelope without parsing; invalid Unicode is `-32700` at the JSON-RPC boundary
  (Clarification A2). Parsing never evaluates source.
- Success is `{schema_version: "genia.mcp.v1", status: "ok", result: {kind: "parsed",
  ast}, error: null}` where `ast` is the existing normalized parse surface
  (`hosts/python/parse_adapter.parse_and_normalize`), unchanged. A Genia syntax
  failure is a `parse_error` / phase `parse` envelope carrying only a character
  offset (never source text or host error text); any other host failure is a fixed
  `internal_error` envelope; a result over 3,276,800 bytes is `result_limit`.
- Lossless AST transport (ledger R28-H22, Clarification A3): the host capability
  serializes the normalized AST losslessly and `mcp.genia` inserts that text into the
  result without decoding or re-encoding it through R9 JSON, so integer literals
  outside the R9 range (for example `9007199254740992` or
  `123456789012345678901234567890`) are returned as exact JSON integer tokens,
  neither rounded nor stringified. `mcp.genia` still validates the capability header
  and AST text shape, applies the source and result limits, and builds the envelope.
  This is not a general Genia raw-JSON facility. A client whose JSON decoder is
  IEEE-754-only may not preserve such integers as native numbers; that is outside
  this contract.
- The normalized AST is the existing minimal projection: most node kinds (including
  unary negation, so a negative literal) appear as `{kind}` only (ledger R28-H23);
  E28-2 does not change normalization.

PYTHON REFERENCE HOST:

- `hosts/python/mcp_parse_capability.py` (`parse_source`) wraps `parse_and_normalize`;
  `hosts/python/mcp_host.py` is the in-process bootstrap that calls
  `serve(revision, {parse: ...})` (the launcher starts it). No MCP SDK is used.
- Validated by `tests/unit/test_r28_mcp_parse.py`,
  `tests/unit/test_r28_mcp_parse_capability.py`, and the existing R28 tests.

Explicit limitations: no `genia_run`, no worker/timeout/cancellation, no MCP resources
or prompts, no C++ MCP support or parity claim, no checked-in client configuration.

~~~~~

## B300: baseline lines 6455-6470

Moved from GENIA_STATE.md@d401f322, lines 6455-6470 (ledger row B300, moved, sha256 246cc0f6ae3c42fd)

~~~~~markdown
## 9.43) R28 E28-3 `genia_run` over the native Genia MCP server

Status: Implemented (Python reference host), **Experimental, intermediate development
surface of the then-incomplete R28 release** (R28, epic #700, is complete as of section 9.49; E28-3 is issue
#704). Governing documents: contract `docs/design/r28-genia-mcp-contract-threat-model.md`
(Clarifications A2, A3, A4) and design `docs/design/r28-e28-3-genia-run-design.md`.
Sections 9.41 and 9.42 still apply; this section records only what E28-3 adds. It is not
an availability claim for agents or editors and **not a security sandbox**.

LANGUAGE CONTRACT:

- E28-3 adds no syntax, parser rule, normalized parse change, AST or Core IR node, builtin,
  prelude function, evaluator behavior, integer type, JSON facility, `execution.process`
  change, or ordinary CLI behavior, and changes no R9/R23 JSON rule. The behavior below is
  application and host behavior of `apps/mcp/mcp.genia` and its host modules.

~~~~~

## B301: baseline lines 6471-6489

Moved from GENIA_STATE.md@d401f322, lines 6471-6489 (ledger row B301, moved, sha256 bcccd9a36ee3132a)

~~~~~markdown
APPLICATION BEHAVIOR:

- `genia_run` is advertised and callable only when the host launcher provisions the `run`
  capability. The advertised order is `genia_capabilities`, `genia_parse`, `genia_run`;
  launcher mode lists exactly these three, plain CLI mode (`genia apps/mcp/mcp.genia
  <revision>`) still lists only `genia_capabilities` and treats `genia_run` as an unknown
  tool. `genia_capabilities.tools` and `execution_profile` keep their closed shape; the
  profile flags report governed policy (no such Genia authority is provisioned), not OS
  mechanisms.
- Input is exactly one string `source` (any other argument is `-32602`). A well-formed
  `source` over 262,144 UTF-8 bytes is `input_limit` before any worker starts; invalid
  Unicode is `-32700` at the JSON-RPC boundary (Clarification A2).
- Success is `{schema_version, status: "ok", result: {kind: "completed", value:
  {rendered}, stdout, stderr, exit_code: 0}, error: null}`. `value.rendered` is the
  existing canonical debug rendering of the final value (`format_debug`); `stdout` and
  `stderr` are the program's output-sink writes captured separately; none is scraped from
  the others. A successful `none("nil")` is a present rendered value. Source is evaluated
  with `run_source` (command-source evaluation); `main` is **not** dispatched (contract
  section 2.5, ledger R28-H29), unlike ordinary `-c` mode.
~~~~~

## B302: baseline lines 6490-6503

Moved from GENIA_STATE.md@d401f322, lines 6490-6503 (ledger row B302, moved, sha256 4366041e845e2e84)

~~~~~markdown
- Failure envelopes (no `result`, no partial value, stdout, or stderr; every message is a
  fixed server-owned string): `parse_error` (phase `parse`, character offset only),
  `policy_denied` (`policy`), `runtime_error` (`execution`, no Genia diagnostic text),
  `timeout` (`execution`, 5,000 ms), `cancelled` (`execution`), `result_limit`
  (`adapter`: a channel or the rendered value over 1,048,576 bytes, or the whole result
  over 3,276,800 bytes), and `internal_error` (`adapter`).
- Cancellation is honored: a `notifications/cancelled` message whose `params.requestId`
  equals the active request id, queued with the request or arriving during the run,
  terminates and reaps the worker and yields `cancelled`. The match is made in native
  `mcp.genia`; a cancel for another id, or after completion, is ignored; other lines that
  arrive during a run are answered in order afterwards.
- Every response is flushed as soon as it is written (previously it could be held in the
  stdout buffer until exit; ledger R28-H31).

~~~~~

## B303: baseline lines 6504-6518

Moved from GENIA_STATE.md@d401f322, lines 6504-6518 (ledger row B303, moved, sha256 0a990d0e5c81e80b)

~~~~~markdown
POLICY AND RUNTIME (each call, in a fresh worker):

- Pre-execution policy runs in the worker over the **raw parser AST** (Clarification A4);
  the shared normalized parse surface is unchanged. It rejects every `import`, shell stage
  `$(...)`, and any reference to an authority-bearing name (file, zip, resource, HTTP,
  server, external process, configuration, secret, declassification, model, retrieval,
  `input`, `stdin_keys`). It is conservative: a user definition reusing such a name is
  rejected too.
- The Genia environment is pruned by an explicit default-deny classification
  (`hosts/python/mcp_worker_profile.py`; a test fails if any binding or autoload is
  unclassified), `import` loading is denied, and process creation and socket use are
  stubbed at runtime (shell stages bypass bindings; ledger R28-H28). `argv()` is empty and
  `stdin` is immediate EOF; no environment, dotenv, configuration, or secret source exists.
- A protected-value carrier in the result is `policy_denied` with a fixed message.

~~~~~

## B304: baseline lines 6519-6538

Moved from GENIA_STATE.md@d401f322, lines 6519-6538 (ledger row B304, moved, sha256 972573f447b4370e)

~~~~~markdown
WORKER FLOOR (guaranteed on the Python reference host, POSIX):

- fresh process per call in its own process group; fixed minimal environment (no `PATH`,
  `HOME`, or user variable); private empty working directory removed after reap; only the
  three standard pipes inherited; source sent over the worker's stdin pipe; reply is one
  ASCII JSON line; process limits (`RLIMIT_FSIZE` 0, `CORE` 0, `CPU` 10 s, `NOFILE` 64,
  `AS` 2 GiB); channel limits enforced incrementally inside the worker; monotonic
  5,000 ms deadline that starts when the worker reports readiness (after its trusted
  bootstrap: interpreter start, imports, limits; before any source is evaluated), with bootstrap
  separately bounded at 30 s (a worker that never becomes ready is `internal_error`);
  forceful kill of the process group and reap on timeout,
  cancellation, overflow, or failure; worker stderr drained and discarded (only its one
  readiness marker is recognized).
- **Best effort, only if verified at runtime:** a user + network namespace
  (`unshare --user --map-root-user --net`), verified once during host initialization
  (before the server reads any request; bounded at 5 s and cached), so a request never runs
  a capability probe. When the probe fails or times out, workers run without it and nothing
  claims it; a hung `unshare` can only delay server startup by the probe bound. Some hosts
  (observed: GitHub-hosted Linux CI) deny unprivileged namespaces; workers then run without
  one, and the namespace-specific tests are skipped there.
~~~~~

## B305: baseline lines 6539-6554

Moved from GENIA_STATE.md@d401f322, lines 6539-6554 (ledger row B305, moved, sha256 148d738dfb8831b9)

~~~~~markdown
- **Not provided or claimed:** filesystem namespaces, seccomp, cgroup memory or CPU
  limits, a PID namespace, protection against interpreter or kernel defects, or isolation
  from other processes of the same user. This is a defense-in-depth profile, not a
  security sandbox and not production multi-tenant isolation.

PYTHON REFERENCE HOST (modules contain no MCP literals; enforced by tests):

- `hosts/python/mcp_run_capability.py` (supervisor), `hosts/python/mcp_worker.py` (worker),
  `hosts/python/mcp_worker_profile.py` (classification and policy), and
  `hosts/python/mcp_stdin.py` (raw stdin line multiplexer: transport framing only, splits
  on `\n`, back-pressure at 8 MiB). `hosts/python/mcp_host.py` provisions `parse` and
  `run` and feeds the multiplexer to the existing `stdin_provider` hook; native Genia
  still owns decoding, validation, dispatch, cancellation matching, limits, and envelopes.
- Validated by `tests/unit/test_r28_mcp_run.py`, `tests/unit/test_r28_mcp_run_worker.py`,
  `tests/unit/test_r28_mcp_run_supervisor.py`, and the existing R28 tests.

~~~~~

## B306: baseline lines 6555-6561

Moved from GENIA_STATE.md@d401f322, lines 6555-6561 (ledger row B306, moved, sha256 50c6e5d33015ebfe)

~~~~~markdown
Explicit limitations: the canonical debug renderer shows host representations for some
values (for example a builtin renders as a Python function representation with an
address; ledger R28-H32); while more than 8 MiB of client input is pending the server
stops reading and cannot observe a cancellation; a closed transport may prevent any
envelope; Windows is not supported; no resources or prompts, no C++ MCP support or parity
claim, and no VS Code or Copilot acceptance (the client configuration is section 9.44).

~~~~~

## B307: baseline lines 6562-6583

Moved from GENIA_STATE.md@d401f322, lines 6562-6583 (ledger row B307, moved, sha256 01b1948d5741ae47)

~~~~~markdown
## 9.44) R28 E28-4 local stdio client configuration and lifecycle (issue #705)

Implemented (Python reference host, POSIX only; verified on Linux only, R28-H43):

- Repository-root `.mcp.json` (portable `mcpServers` format) registers one stdio server `genia`:
  `uv run --no-project --no-python-downloads python hosts/python/mcp_launch.py`. No `env`, URL,
  token, or absolute path. Run it with the repository root as working directory and `git` and `uv`
  available. Guide: `docs/mcp/stdio-development.md`.
- A mainstream client discovers exactly `genia_capabilities`, `genia_parse`, `genia_run` (no resources
  or prompts) and enabling the configuration grants no authority beyond the E28-3 profile.
- Lifecycle plumbing (host only, no MCP semantics): the launcher forwards SIGTERM/SIGINT/SIGHUP to
  the host; the host unwinds on SIGTERM and SIGHUP (SIGINT unwinds as `KeyboardInterrupt`), reaping its
  worker and temp directory (SIGHUP handling added by E28-5, ledger R28-H41); the worker has an 8 s
  orphan backstop (`SIGALRM` armed after readiness; not a second deadline).
- Executed acceptance: the official MCP TypeScript client SDK `@modelcontextprotocol/client` 2.2.0
  (`tools/mcp_acceptance/`, CI job `mcp-client-acceptance`) with version negotiation `auto`.

Explicit limitations: Streamable HTTP is deferred (no listener); a client that only speaks the legacy
`initialize` handshake could not use the server when this section was written (R28-H36; superseded by
amendment A5, section 9.47); no VS Code or GitHub Copilot run had succeeded (R28-H39); a SIGKILLed host may leave an empty private temp directory; R28 was not yet complete when this section was written (the
E28-5 conformance evidence is section 9.45; the E28-6 demo and final audit are section 9.46; completion is section 9.49); no C++ MCP support or parity is claimed.

~~~~~

## B315: baseline lines 6672-6709

Moved from GENIA_STATE.md@d401f322, lines 6672-6709 (ledger row B315, moved, sha256 3552f31afb00109f)

~~~~~markdown
## 9.45) R28 E28-5 MCP conformance and parity matrix (issue #706)

Evidence phase; it adds no Genia syntax, builtin, Core IR node, MCP tool, resource, prompt, or
transport. The only behavior change is host lifecycle plumbing: the host now unwinds on SIGHUP like
SIGTERM, so the worker is reaped and its private directory removed (ledger R28-H41).

- **Matrix:** `docs/mcp/conformance-matrix.md` records, per behavior, the authority, direct Genia
  behavior, MCP behavior, expected relationship, evidence test, host limitation, and a status of
  PASS, KNOWN LIMITATION, or NOT APPLICABLE. `tests/unit/test_r28_mcp_conformance_matrix.py` fails if
  a cited test does not exist. Design: `docs/design/r28-e28-5-conformance-matrix-design.md`.
- **Adapter, not a second semantics path:** a 55-program corpus (literals, arithmetic, exact
  numerics, collections, functions, Outcomes, pipelines and Flow, program output) yields rendered
  value, stdout, and stderr identical to direct command-source evaluation (`run_source` with
  `filename="<command>"` and the canonical debug renderer). Intentional differences are
  classified, not hidden: `main` is not dispatched by MCP (contract 2.5; the CLI `-c` mode
  dispatches it, R28-H29); an authority available to direct execution is a policy restriction
  (`policy_denied`), not a semantic difference.
- **Verified boundaries:** exactly the three tools (four since amendment A6, section 9.50) and closed schemas; no resources, prompts, or
  other protocol surface; every failure class is the closed envelope with a fixed message and no
  partial data; limits are UTF-8 byte sizes (one below, exact, one above, including multibyte and
  the aggregate); 55 authority attempts plus every denied binding are rejected by static policy,
  absent after pruning, and unbound at runtime; a protected carrier injected into the real worker
  never appears in any response byte on any path; program output (JSON-RPC and cancellation
  lookalikes, Unicode separators) is data, never framing; cancellation, timeout, and lifecycle edge
  cases leave no worker; results are identical with the optional namespace granted or denied.
- **Official client:** the E28-4 harness (SDK 2.2.0, negotiation `auto`) also covers schemas,
  parse-repair-run, failing runs, authority denial, sequential calls, client-abort cancellation,
  disconnect, and relaunch.

Explicit limitations (unchanged or newly recorded): UTF-16 surrogate `\u` escapes in program
strings do not cross the JSON boundary unchanged (a pair becomes the scalar value, a lone surrogate is
`internal_error`; R28-H40); the debug renderer shows host text for callable values (R28-H32);
Unicode identifiers are not accepted by the parser; SDK-default clients that send `initialize`
could not connect when E28-5 was written (R28-H36; the VS Code run then showed an amendment was
required; section 9.47); no successful VS Code or Copilot run is recorded (R28-H39); Streamable HTTP is deferred and C++ MCP is not
supported; R28 was not yet complete when this section was written (E28-6 demo, publishing, and final audit: section 9.46; completion: section 9.49). Issue #1078 (the
spec-runner adapter timeout) is separate infrastructure work.

~~~~~

## B316: baseline lines 6710-6738

Moved from GENIA_STATE.md@d401f322, lines 6710-6738 (ledger row B316, moved, sha256 ea78a24a8c85ca3e)

~~~~~markdown
## 9.46) R28 E28-6 demo, publishing documentation, and release-candidate audit (issue #707)

Documentation, example, and entrypoint phase. It adds no Genia syntax, builtin, Core IR node, MCP tool,
resource, prompt, or transport. This section records the E28-6 release candidate as it stood then (R28 completed later: section 9.49).

- **Demo:** `docs/mcp/demo.md` walks a first-time user from `git clone` to parse, diagnose, repair, and run of
  an Outcome-aware validated record pipeline through the MCP server, using the ordinary Genia in
  `examples/mcp/` (tested by `tests/unit/test_r28_mcp_demo.py`).
- **Entrypoint:** `scripts/genia-mcp`, a POSIX shell script that takes no arguments, works from any
  directory, and starts the launcher the checked-in `.mcp.json` starts (`uv` or Python 3.10+). The `genia`
  CLI, `pyproject.toml`, and the wheel are unchanged; no package, registry, or container publication
  exists.
- **Reference and limits:** `docs/mcp/reference.md` (schemas, envelope, error kinds, limits),
  `docs/mcp/security-and-deployment.md` (a defense-in-depth profile, not a security sandbox and not
  production multi-tenant isolation), `docs/mcp/host-portability.md` (native Genia versus Python reference
  host; no C++ MCP implementation and no cross-host parity).
- **Clients:** the official TypeScript client is automated in CI; the official Inspector 2.9.0 CLI was run
  manually (not in CI); both default to the legacy `initialize` handshake, which the server serves since
  amendment A5 (section 9.47). VS Code with GitHub Copilot run 1 (2026-10-05) **failed at `initialize`**
  (R28-H39); the rerun then pending passed later (section 9.49); the procedure is `docs/mcp/vscode-copilot-acceptance.md`
  and the record is `docs/mcp/acceptance/vscode-copilot-evidence.md`.
- **Release gate:** `tests/unit/test_r28_release_gate.py` fails any document that claims R28 complete
  until the latest run in that record is executed, complete, and `PASS` with a negotiation path the amended
  contract allows (`initialize` with `2025-11-25`, or `server/discover` with `2026-07-28`).
- **Audit:** `docs/design/r28-e28-6-final-audit-plan.md` and the ledger disposition of every non-closed
  entry; new findings R28-H42 (a failed run returns no diagnostic text) and R28-H43 (evidence is Linux only).
- **Release page:** `docs/releases/R28.md` (Release Candidate at the time; Complete as of section 9.49). The R20 follow-up (#1067) remains scheduled
  after R28 and before R29; #1078 remains separate infrastructure work.

~~~~~

## B317: baseline lines 6739-6774

Moved from GENIA_STATE.md@d401f322, lines 6739-6774 (ledger row B317, moved, sha256 948613045b7eb710)

~~~~~markdown
## 9.47) R28 E28-6 amendment A5: the `2025-11-25` compatibility era (issue #707)

Trigger: the first authentic VS Code 1.138.0 + GitHub Copilot Chat 0.66.0 run (macOS, 2026-10-05) sent
`initialize` with `protocolVersion: "2025-11-25"`; the then stateless-only server answered `-32601` and no
tool was reached (ledger R28-H36, R28-H39). Contract amendment A5 (section 18 of
`docs/design/r28-genia-mcp-contract-threat-model.md`; pre-flight
`docs/design/r28-e28-6-protocol-compat-preflight.md`) adds one compatibility era. It adds no Genia syntax,
builtin, Core IR node, host capability, MCP tool, resource, prompt, transport, limit, or authority, and no
Python host code: it is entirely native Genia in `apps/mcp/mcp.genia`.

- **Closed policy:** exactly `2026-07-28` and `2025-11-25` are served. Era is selected per request: a request
  whose `params._meta` has `io.modelcontextprotocol/protocolVersion` is a `2026-07-28` request (unchanged);
  every other request is a `2025-11-25` request.
- **`initialize`:** params must be an object with string `protocolVersion`, object `capabilities`, and object
  `clientInfo` with string `name` and `version`. `protocolVersion` `2025-11-25` succeeds with exactly
  `{protocolVersion, capabilities: {tools: {}}, serverInfo: {name: "genia-mcp", version: <contract_revision>}}`;
  any other string is `-32602 Unsupported protocol version` with `data: {supported: ["2025-11-25"],
  requested}` (never negotiated down); malformed params are `-32602`; a second `initialize` is `-32600`; an
  id-less `initialize` is ignored; a failed `initialize` changes nothing.
- **State:** one process-local bit (a single `ref` cell; NEW then INITIALIZED), never persisted or shared.
  `tools/list` and `tools/call` before `initialize` are `-32602` (as before the amendment); `ping` is `{}` in
  every state; `notifications/initialized` is accepted silently and gates nothing; every other method
  (resources, prompts, completion, logging, tasks, roots, sampling, elicitation) is `-32601`.
- **Wire shape:** compat results omit `resultType`, `ttlMs`, `cacheScope`, and `_meta`; descriptors, order,
  envelope, messages, limits, cancellation, and policy are identical in both eras; `genia_capabilities`
  reports the serving revision in `mcp.protocol_version`.
- **Client capabilities grant nothing:** `roots`, `sampling`, `elicitation`, `tasks`, `extensions`, or any
  other value are shape-checked and discarded; the server never sends a request or a notification.
- **Evidence:** `tests/unit/test_r28_mcp_compat.py` (protocol, replaying VS Code's exact message),
  `tests/unit/test_r28_mcp_compat_conformance.py` (both-era conformance), matrix section K, and the official
  client scenario on the default, `auto`, legacy, and `2026-07-28`-pin paths (`docs/mcp/conformance-matrix.md`).
- **Not claimed:** VS Code's behavior after `initialize` (the `initialized` notification, when it lists tools,
  `ping`) rests on the SDK reference and run 1's trace; run 2 (pending; `docs/mcp/vscode-copilot-acceptance.md`)
  decided it (run 3 passed; section 9.49). When this section was written macOS evidence showed only that VS Code
  discovered `.mcp.json`, started the launcher, and spoke stdio JSON-RPC (R28-H43).

~~~~~

## B318: baseline lines 6775-6807

Moved from GENIA_STATE.md@d401f322, lines 6775-6807 (ledger row B318, retained-condensed, sha256 1d4b7aea4c6f41dd)

~~~~~markdown
## 9.48) R28 E28-6 macOS portability of the governed `genia_run` profile (issue #707, ledger R28-H47)
<!-- anchor: state:mcp-macos -->

Trigger: authentic VS Code run 2 on macOS (Darwin x64 24.6.0, 2026-10-05, revision `66b50594`) proved amendment A5
(negotiation, three tools, `genia_capabilities`, both `genia_parse` calls) but `genia_run` returned the sanitized
`internal_error`; `tests/unit/test_r28_mcp_run.py` gave 53 failed, 17 passed, 3 skipped there. Pre-flight:
`docs/design/r28-e28-6-macos-execution-preflight.md`. No Genia syntax, builtin, Core IR node, MCP tool, resource,
prompt, protocol, authority, limit, parse behavior, or envelope changed.

- **Worker limits are platform-aware.** `hosts/python/mcp_worker.py` `apply_limits()` applies `RLIMIT_FSIZE` 0,
  `CORE` 0, `CPU` 10 s, `NOFILE` 64 on every platform, and `RLIMIT_AS` 2 GiB on every platform; any failure is
  `internal_error` (the worker never runs without them). The single exception: on Darwin a rejected
  `RLIMIT_AS` is tolerated (the kernel rejects an address-space bound below the process's current virtual size).
  Linux behavior is unchanged. One execution model, same envelopes, on every platform.
- **macOS has a weaker resource bound and no namespace.** There is no address-space bound on macOS, so memory is
  bounded only by the 5,000 ms deadline and the 10 s CPU limit; there is no network namespace (Linux-only); the
  network, file, process, and import denial rests on the static policy, the pruned environment, and the runtime
  stubs. No namespace or sandbox is claimed on macOS.
- **Root cause (confirmed on macOS):** Darwin rejects `setrlimit(RLIMIT_AS)` with `ValueError: current limit exceeds
  maximum limit`; `tools/mcp_diagnostics/worker_probe.py` printed `VERDICT OK` and `genia_run` works there (64 of
  73 `test_r28_mcp_run.py` tests pass; development-only worker diagnostic `GENIA_MCP_WORKER_DIAG=1`, on the worker's
  own stderr, never forwarded, never on the wire). The 5 remaining failures were test-observation only (the `ps`
  backend did not recognise the governed worker: macOS names the interpreter `Python`; `ps` needs `-ww`);
  repaired and Mac-verified (`tools/mcp_diagnostics/process_probe.py` `VERDICT OK`; the 5 tests pass; the cause was
  macOS's interpreter name `Python`; `-ww` was not needed here).
- **Tests:** `tests/unit/test_r28_mcp_portability.py` (simulated Darwin rejection, fail-closed rules, wire
  regression, diagnostic hygiene, probe, `ps`/`lsof` process backend); the lifecycle helpers use `/proc` on Linux
  and `ps`/`lsof` where there is no `/proc`; Linux-only namespace tests are skipped elsewhere with a stated reason.
- **Full macOS suite run (owner, `44ec62cd`): 1135 passed, 18 skipped, 3 failed**, all test assumptions or platform facts (ledger R28-H48): the namespace-probe test assumed Linux; macOS injects `__CF_USER_TEXT_ENCODING` into every process (the supervisor does not pass it); plain file mode (a development path) reads stdin through the locale-dependent interpreter decoder, which is `strict` on macOS (the launcher path decodes with `surrogateescape` itself and is unaffected). Repaired in tests; the full macOS R28/MCP suite then passed at `d0e4f2a4` (**1141 passed, 18 skipped, 0 failed**).
- **Outcome:** macOS governed execution is Mac-verified (owner: full R28/MCP suite `1141 passed, 18 skipped, 0 failed`
  at `d0e4f2a4`) and authentic VS Code run 3 passed (section 9.49). macOS still has no address-space bound and no network
  namespace (Linux-only; Linux-only namespace tests skip on macOS). R28-H47 and R28-H48 are closed; R28-H36 was closed by run 2.

~~~~~

## B319: baseline lines 6808-6839

Moved from GENIA_STATE.md@d401f322, lines 6808-6839 (ledger row B319, retained-condensed, sha256 d6a641ae679d7a3d)

~~~~~markdown
## 9.49) R28 completion: authentic VS Code + GitHub Copilot acceptance (issue #707, epic #700)
<!-- anchor: state:mcp-surface -->

R28 (Genia MCP Server) is **Complete**: contract section 12.2 is satisfied by an authentic VS Code + GitHub Copilot
run. The evidence record is `docs/mcp/acceptance/vscode-copilot-evidence.md`; the release page is `docs/releases/R28.md`.
This section adds no Genia syntax, builtin, Core IR node, MCP tool, resource, prompt, transport, protocol, authority, limit,
or envelope.

- **Run 3 (PASS), revision `0ff058a28e488275f344ee24bbd12d072bd3e9cc`, macOS, VS Code 1.138.0, Copilot Chat 0.66.0:**
  VS Code started the repository-configured `genia` server (`.mcp.json`, `initialize` for `2025-11-25`) and reported
  `Discovered 3 tools`; `genia_capabilities` returned protocol `2025-11-25`, transport `stdio`, exactly `genia_capabilities`,
  `genia_parse`, `genia_run`, profile `source-only-isolated-v1`, timeout 5000 ms, and every authority flag `false`; the
  broken canonical demo through `genia_parse` gave `parse_error` (phase `parse`) at character offset 171; the corrected
  demo parsed (`parsed`, AST returned); through Copilot Agent `genia_run` returned `ok`/`completed`, exit code 0, stdout
  `"2\n"`, stderr `"record_validation_failed\nrecord_validation_failed\n"`, and a rendered value with the clean records Ada
  and Edsger and the two structured validation diagnostics, with value, stdout, and stderr separate; after the server
  stopped no `mcp_launch`, `mcp_host`, or `mcp_worker` process remained. `resources_or_prompts_visible: none` rests on the
  server's advertised `capabilities: {tools: {}}`, automated `-32601` for resources and prompts, and VS Code's report of exactly
  three discovered tools, not on a separately reported UI inspection (stated in the evidence file).
- **History is preserved:** run 1 failed at `initialize` (fixed by contract amendment A5, section 9.47); run 2 failed at
  `genia_run` on macOS (fixed by ledger R28-H47, section 9.48). The release gate (`tests/unit/test_r28_release_gate.py`) reads the
  latest run: executed, complete, `PASS`, on a negotiation path the amended contract allows.
- **Ledger:** R28-H36, H39, H45, H47, H48 and the accepted-limitation entries are closed; the post-R28 follow-up candidates
  (H05-H09, H15, H24, H26) stay open in the ledger and the parking lot, not ticketed. R20 follow-up #1067 stays after R28 and
  before R29; #1078 is separate infrastructure work.
- **Agent guidance (contract 12.3):** `docs/ai/LLM_CONTRACT.md` and `.github/copilot-instructions.md` direct Genia development
  agents to prefer the Genia MCP server for parsing and running Genia source where an MCP client is available; they add no
  language semantics and do not make MCP a prerequisite.
- **Supported platforms and limits:** Python reference host only; local stdio only; exactly four tools (the fourth, `genia_language_profile`, is section 9.50; acceptance runs saw three); no resources, prompts,
  Streamable HTTP, or C++ MCP; Linux (CI) and macOS (owner-run, not in CI) verified, Windows unsupported; macOS has no address-space
  bound and no network namespace; the execution profile is a defense-in-depth profile, not a security sandbox.

~~~~~

## B320: baseline lines 6840-6874

Moved from GENIA_STATE.md@d401f322, lines 6840-6874 (ledger row B320, retained-condensed, sha256 2ffb8b4e4d9b0395)

~~~~~markdown
## 9.50) R28 follow-up amendment A6: `genia_language_profile` (MCP adapter affordance)
<!-- anchor: state:mcp-language-profile -->

Contract amendment A6 (section 19 of `docs/design/r28-genia-mcp-contract-threat-model.md`; pre-flight
`docs/design/r28-a6-language-profile-preflight.md`) adds one MCP tool to the R28 server. It adds no Genia syntax, parser or
evaluator behavior, builtin, Core IR node, host capability, resource, prompt, transport, limit, or authority, and no Python
host code: the tool is entirely native Genia in `apps/mcp/mcp.genia`. It is an adapter affordance for assistants, not
language behavior; this file and `GENIA_RULES.md` remain the language authority. Python reference host only; no C++ MCP.

LANGUAGE CONTRACT: none. The MCP wire behavior below is the application contract of `apps/mcp/mcp.genia`.

PYTHON REFERENCE HOST (MCP adapter):

- The advertised surface is exactly four tools, in this order: `genia_capabilities`, `genia_parse`, `genia_run`,
  `genia_language_profile`. `genia_language_profile` needs no host capability, so plain file mode (no host capability) advertises
  `genia_capabilities` and `genia_language_profile`; the launcher advertises all four. `genia_capabilities.tools` reports the advertised
  set. No resources, prompts, pagination, or other protocol surface is added.
- It takes no arguments: `arguments` omitted or `{}` is accepted and any other value is `-32602`. The input schema is identical to
  `genia_capabilities`. It returns the normal `CallToolResult` with `structuredContent` and one text item holding the same
  `genia.mcp.v1` envelope (`result = {language: {...}}`).
- `language` is a fixed constant except `contract_revision` (the launch revision `genia_capabilities` reports). It states:
  `control_flow` (`conditionals: "pattern_matching"`, `if_expression: false`, `loops: false`, `recursion: true`,
  `tail_call_optimization: true`), `supported_forms`, `absent_forms` (`if_expression`, `while_loop`, `for_loop`), `patterns`
  (function-argument, literal, wildcard, tuple, list, map, and guard patterns; first-match resolution), `idioms`, and two `examples`
  (`gcd`, `factorial`). Each claim restates implemented behavior of sections 5 and 8 and the open-function clause rules; the example
  programs evaluate to `6` and `120` under direct command-source evaluation (verified by tests).
- **Example spelling:** a function whose clauses start with a literal parameter pattern needs the first clause declared `open`
  (`open gcd(a, 0) = a`); the same text without `open` is rejected (`Invalid function definition parameter token`). The profile therefore
  carries the `open` form and states that rule in `idioms.clauses`.
- Output is byte-identical across calls, protocol eras, and namespace modes; JSON member order is the encoder's sorted order.
- **Evidence:** `tests/unit/test_r28_mcp_language_profile.py` plus the updated four-tool discovery, descriptor, and architecture
  tests; matrix rows D1, D5, D6, D9 in `docs/mcp/conformance-matrix.md`.
- **Not claimed / not done:** no source-specific parse or run diagnostic hints; the VS Code + GitHub Copilot acceptance record
  (runs 1-3) predates this tool and describes the three-tool surface, and no new authentic client run is recorded for the fourth.

~~~~~

## B321: baseline lines 6875-6928

Moved from GENIA_STATE.md@d401f322, lines 6875-6928 (ledger row B321, retained-condensed, sha256 a28df6871f9f032a)

~~~~~markdown
### R28 follow-up amendment A7: scoped maturity/gap facts (issue #1086)

LANGUAGE CONTRACT: unchanged. This extends MCP adapter metadata only.

PYTHON REFERENCE HOST (MCP adapter): `genia_language_profile` now adds
`language.discovery`, exactly `{coverage, facts}`. `coverage` is
`"curated_non_exhaustive"`; `facts` is the fixed ordered 12-row catalogue below.
Each row has exactly `{id, scope, status, maturity, summary, state_sections}`.
Summaries and the closed value sets are specified in application contract
amendment A7 (section 20); section identifiers are strings in ordered arrays
referencing this file at the launch revision. No live discovery occurs.

| ID | Scope | Status | Maturity | STATE sections |
|---|---|---|---|---|
| pattern_branching | language | implemented | null | 5 |
| tail_calls | language | implemented | null | 8 |
| if_and_loops | language | unsupported | null | 5, 9.50 |
| flow_shared_coverage | shared_conformance | partial | Experimental | 0, 1 |
| core_ir_stability | shared_conformance | partial | Partial | 0 |
| cpp_language_floor | cpp_host | partial | null | 0 |
| other_language_hosts | other_hosts | planned | null | 0 |
| browser_runtime | browser | scaffolded | null | 0.1 |
| mcp_surface | mcp | implemented | null | 9.49, 9.50 |
| cpp_mcp | mcp | unsupported | null | 9.49, 9.50 |
| windows_mcp | mcp_windows | unsupported | null | 9.49 |
| macos_hardening | mcp_macos | partial | null | 9.48, 9.49 |

Status describes support within the row's scope; maturity copies an explicit
STATE rating or is JSON null for unspecified. Null does not mean Stable or
unavailable. Partial C++ support is the bounded R27 language floor, not C++
MCP; partial Flow shared coverage does not mean missing Python Flow behavior.
Browser scaffolding is documentation only. macOS hardening is bounded as in
9.48; no security sandbox is claimed. These facts grant no execution authority
and are not an exhaustive language/host inventory.

The profile constants (`control_flow`, `supported_forms`, `patterns`, `absent_forms`,
`idioms`, and `discovery`) are generated into a delimited block of
`apps/mcp/mcp.genia` from the `mcp_language_profile` registry in
`docs/contract/semantic_facts.json`, a guarded projection source: this file stays the
authority, and each registry fact carries semantic anchors (`<!-- anchor: state:... -->`
markers in this file) and evidence (STATE text, executable probes, or manifest
cross-checks). `state_sections` values keep their legacy section numbers through the
registry's anchor crosswalk, so the wire output is unchanged. The server never reads
the registry at runtime. Its JSON is
bounded to 16,384 UTF-8 bytes with summaries at most 256 bytes each; these are
static output bounds, not new runtime limits. Output remains deterministic
across calls, protocol eras, namespace modes, and plain file mode. Existing
profile members/examples, launch revision, arguments, four-tool surface,
`genia_capabilities`, envelopes, authority, and host behavior are unchanged.
Evidence: `tests/unit/test_r28_mcp_language_profile.py`,
`tests/unit/test_r28_mcp_language_registry.py`,
`tests/doc/test_state_anchors_and_registry_sync.py`; matrix row D10. No
new authentic client acceptance run is claimed; runs 1–3 predate A6 and A7.

~~~~~

## B322: baseline lines 6929-6960

Moved from GENIA_STATE.md@d401f322, lines 6929-6960 (ledger row B322, retained-condensed, sha256 0f34684004cfb899)

~~~~~markdown
## 9.51) R28 follow-up: MCP grounded-evidence example (issue #1087)

LANGUAGE CONTRACT: unchanged. This is one checked-in example program and tests,
not a new Genia feature.

PYTHON REFERENCE HOST (MCP example): `examples/mcp/grounded_evidence.genia`
runs through the existing `genia_run` tool. It validates client-supplied
document literals, chunks valid documents with Experimental R12 `chunk/2`, and
prints one strict JSON evidence package on stdout. The package includes the
question, retained validated input documents, selected evidence with exact
`chunk/2` source spans, first-occurrence sources, indexed diagnostics, and a
selection descriptor whose claim is
`ordinary_example_selection_not_r12_retrieve`.

The example uses only ordinary Genia plus existing public helpers. It adds no
MCP tool, resource, prompt, transport, authority, builtin, parser/evaluator
behavior, Core IR node, provider, or host capability. It is Python-reference-host
MCP behavior only; no C++ MCP or cross-host parity is claimed.

The selection step is a deterministic example-local exact-term overlap over the
checked-in source literals. It is not R12 `retrieve/4`, semantic retrieval,
embedding, reranking, RAG, citation validation, answer generation, or evidence
authenticity. Answer generation remains outside Genia with the MCP client.
Document ids and metadata are client-asserted labels; the example preserves
supplied spans and diagnostics but does not verify origin or trust.

Evidence: `tests/unit/test_r28_mcp_grounded_evidence_example.py` exercises the
program through real MCP `genia_run`, direct CLI execution, deterministic stdout
JSON, Unicode code-point provenance, invalid/duplicate/zero-chunk diagnostics,
input limit behavior, prompt-like text as inert data, and static denial of
imports, private underscore host functions, and denied names.

~~~~~
