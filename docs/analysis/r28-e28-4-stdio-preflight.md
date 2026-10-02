# R28 E28-4 — Pre-flight and reconciliation (stdio transport and client configuration)

Status: **Pre-flight record for issue #705 (epic #700).** Not a language contract.
`GENIA_STATE.md` remains final authority. This follows `docs/process/run-change.md` and
the GENIA Change Pre-Flight template (sections condensed; the portability block is complete).

## 1. Sources reconciled

| Source | What it says about E28-4 |
|---|---|
| Issue #705 | Make the server usable through the transport(s) E28-0 approved; stdio is required, Streamable HTTP "only if E28-0 approves it for R28"; deterministic startup/config; transport tests that do not alter Genia semantics; deployment/security docs. Acceptance: at least one mainstream MCP host/client connects over stdio and uses the tools end to end. |
| E28-0 contract (`docs/design/r28-genia-mcp-contract-threat-model.md`) | Section 7: "V1 transport scope is local **stdio only** ... Streamable HTTP is explicitly deferred from R28 v1 and is not required for release completion." Section 9.3: any HTTP proposal needs a separate contract amendment and threat review. Section 12: the checked-in configuration (prefer `.mcp.json`, `.vscode/mcp.json` only if verified necessary), the end-to-end evidence list (12.2), and the documentation obligations (12.3). |
| `docs/strategy/roadmap/r25-r29.md` | "Streamable HTTP is deferred from R28 v1." Release acceptance requires a checked-in credential-free configuration and a reproducible VS Code/Copilot development loop. |
| `GENIA_STATE.md` 9.41-9.43 | The server, `genia_parse`, and `genia_run` are implemented (Python reference host, experimental, intermediate surface); no client configuration is checked in; no VS Code/Copilot acceptance has been demonstrated. |
| Merged E28-1 through E28-3 (PR #1073 verified in `git log`) | `apps/mcp/mcp.genia` advertises exactly `genia_capabilities`, `genia_parse`, `genia_run` when launched through `hosts/python/mcp_launch.py`. |
| Ledger `docs/analysis/r28-host-dependency-inventory.md` | H01-H35 recorded; this phase adds findings only with evidence. |

## 2. Conclusions (each supported by the sources above)

- **stdio is approved; Streamable HTTP is deferred.** The contract and the roadmap agree (contract
  sections 7 and 9.3 against roadmap "deferred from R28 v1"). There is no contradiction to
  report. E28-4 implements and proves stdio only and adds no HTTP listener, route, or option.
- **No language semantics change.** Nothing here touches syntax, the parser, the evaluator, the
  normalized parse surface, Core IR, builtins, or R9/R23 JSON.
- **No new authority.** The client configuration only starts the existing launcher; the worker
  profile (E28-3) is unchanged. No secret, environment, or configuration discovery is needed or
  allowed.
- **Client configuration is developer tooling, not language semantics.** It is process-only.
- **Numbering note.** Issue #706 is the conformance/parity matrix (E28-5) and #707 the demo and
  release audit (E28-6). E28-4 therefore owns the checked-in configuration and the minimal
  acceptance proving case; the full matrix and the final demo are not part of it.

## 3. Verified client facts (primary sources; not from memory)

- VS Code documentation source (`microsoft/vscode-docs`, `docs/agent-customization/mcp-servers.md`
  and `docs/agents/reference/mcp-configuration.md`, fetched during this phase): workspace
  `.vscode/mcp.json` (top-level `servers`) and a workspace-root **portable** `.mcp.json`
  (top-level `mcpServers`, "works across compatible tools"); in a trusted workspace servers in both
  files "can start without a separate MCP server trust prompt"; the `cwd` of a VS Code-format stdio
  server defaults to the workspace folder. The fetched pages do **not** state which MCP protocol
  versions VS Code speaks, and do not enumerate the portable format's fields.
- Claude Code reads a project-root `.mcp.json` with a top-level `mcpServers` object whose stdio
  entries use `command`, `args`, and `env` (search-result documentation; the host
  `code.visualstudio.com` and the Claude documentation host could not be fetched directly).
- Official TypeScript client SDK `@modelcontextprotocol/client` 2.2.0 (published 2026-09-28)
  implements the 2026-07-28 spec. Its `connect()` defaults to the legacy `initialize` handshake
  (`DEFAULT_VERSION_NEGOTIATION_MODE = "legacy"`); the modern, stateless path needs
  `versionNegotiation` `auto` or a pin, and `auto` launches the server twice for one connection
  (a `server/discover` probe, then the session). The v1 `@modelcontextprotocol/sdk` 1.31.0 does not
  know 2026-07-28 at all.

## 4. PORTABILITY ANALYSIS

- **Does this change portable semantics?** NO.
- **Portable contract:** none new. The stdio framing and the three tools are already the E28-0 contract.
- **Python implementation today:** the launcher, host, supervisor, and worker (E28-1 to E28-3).
- **C++ implementation today:** none; no C++ MCP support or parity is claimed.
- **Not implemented:** Streamable HTTP, resources, prompts, C++ MCP.
- **Shared spec/conformance approach:** not applicable (no portable observable language behavior;
  R16 conformance is untouched). `spec/manifest.json` and `spec/known_host_gaps.json` need no entry.
- **Classification:** host-only plus process-only.
- **Can one host merge before the other?** Not applicable.

## 5. Risks recorded before design

1. A client that defaults to the legacy `initialize` handshake cannot use this server, because the
   contract (section 7.1) makes `initialize` an unknown method. Whether VS Code/Copilot does so is
   unverified here; this is not changed in E28-4 (it would be a contract amendment).
2. The launch command is a chain of up to four processes with a wrapper (`uv`), so shutdown and
   disconnect paths need real tests, not assumptions.
3. A real VS Code/Copilot run cannot be executed in this environment (no GUI, no GitHub
   authentication, documentation host not fetchable); it must not be claimed.

## 6. Decision

**GO** for design, failing tests, and implementation of stdio only. Streamable HTTP, resources,
prompts, C++ MCP, new Genia semantics, a Python MCP SDK, and any widening of authority stay out.
E28-4 does not complete R28 and does not implement E28-5 or E28-6.
