# R28 E28-4 — Local stdio transport and client configuration: Design

Status: **Design (decisions below); nothing here is implemented until the implementation phase.**
`GENIA_STATE.md` remains final authority (E28-1: 9.41, E28-2: 9.42, E28-3: 9.43). Governing
contract: `docs/design/r28-genia-mcp-contract-threat-model.md` sections 7, 7.1, 9.3, 12 (this design
references the contract and E28-3 design; it does not restate them). Issue #705.
Pre-flight: `docs/analysis/r28-e28-4-stdio-preflight.md`. Findings: ledger
`docs/analysis/r28-host-dependency-inventory.md` (cited `[H##]`).

## 1. Decisions

| # | Decision | Basis |
|---|---|---|
| T1 | **stdio is the only R28 v1 transport.** Streamable HTTP, legacy HTTP+SSE, and any listener stay out and are not enabled by any option. | Contract 7 and 9.3; roadmap "deferred from R28 v1" (no contradiction) |
| T2 | The checked-in client configuration is **one repository-root `.mcp.json`** (portable format). `.vscode/mcp.json` is not added and nothing is duplicated. | Contract 12.1 prefers `.mcp.json`; VS Code documentation source states VS Code supports a workspace-root portable `.mcp.json` (`mcpServers`) that "works across compatible tools" (pre-flight section 3) |
| T3 | The server entry starts the **existing** launcher with `uv run --no-project --no-python-downloads python hosts/python/mcp_launch.py`. | Section 3 |
| T4 | Lifecycle hardening is host/OS plumbing only: the launcher forwards termination signals, the host reaps its worker on SIGTERM, and the worker has an orphan backstop. No MCP semantics move out of `mcp.genia`. | Section 6 (measured red evidence) |
| T5 | Real-client acceptance uses the **official MCP TypeScript client SDK v2** through a small pinned harness; a VS Code/Copilot run is a documented manual procedure and is **not** claimed as executed. | Section 8 |
| T6 | Not changed: tool surface, schemas, envelopes, cancellation matching, policy, limits, the stateless 2026-07-28 protocol (no `initialize`). | Contract 2, 5, 7.1 |

## 2. Architecture (unchanged shape)

```text
MCP client --stdio--> uv (wrapper) -> hosts/python/mcp_launch.py -> hosts/python/mcp_host.py
                                                                     -> apps/mcp/mcp.genia
                                                                     -> disposable worker (E28-3)
```

`uv` is a wrapper process that stays alive (measured), so the chain is up to four processes deep.
Every layer inherits the same stdin/stdout/stderr descriptors from the client, so end of input
reaches the host directly.

## 3. Startup command, working directory, identity

- **Exact entry:** `{"command": "uv", "args": ["run", "--no-project", "--no-python-downloads",
  "python", "hosts/python/mcp_launch.py"]}`, `"type": "stdio"`, server name `genia`.
- **Why `uv`:** it is the repository's documented tool (`AGENTS.md`; `.vscode/launch.json` already
  uses `uv`; CI installs it), has the same name on every OS (`python` versus `python3` versus `py`
  does not), and resolves the interpreter. `--no-project` means no project sync, no `.venv`
  creation, and no network access at launch. `--no-python-downloads` forbids fetching an
  interpreter. Nothing is installed or acquired when a client starts the server.
- **Fallback (not committed):** where `uv` is absent, replace the command with a Python 3.10+
  interpreter and the same script argument.
- **Working directory:** the script argument is repository-relative, so the client must start the
  command with the repository root as its working directory (VS Code documents the workspace folder
  as the default working directory for its own format; the portable format is not documented to
  differ). The launcher itself computes repository paths from its own file location, never from the
  working directory, so everything after launch is directory-independent.
- **Identity:** the launcher resolves `git rev-parse HEAD` (ambient `GIT_*` ignored) and passes it as
  the single program argument (E28-1/H10). A checkout without `.git` or without `git` on `PATH`
  fails closed with one fixed stderr line and a nonzero exit. This is a documented prerequisite.
- **No configuration inputs:** the file has no `env`, `envFile`, `inputs`, `cwd`, `url`, or token.

## 4. Startup, readiness, framing, stream ownership

- **Readiness:** there is no separate signal. The server is ready when it answers `server/discover`
  (E28-1). Host initialization, including the bounded isolation probe (H33), completes before the
  first request is read. Startup takes about 0.5 s; clients must wait for the first response.
- **Repeated launches:** a client may launch the server more than once per connection (the official
  v2 client in `auto` mode starts a `server/discover` probe process and then the session process).
  Each launch is independent and stateless (contract 7.1); no state is shared between launches.
- **stdout ownership:** stdout carries only newline-delimited JSON-RPC messages, one per line, each
  flushed when written (H31). The wrapper, launcher, host, and worker write nothing else to stdout;
  program output is data inside a response, never a frame.
- **stderr ownership:** stderr carries only fixed launcher and host diagnostics (and `uv`
  diagnostics). Program stderr is captured into the result and the worker's own stderr is discarded.
  Nothing a program writes reaches either process stream.
- **Framing:** unchanged from contract 7.1 (`\n`-delimited, no embedded newlines).

## 5. Environment, configuration, secrets, authority

The client's environment reaches `uv` and the launcher. The launcher passes the host only a fixed
allowlist, and the supervisor passes the worker a smaller fixed allowlist (E28-1, E28-3): no `HOME`,
no user variables, no `PATH` inside the worker. Enabling the client configuration adds no Genia
authority: the worker profile and policy of E28-3 are the only execution surface, and no provider,
`.env`, secret, or network capability is provisioned. The configuration file contains no value that
could carry a credential.

## 6. Shutdown, disconnect, and cancellation

Measured on the E28-3 code (red evidence, section 9):

| Event | Current behavior | Required behavior (this phase) |
|---|---|---|
| stdin closed while idle | clean exit 0 in about 0.06 s | unchanged |
| stdin closed (and stdout closed) mid-run | run finishes, then host and worker are gone | unchanged: a run in flight completes within its deadline, then the server exits |
| SIGTERM/SIGINT/SIGHUP to the launcher mid-run | launcher dies; host and worker keep running as orphans | the launcher forwards the signal to the host, waits for it, and exits with the host's status |
| SIGTERM to the host mid-run | host dies at once; the worker survives at least 25 s; its private temp directory leaks | the host handles SIGTERM by unwinding: the supervisor kills the worker's process group, reaps it, and removes the temp directory, then the host exits |
| SIGKILL to the host mid-run | the worker survives at least 25 s | the worker terminates itself within a fixed bound (orphan backstop) |
| cancellation | E28-3 (native match, supervisor terminates and reaps) | unchanged |

**Orphan backstop.** After it reports readiness, the worker arms a one-shot `SIGALRM` (default
action: terminate) for `ORPHAN_BACKSTOP_SECONDS = 8`. This is not a second deadline: the supervisor
kills the worker at 5 s, so a healthy run never reaches it. It bounds only a worker whose host died
without being able to clean up (SIGKILL). It is portable POSIX, and Genia code cannot install a
handler. A SIGKILLed host can leave its empty private temp directory behind; that is documented.

**Client escalation order.** A stdio client closes stdin, waits, then sends SIGTERM, then SIGKILL;
each step above is bounded: EOF drains the in-flight request (at most its deadline), SIGTERM reaps
immediately, SIGKILL leaves at most the backstop.

## 7. Developer workflow (documented, not duplicated here)

Prerequisites: a clone with `git`; `uv` on `PATH`; a Python 3.10+ interpreter `uv` can find; POSIX
(Linux or macOS). Steps: open the repository folder as the workspace, trust it, start or enable the
`genia` server (VS Code: MCP servers view; other clients per their documentation), confirm exactly
three tools, then use `genia_parse` and `genia_run`. Troubleshooting covers a missing `uv`/`git`, a
wrong working directory, a client that only speaks the legacy `initialize` handshake, and where to
read the server output. The full text lives in `docs/mcp/stdio-development.md` after implementation.

## 8. Acceptance clients

- **Executed, automated:** the official TypeScript client SDK `@modelcontextprotocol/client` 2.2.0
  (pinned by lockfile in `tools/mcp_acceptance/`) launching the command read from `.mcp.json`, with
  the SDK's restricted default child environment. One deterministic scenario: discovery (exactly
  three tools, no resources, no prompts), `genia_capabilities`, `genia_parse` on invalid source (a
  structured failure), the corrected source (success), `genia_run` showing value, stdout, stderr and
  exit code distinct, hostile program output that cannot corrupt framing, and denied authority.
  Version negotiation must be `auto` (or a pin): the SDK default `legacy` mode sends `initialize`,
  which this contract-mandated stateless server rejects (see risk R1).
- **Not executed here:** VS Code/GitHub Copilot. It cannot run in this environment, and the fetched
  VS Code documentation does not state its protocol versions. The manual procedure and the evidence
  record required by contract 12.2 are documented, and the claim stays "configuration format
  verified against VS Code documentation; no VS Code run recorded".
- **Risk R1 (recorded, not fixed):** a client that defaults to the legacy `initialize` handshake
  cannot use this server. Supporting it is a contract amendment (contract 7), outside E28-4.

## 9. Test strategy

Red first (all must fail for the missing E28-4 capability, with no sleeps): configuration checks
(`.mcp.json` exists, exact shape, no secret or absolute path or `env` or URL, no second
configuration file); launching the exact configured command with the repository root as working
directory and a minimal environment (every stdout line is JSON-RPC; exactly three tools; no
resources or prompts; parse, repair, run; framing; authority); lifecycle (launcher signal
forwarding, host SIGTERM reaping and temp-directory removal, host SIGKILL worker backstop, EOF
mid-run, stdout closed mid-run); the worker backstop in isolation; no listener or HTTP option; the
official-SDK acceptance scenario (skipped locally without Node, required in its CI job).
Synchronization uses the E28-3 helpers (readiness barrier, bounded observable polling, strict reap
checks), never fixed sleeps. Namespaces stay best effort and are not an E28-4 requirement.

## 10. Platform and security limitations

POSIX only (process groups, signals). Streamable HTTP is not available. The server is a local
development tool for trusted stdio clients: not a security sandbox and not a multi-tenant service
(contract 9.3). A client runs the configured command, so the usual workspace-trust prompt applies and
the file must be reviewed like any executable configuration. No C++ MCP support or parity is claimed.

## 11. Out of scope

HTTP transports, resources, prompts, additional tools, new Genia syntax or builtins, a Python MCP
SDK, legacy-handshake support, E28-5 (conformance matrix), E28-6 (demo, publishing, final audit),
and issue #1078 (spec-runner timeout).
