# Genia MCP server over local stdio (development guide)

Status: R28 E28-4 (issue #705), conformance evidence in E28-5 (`docs/mcp/conformance-matrix.md`); public walkthrough `docs/mcp/demo.md`, reference `docs/mcp/reference.md`, limits `docs/mcp/security-and-deployment.md`. `GENIA_STATE.md` is the final authority. This is a local
development tool for trusted stdio clients: it is **not a security sandbox**.

## What you get

The repository-root `.mcp.json` registers one server, `genia`, started over stdio:

```text
uv run --no-project --no-python-downloads python hosts/python/mcp_launch.py
```

The client discovers exactly three tools: `genia_capabilities`, `genia_parse`, `genia_run`.
There are no resources and no prompts. Enabling the server grants no extra authority: execution
uses the E28-3 worker profile and policy only, and the file holds no environment, token, URL, or
secret.

## Prerequisites

- A git clone (the launcher passes `git rev-parse HEAD` as the contract revision; without `.git`
  or `git` it fails closed with one stderr line).
- `uv` on `PATH` and a Python 3.10+ interpreter `uv` can find. Nothing is installed or downloaded
  at launch.
- POSIX. Linux (CI) and macOS (owner-run, not in CI) are verified, including an authentic VS Code + GitHub Copilot run on macOS; macOS has no address-space bound and no network namespace (ledger R28-H47); Windows is not supported.
- The client must start that command with the repository root as working directory, or use `scripts/genia-mcp` (no arguments), which works from any directory and starts the same launcher.

## Use

1. Open the repository folder as the workspace and trust it (the file is executable
   configuration; review it like code).
2. Start or enable the `genia` server in your client (VS Code: the MCP servers view).
3. Confirm exactly three tools, then call `genia_parse` on source and `genia_run` to execute it.
   `genia_run` returns value, stdout, stderr, and exit code separately.

## Limits and troubleshooting

- **Streamable HTTP is deferred.** Only local stdio exists; there is no listener.
- **Two protocol eras, one server (amendment A5).** The server speaks exactly `2026-07-28` (stateless,
  per-request `_meta`, `server/discover`) and `2025-11-25` (selected by `initialize`). Clients that send
  `initialize` for `2025-11-25` (VS Code, the official TypeScript client's default) connect; `auto` and a
  pin of `2026-07-28` still connect. Any other `initialize` version is rejected with `-32602` and a
  `data.supported` list; the server never negotiates down. Both eras serve the same three tools. Client
  capabilities (roots, sampling, elicitation, tasks, extensions) are accepted and ignored: they grant
  nothing. The first VS Code run failed because this server then had no `initialize` (ledger R28-H36);
  authentic VS Code acceptance run 3 (macOS) completed the whole flow: negotiation, three tools, parse, and run (ledger R28-H39).
- Startup takes about 0.5 s; wait for the first response.
- `uv` or `git` missing, or a wrong working directory, makes the server fail to start; the client
  shows the launcher's stderr line.
- Server stderr appears in the client's MCP output log; stdout carries only JSON-RPC frames.
- Stdin EOF lets an in-flight run finish then exits; SIGTERM and SIGHUP (and SIGINT) stop the whole
  chain; a SIGKILLed host leaves at most an orphan worker for 8 s and possibly an empty private temp
  directory.

## Acceptance

Automated: `tools/mcp_acceptance/` runs the official MCP TypeScript client against the command
read from `.mcp.json` (`node acceptance.mjs`; `node negotiation.mjs` records how each negotiation
mode behaves). The full evidence matrix is `docs/mcp/conformance-matrix.md`; run the whole R28 suite
as on a host that denies unprivileged namespaces with `GENIA_R28_TEST_DENY_NAMESPACE=1`.

A VS Code / GitHub Copilot run cannot be executed in the CI or cloud environment; the recorded acceptance run is manual
(owner, macOS: run 3 passed; ledger R28-H39), and we do not claim it as automated or CI evidence, nor claim Windows, HTTP, or
multi-tenant use. The exact procedure and the record format are `docs/mcp/vscode-copilot-acceptance.md` and
`docs/mcp/acceptance/vscode-copilot-evidence.md`; the summary:

1. Record the VS Code version and the Copilot extension version.
2. Open the repository folder as the workspace and trust it; start the `genia` server from the MCP
   servers view.
3. Record whether the server shows as running (otherwise copy the launcher's stderr line from the
   MCP output log).
4. Confirm exactly three tools: `genia_capabilities`, `genia_parse`, `genia_run`.
5. From the host, ask for a `genia_parse` of `f(x) = x +` (a diagnostic), then of `f(x) = x + 1\nf(41)`,
   then a `genia_run` of that program (rendered value `42`). Record the exchange.
6. In the MCP output log, record whether the host sent `initialize` or `server/discover` and the negotiated protocol version.
