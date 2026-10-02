# Genia MCP server over local stdio (development guide)

Status: R28 E28-4 (issue #705). `GENIA_STATE.md` is the final authority. This is a local
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
- POSIX (Linux or macOS). Windows is not supported.
- The client must start the command with the repository root as working directory.

## Use

1. Open the repository folder as the workspace and trust it (the file is executable
   configuration; review it like code).
2. Start or enable the `genia` server in your client (VS Code: the MCP servers view).
3. Confirm exactly three tools, then call `genia_parse` on source and `genia_run` to execute it.
   `genia_run` returns value, stdout, stderr, and exit code separately.

## Limits and troubleshooting

- **Streamable HTTP is deferred.** Only local stdio exists; there is no listener.
- **Stateless protocol (2026-07-28):** the server has no `initialize`. A client that only speaks
  the legacy `initialize` handshake gets `Method not found` and cannot use the server (the official
  TypeScript client v2 must use version negotiation `auto`). Supporting it needs a contract
  amendment (ledger R28-H36).
- Startup takes about 0.5 s; wait for the first response.
- `uv` or `git` missing, or a wrong working directory, makes the server fail to start; the client
  shows the launcher's stderr line.
- Server stderr appears in the client's MCP output log; stdout carries only JSON-RPC frames.
- Stdin EOF lets an in-flight run finish then exits; SIGTERM stops the whole chain; a SIGKILLed
  host leaves at most an orphan worker for 8 s and possibly an empty private temp directory.

## Acceptance

Automated: `tools/mcp_acceptance/` runs the official MCP TypeScript client against the command
read from `.mcp.json`. A VS Code / GitHub Copilot run cannot be executed in the CI environment: we
do not claim one (ledger R28-H39). Manual procedure: do steps 1-3 above and record the tool list
and a parse-then-run exchange.
