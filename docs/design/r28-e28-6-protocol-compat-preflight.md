# GENIA Change Pre-Flight: MCP 2025-11-25 compatibility era for the Genia MCP server

Status: **Pre-flight for contract amendment A5** (issue #707, epic #700, ledger R28-H36 and R28-H39). This
follows the R26+ gate (`docs/process/run-change.md`, `.github/ISSUE_TEMPLATE/genia-change-preflight.md`).
`GENIA_STATE.md` remains final authority for implemented behavior; nothing here is implemented until the
phases below land. **R28 is not complete.**

## Change identity

- **Change name:** MCP `2025-11-25` compatibility era (`initialize`) alongside the existing `2026-07-28` era
- **Release / issue:** R28 / #707 (E28-6), amends the E28-0 contract (#701) as Clarification A5
- **Proposed branch:** the existing E28-6 branch `claude/bold-euler-jb7uoy` (PR #1082)
- **Owner:** repository owner decides; this pre-flight is the recommendation

## Trigger: the H36 decision point occurred

The E28-5/E28-6 audit recorded: if VS Code sends legacy `initialize`, stop and make a contract decision. It
did. On 2026-10-05 the owner ran VS Code `1.138.0` with GitHub Copilot Chat `0.66.0` on macOS (full record:
`docs/mcp/acceptance/vscode-copilot-evidence.md`, run 1). The authentic trace is:

```text
[editor -> server] {"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-11-25",
  "capabilities":{"roots":{"listChanged":true},"sampling":{},"elicitation":{"form":{},"url":{}},
  "tasks":{"list":{},"cancel":{},"requests":{"sampling":{"createMessage":{}},"elicitation":{"create":{}}}},
  "extensions":{"io.modelcontextprotocol/ui":{"mimeTypes":["text/html;profile=mcp-app"]}}},
  "clientInfo":{"name":"Visual Studio Code","version":"1.138.0"}}}
[server -> editor] {"error":{"code":-32601,"message":"Method not found"},"id":1,"jsonrpc":"2.0"}
```

Established by evidence: the checked-in `.mcp.json` is discovered; the launcher starts on macOS; VS Code
reaches the server; VS Code does **not** use `server/discover`; it sends `initialize` for `2025-11-25` with no
`_meta`; the pre-amendment server returns `-32601`; nothing after that was reachable. Under contract section 12.2
the R28 release cannot be accepted by its required mainstream client without a decision.

## Evidence base and its limits

The MCP specification site was **not reachable** from the audit environment (egress blocked), so the
protocol surface below is taken from (a) the VS Code trace above, (b) the official TypeScript SDK `1.31.0`
source, which implements `2025-11-25` (`LATEST_PROTOCOL_VERSION = '2025-11-25'`) and is the reference client
and server for that era, (c) the official client `2.2.0` and Inspector `2.9.0` legacy modes (executed here),
and (d) the repository's own E28-1 verification notes. Facts the trace does not show (what VS Code sends
after the initialize response) are marked **unverified**; the design is deliberately tolerant exactly there.

## 1. Scope lock

**Includes:** one new protocol era, selected by the client's `initialize` request, served by the same native
`mcp.genia`; a closed two-version policy; one state bit (initialized or not) held in the server process; the
methods `initialize`, `ping`, and the notification `notifications/initialized`; era-specific wire shapes for
results; permanent conformance evidence for both eras; the release-gate and ledger updates.

**Excludes:** any new tool, resource, prompt, HTTP, C++ MCP, Windows, sampling, elicitation, roots, tasks,
MCP Apps/UI, logging, completions, pagination, authentication, persistent sessions, protocol versions other
than the two named, any change to Genia syntax, builtins, Core IR, the renderer, string semantics, the
worker, supervisor, policy, limits, or isolation, and #1078 / #1067 work.

## 2. Source of truth

- **`GENIA_STATE.md`:** sections 9.41 to 9.46 (R28 sections 9.41 and 9.43 say the server has no `initialize`).
- **Contract:** `docs/design/r28-genia-mcp-contract-threat-model.md` section 7 ("A future protocol version
  requires an explicit compatibility review"; `genia.mcp.v1` and MCP dates are independent axes), 7.1, 12.2.
- **Conflict to resolve:** section 7 and A1 say the server has no `initialize`, and 12.2 requires VS Code
  acceptance. They cannot both hold for VS Code `1.138.0`. Resolution: amend section 7 narrowly (A5).

## 3. Feature maturity

Experimental/partial as R28 is. The compatibility era is Python-reference-host-only exactly as the rest of MCP.

## 4. What the 2025-11-25 era requires (minimum subset)

| Question | Answer (source) |
|---|---|
| Exact surface VS Code requires | `initialize` (request), result with `protocolVersion`, `capabilities`, `serverInfo` (trace, SDK `InitializeResultSchema`); then `tools/list` and `tools/call` for the three tools. Whether it also sends `notifications/initialized` and `ping` is **unverified** from run 1, but the SDK client sends `notifications/initialized` immediately after a successful initialize (SDK `client/index.js`), and `ping` is a standard either-side request |
| Minimum compatibility subset | `initialize`, `ping`, `tools/list`, `tools/call`, and tolerant acceptance of `notifications/initialized` and `notifications/cancelled` |
| State the server retains | **One bit** per server process: whether a valid `initialize` has succeeded. It carries no client data (client capabilities and `clientInfo` are validated for shape and discarded), grants nothing, and dies with the process |
| Methods and notifications | requests: `initialize`, `ping`, `tools/list`, `tools/call`; notifications: `notifications/initialized` (accepted, no response, no effect), `notifications/cancelled` (same matching as today). Everything else, including `resources/*`, `prompts/*`, `completion/complete`, `logging/setLevel`, `tasks/*`, stays `-32601` |
| Result shapes that differ | `initialize` result is new. `tools/list` result is `{"tools": [...]}` only. `tools/call` result is `{"content": [...], "structuredContent": envelope, "isError": bool}`. The `2026-07-28` fields `resultType`, `ttlMs`, `cacheScope` and `_meta.serverInfo` are **not** part of this era and are omitted. The tool descriptors, the envelope inside `structuredContent`, and the text item are identical to the modern era |
| Error shapes and codes | the same JSON-RPC codes (`-32700`, `-32600`, `-32601`, `-32602`). Unsupported `initialize` version is `-32602` with `data.supported` (the modern `-32022` is a `2026-07-28` code); modern `-32022` is unchanged for modern requests |
| `ping` | answered `{}` (SDK `PingRequestSchema` handler returns `{}`); allowed in any state |
| `notifications/initialized` | accepted and ignored in every state: the reference SDK server only invokes a callback and gates nothing, and gating would add a state that protects no authority. This keeps the machine to NEW and INITIALIZED |
| Immediate `tools/list` after init | **unverified** for VS Code; works either way because the server does not gate on the notification |
| Capabilities not currently advertised | none required: the server advertises exactly `{"tools": {}}` (no `listChanged`, resources, prompts, logging, completions, tasks) |
| Cancellation | `notifications/cancelled` has the same shape in both eras and the native matcher already needs only `method`, no `id`, and `params.requestId`; it needs no `_meta`, so it works unchanged. An `initialize` request is never running work, so it cannot be cancelled |
| A `ping` sent during a run | the server is single-threaded between requests (ledger H27): it is answered after the run, at most the 5,000 ms deadline later. Documented limitation |

## 5. Era selection and the state machine

Era is decided per message, deterministically, by one rule: **a request whose `params._meta` object contains
the key `io.modelcontextprotocol/protocolVersion` is a `2026-07-28` request** and is validated and served by
exactly the existing path (so every existing modern behavior, including `initialize` with that `_meta`
being `-32601`, is unchanged). Every other request is judged by the compatibility era:

```text
NEW ---- valid initialize (version 2025-11-25) ----> INITIALIZED
 |  ^                                                  |
 |  +-- invalid/unsupported initialize: stay NEW        +-- initialize again: -32600
 +-- ping: {} (any state)                              +-- tools/list, tools/call: served
 +-- tools/list, tools/call: -32602 (no era established, exactly as before the amendment)
 +-- any other method: -32601
```

Deterministic rejections: a request needing an era before a valid `initialize` is `-32602 Invalid params`
(unchanged from the pre-amendment answer for a request without `_meta`); a second `initialize` is
`-32600 Invalid request`; an `initialize` without an id (a notification) is ignored; `server/discover`
without its `_meta` stays `-32602`. A failed `initialize` never changes state. State never survives the
process, so a new server launch always starts NEW.

## 6. Closed protocol-version policy

Exactly two revisions: `2026-07-28` (stateless, selected per request) and `2025-11-25` (selected by
`initialize`). `initialize` with any other `protocolVersion`, including `2025-06-18`, `2025-03-26`,
`2024-11-05`, `2026-07-28` itself, an empty or non-string value, is **rejected, never negotiated down**: the
reference SDK server would counter-offer its latest version; this server instead answers `-32602`
`Unsupported protocol version` with `data: {"supported": ["2025-11-25"], "requested": <string>}`, so no
older revision is implied to be supported merely because it also uses `initialize`. The supported set is
recorded in one machine-readable place in the contract, and the code and the release gate are tested against
it.

## 7. Native Genia and host responsibilities

The existing native program can own everything: `mcp.genia` already decodes, validates, dispatches, builds
every envelope, and matches cancellation, and Genia has `ref` for one mutable cell. **The compatibility era
stays entirely in `apps/mcp/mcp.genia`.** No Python host module gains MCP literals, `initialize`, `ping`,
version strings, or protocol semantics (the architecture tests are extended to assert exactly that). The
launcher, host, supervisor, worker, and multiplexer are unchanged.

## 8. One execution model, not two

Both eras reach the same `tool_descriptors`, the same `call_capabilities`, `call_parse`, `call_run`, the same
`tool_result` envelope builder, the same host capabilities, the same worker, policy, limits, and cancellation
matcher. The era only changes (a) how a request is validated before dispatch and (b) a final wrapper that
drops the four `2026-07-28`-only result fields. `genia_capabilities.mcp.protocol_version` reports the
revision serving that request (`2026-07-28` or `2025-11-25`); its shape is unchanged. Conformance proof: the
same corpus is run through both eras and the `structuredContent` envelopes must be equal (except that one
field).

## 9. Security and authority

Client capabilities (`roots`, `sampling`, `elicitation`, `tasks`, `extensions`) are **parsed for shape only
and discarded**. The server never sends a request, a notification other than responses, or any message
about those capabilities; `genia_run` stays source-only with the unchanged worker profile. The tests assert:
the server emits only responses with matching ids even with VS Code's exact capabilities; results and
tool lists are identical with empty and maximal capabilities; the native program contains no roots,
sampling, elicitation, or task method; and the whole authority, protected-value, limit, timeout, cancellation,
framing, and lifecycle matrix is repeated through the compatibility era. The initialization bit gates only
*whether a request is answered*, never *what a program may do*.

## 10. Test strategy

Failing tests first (red against the pre-amendment server): the VS Code trace replayed verbatim; the handshake;
ordering and malformed/unsupported initialize; ping; unknown methods; era wire shapes; the authority and
protected-value corpora in both eras; limits, timeout, cancellation, lifecycle; the architecture literals; the
official client default/legacy mode connecting (the E28-5 negotiation test becomes a regression test),
`auto` and a modern pin still connecting; the Inspector default and `auto`; the release gate for the three
run states and the contract-derived negotiation set (mutation-tested). Host-specific: Python/OS lifecycle
tests as before.

## 11. Complexity, cross-file impact, philosophy

Necessary complexity: one era branch in `dispatch`, three small handlers, one `ref`. It reveals existing
structure (`result_response` is the one place every success passes through). Files: `apps/mcp/mcp.genia`,
tests and fixtures, the contract, STATE, the MCP docs, the ledger, the matrix, the release page, the
acceptance record and gate. Drift risk: medium (two eras), mitigated by shared code paths and the
cross-era equality tests. Preserves minimalism YES; avoids hidden behavior YES; keeps semantics out of host
adapters YES; the Outcome-aware pipeline demo is unchanged and must work through both eras.

## 12. Host parity

Python only (as all R28 MCP). No portable Genia semantics change; no shared spec, C++, or known-gap entry.

## 13. Prompt plan

Pre-flight (this document) → contract amendment A5 → failing tests → implementation → documentation → audit.
The owner's second authentic VS Code run is the acceptance gate; H39 stays open until then.

## 14. GO / NO-GO

**GO**, conditional on the owner's approval of A5, which the owner has already requested in the instruction
that started this phase. Missing evidence after implementation: the second authentic VS Code run.
