# Genia MCP host-portability statement (R28)

Status: **Release candidate.** `GENIA_STATE.md` is the final authority. R28 delivers MCP on **one host: the
Python reference host**. It does **not** prove that MCP is portable across hosts, and there is **no C++ MCP
implementation and no cross-host MCP parity claim**.

## Native Genia responsibility (`apps/mcp/mcp.genia`)

The MCP application is a Genia program. It owns: newline-delimited JSON-RPC handling and the protocol
revision rules, including the two-era policy (`2026-07-28` and `2025-11-25`), the `initialize` handshake,
the one-bit initialization state (a single `ref` cell in the program), and `ping`; request and `_meta`
validation; the tool schemas and discovery results; tool dispatch;
result-envelope composition and the fixed error messages; the source byte limit and the aggregate result
limit; cancellation matching (which notification cancels which request); and the result policy decisions
that native code owns. The host does not construct protocol messages, tool names, or envelopes (tests scan
the host modules for MCP literals; amendment A5 added no host code: `initialize`, `ping`, protocol-version
strings and client-capability handling appear in no Python module).

## Python reference-host responsibility (`hosts/python/`)

Capabilities handed to the Genia program as an explicit argument, never as ambient bindings:

- parser and evaluator access (the Genia source cannot reach the parser; one capability returns the
  normalized parse output as JSON text);
- worker process supervision: spawn, process groups, hard kill and reap, the deadline, incremental byte caps,
  private working directory, fixed environment, operating-system resource limits;
- raw stdin line multiplexing (so a cancellation can be observed during a run);
- the worker's restricted environment and static policy over the raw parser AST;
- best-effort namespace isolation, where verified;
- host bootstrap (loading the program in-process and providing the repository revision).

These are listed as host-dependency ledger entries (`docs/analysis/r28-host-dependency-inventory.md`);
each records what could disappear if Genia gained a general facility. None of them is promoted to a
language feature by R28.

## Not implemented

- C++ MCP support, and any statement that the same `mcp.genia` runs over another host's capability boundary.
- Cross-host MCP conformance or parity evidence.
- Windows host support. macOS is unverified: the governed worker's process limits are platform-aware (ledger R28-H47) but no macOS run has passed yet.
- Streamable HTTP, MCP resources, MCP prompts, an MCP client inside Genia, an agent framework.

The architecture keeps host code narrow so that a later host could provide the same capabilities, but R28
does not demonstrate it.
