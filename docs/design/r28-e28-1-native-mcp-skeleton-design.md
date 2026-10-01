# R28 E28-1 — Native Genia MCP Skeleton and Capabilities: Design

Status: **Design approved and implemented (issue #702, epic #700); contract
Clarification A1 applied.** The implemented behavior is recorded in
`GENIA_STATE.md` section 9.41; this document remains the design and discovery
record. Implementation differences from the original plan: the launcher starts
Genia with `python -c "from genia.interpreter import _main; ..."` (as
`hosts/python/exec_cli.py` does) because `-m genia.interpreter` writes a runpy
warning to stderr; nonzero exit on a rejected launch datum uses a deliberate
runtime error because Genia has no exit facility (ledger R28-H15); and `mcp.genia`
uses total accessors and guard arms rather than `&&` chains (ledger R28-H16). `GENIA_STATE.md` remains final authority for implemented behavior.
This document applies the merged E28-0 contract
(`r28-genia-mcp-contract-threat-model.md`). Where verified MCP `2026-07-28` wire
requirements or the intermediate-surface rule need wording the contract lacks, the
gap was listed as a proposed clarification and is now resolved by contract
Clarification A1 (§9) rather than silently contradicted.

## 0. Relationship to the R28 ledger

`docs/analysis/r28-host-dependency-inventory.md` is the **primary, living record**
of host dependencies and Genia capability gaps for all of R28 (what we found and
what we are doing about it). **This document records how each E28-1 finding was
discovered** (probes, outputs, wire verification). The ledger is a required input
to every later R28 phase and the final audit. Discovery here creates no issue: an
entry is promoted to an issue only through the normal finding → evidence → issue →
pre-flight → roadmap process, at the R28 audit or earlier only if a gap blocks R28.
Section 8's table is the E28-1 slice of the ledger; on any conflict the ledger wins.
Ledger IDs are cited as `[H##]` below.

## 1. Issue/contract reconciliation

Issue #702's original body predated the native-Genia amendment (Python package,
mandatory official SDK, "resource metadata"). The merged contract overrides it, and
#702 has been rewritten to match (see the E28-1 report). E28-1 is: a native
`apps/mcp/mcp.genia` over stdio, `server/discover`, `tools/list`, and
`tools/call` for `genia_capabilities` only. No SDK, no resources, no prompts.

## 2. Final surface vs intermediate development surface

- **Final R28 v1 surface** (contract §2.1, unchanged): exactly `genia_capabilities`,
  `genia_parse`, `genia_run`. Required by final R28 acceptance (E28-5/E28-6).
- **Intermediate surface** (this design): a server advertises only tools whose
  behavior is implemented at that ticket.
  - E28-1: `["genia_capabilities"]`
  - E28-2 adds `genia_parse`; E28-3 adds `genia_run`.
- An unadvertised tool name is an **unknown tool** protocol error (§7). There is no
  fabricated "not implemented" envelope and no `internal_error` stand-in.
- Intermediate evidence never presents an advertised-but-nonfunctional tool as a
  completed capability. The three-name assertion is a final-acceptance test owned by
  E28-3+/E28-5, not E28-1.
- Consequence for `genia_capabilities.tools`: it reports the tools the running server
  actually exposes (E28-1: one name). See §9 C1.

## 3. Capability reconnaissance (evidence table)

Probed with the real CLI on the Python reference host and cross-read against
`GENIA_STATE.md`.

| Capability | Authority | From `.genia` | Result / MCP-relevant limit |
|---|---|---|---|
| stdin | STATE (`stdin` lazy source) | yes: `stdin \|> lines` | line-oriented; per-line byte bound not enforceable before materialization (gap, E28-3+) |
| stdout | STATE 1776-1780 | yes: `writeln(stdout, s)` | no `writeln/1`; sink required |
| stderr | STATE sink section | yes | used only for fixed startup diagnostics |
| strict JSON decode | STATE 3218-3254 | yes | returns `some(represent("json", root), ctx)`; needs `pattern Json(v) = representation_match("json", v)` before map patterns match (verified) |
| strict JSON encode | STATE 3219, 3252 | yes | always indented + sorted keys; multi-line → must be framed (§6) |
| single-line framing | — | yes (verified) | `split(t, "\n") \|> map(trim) \|> join("")` yields valid one-line JSON; `": "` separators remain (accepted, §6) |
| bytes/Unicode | STATE, `utf8_*` | yes | strict UTF-8 + scalar validation in `json_decode` |
| functions / patterns | GENIA_RULES 45-62 | yes | top-level params are identifiers; dispatch via arm bodies `f(x) = pat -> e \| _ -> e` (verified) |
| Outcomes | STATE | yes | `some/err` arms work; `unwrap_or` rejects `err` (verified) |
| maps | STATE | yes | `{k: v}` literals and partial map patterns |
| Templates / `json_schema` | STATE 3255+ | yes | candidate for closed validation; may use hand patterns where simpler |
| Flow | STATE | yes | lazy; terminal `run` required (verified) |
| entry / CLI | CLI help | yes | `genia file.genia args…` calls `main(args)`; argv reaches Genia (verified) |
| spawn worker | STATE 9.40 | partial | `execution.process` has hard deadline, kill+reap, incremental limits; no Genia-side capability bootstrap, child stdin EOF, argv ≤128 KiB/arg, non-cancellable (E28-3 concerns) |
| parse / eval value APIs | `parse_adapter.py`, CLI | no | E28-2 / E28-3 scope |

Discovery notes (ledger cross-references): `json_decode`'s outer `json` facet and the
need for a `Json(...)` pattern [H11]; lazy Flow requiring terminal `run`, `writeln`
requiring a sink, identifier-only top-level parameters [H12]; single-line JSON via
`split/trim/join` [H03]; `execution.process` limits (capability bootstrap [H05],
stdin [H06], argv size [H07], cancellation [H08]); unbounded `lines` and the
unverified U+2028 behavior [H09]; build identity [H10].

## 4. Native proof (experiment, not product code)

A throwaway program read stdin lines, decoded JSON, matched the `Json(...)` facet and
a map pattern, built a value, encoded it, and wrote it to stdout. **Yes**: the
validation/dispatch/composition centre lives in Genia. The E28-1 tests now encode that
pipeline.

## 5. E28-1 scope and architecture

```text
MCP client --(newline-delimited JSON-RPC, stdio)--> apps/mcp/mcp.genia
   main(args): args = [contract_revision]      # only host-supplied datum
   stdin |> lines |> decode |> validate |> dispatch |> build response |> encode+frame |> stdout
```

Native (`mcp.genia`): line decode, JSON-RPC shape validation, `_meta` validation,
protocol-version check, method dispatch (`server/discover`, `tools/list`,
`tools/call`), tool dispatch, closed argument validation, the `genia_capabilities`
value, the result envelope, the `CallToolResult`/`ListToolsResult`/`DiscoverResult`
values, protocol-error selection, JSON encoding and single-line framing, stdout.

Host (narrow): the launcher passes exactly one datum, `contract_revision`, as argv[0]
and starts the same program any MCP client could start (a future `.mcp.json` command
launches this same thing). `mcp.genia` validates the value (40 lowercase hex) and
refuses to start otherwise (nonzero exit, fixed stderr text, nothing on stdout).

Not in E28-1: parsing, execution, workers, limits, cancellation behavior beyond
ignoring notifications, VS Code acceptance, C++.

## 6. JSON framing (decision)

Single-line valid JSON is the E28-1 bar; byte-minimized JSON is **not** required and is
removed from the gap backlog. Native `json_encode → split("\n") → trim → join("")` is
accepted provided tests prove (a) exactly one protocol line per frame, (b) string
escapes stay correct, (c) newlines inside strings (including U+2028, control
characters, quotes, backslashes, astral code points) cannot become framing newlines,
and (d) decoding the emitted line reproduces the intended value. Test vector: the
JSON-RPC `id`, which the server echoes verbatim.

## 7. Verified MCP 2026-07-28 wire shapes

Authoritative sources (raw files from `modelcontextprotocol/modelcontextprotocol`,
`main`, fetched during this phase):

| Topic | Source |
|---|---|
| stdio framing | `docs/specification/2026-07-28/basic/transports/stdio.mdx` |
| JSON-RPC shapes, `resultType`, error codes, `_meta`, statelessness | `docs/specification/2026-07-28/basic/index.mdx` |
| version handling, `UnsupportedProtocolVersionError`, `server/discover` MUST | `docs/specification/2026-07-28/basic/versioning.mdx` |
| `tools/list`, `tools/call`, tool errors, unknown tool | `docs/specification/2026-07-28/server/tools.mdx` |
| cancellation | `docs/specification/2026-07-28/basic/patterns/cancellation.mdx` |
| typed shapes (`RequestMetaObject`, `CacheableResult`, `DiscoverResult`, `ListToolsResult`, `CallToolResult`, `Tool`, error codes) | `schema/2026-07-28/schema.ts` (+ generated `schema.json`) |

Pinned facts:

- **Framing:** one JSON-RPC message per line; messages MUST NOT contain embedded
  newlines; server stdout carries only valid MCP messages; logging only on stderr;
  server exits promptly on stdin EOF.
- **Request:** `{jsonrpc:"2.0", id:string|integer (never null), method, params?}`;
  a message without `id` is a notification and gets no response.
- **Per-request `_meta`** (in `params._meta`, required): `io.modelcontextprotocol/protocolVersion`
  (string, required), `io.modelcontextprotocol/clientCapabilities` (object, required),
  `io.modelcontextprotocol/clientInfo` (optional). Missing required field → `-32602`.
- **No `initialize`, no session.** The server MUST implement `server/discover`.
- **Unsupported version** → error `-32022`, `data:{supported:["2026-07-28"], requested:<v>}`.
- **Result:** `{jsonrpc, id, result:{resultType:"complete", …}}`; server SHOULD add
  `_meta["io.modelcontextprotocol/serverInfo"]:{name,version}`.
- **`server/discover`:** `DiscoverResult` = `resultType`, `supportedVersions`, `capabilities`,
  `ttlMs`, `cacheScope`, optional `instructions`. E28-1 capabilities: exactly `{tools:{}}`.
- **`tools/list`:** `resultType`, `tools[]` (each `name`, `inputSchema{type:"object"}`,
  optional `description`), `ttlMs`, `cacheScope`, optional `nextCursor` (E28-1: omitted).
- **`tools/call`:** `CallToolResult`: `resultType`, `content[]`, optional `structuredContent`,
  optional `isError`. Contract §2.2 maps to one text item plus `structuredContent`.
- **Protocol errors:** unknown tool, malformed call params → `-32602`; unknown method →
  `-32601`; invalid JSON-RPC object → `-32600`; unparseable JSON → `-32700`; error
  responses omit `id` when it cannot be read. `-32002`/`-32042` MUST NOT be emitted;
  `-32020..-32099` only as defined (`-32022` used).
- **Cancellation (stdio):** `notifications/cancelled`; server MAY ignore unknown/finished
  requests; notifications never get a response.
- Fixed protocol-error messages (no echo of caller strings): "Invalid request",
  "Parse error", "Method not found", "Invalid params", "Unknown tool",
  "Unsupported protocol version".
- `tools/list` and `server/discover` use `ttlMs: 0`, `cacheScope: "public"` because the
  intermediate surface changes between tickets (decision D1).
- `serverInfo` = `{name:"genia-mcp", version:<contract_revision>}` (decision D2).

## 8. Host-dependency inventory (E28-1 slice; ledger is authoritative)

Classes: A intrinsic host; B Genia capability gap; C native Genia.

| # | Responsibility | Class | Evidence | Host API / authority | Tests | Removal condition |
|---|---|---|---|---|---|---|
| 1 | stdio loop, decode, validation, dispatch, discovery | C | §4 proof | none | stdio behavioral + drift tests | n/a |
| 2 | `genia_capabilities` value, envelope, protocol results/errors | C | maps/arms verified | none | exact-shape tests | n/a |
| 3 | Closed request/argument validation | C | patterns verified | none | schema tests | n/a |
| 4 | Single-line JSON framing | C | `split/trim/join` verified | none | framing tests (§6) | n/a |
| 5 | **Build/launch identity: `contract_revision` (40 lowercase hex)** | **A** | Genia has no build-info facility; value must not be request-selected and must carry no dirty state | launcher computes `git rev-parse HEAD` at repo root (module-relative, not caller cwd), passes as argv[0]; fails closed if unavailable; sanitized env allowlist | format, determinism, no-dirty, no-request-fs, no-Python-capability-construction tests | a reusable build-identity facility |
| 6 | Launch command / env allowlist | A | existing CLI file mode | `hosts/python/mcp_launch.py` only | launcher tests | n/a |
| 7 | Worker launch, deadline, kill/reap, byte bounds | A (reuse) | `execution.process` | provisioned capability | E28-3 | n/a |
| 8 | Capability bootstrap for `execution.process` | B | STATE 9.40 | none in E28-1 | E28-3 | bootstrap API |
| 9 | Source → worker stdin / >128 KiB | B | STATE 9.40 | none | E28-3 | stdin option |
| 10 | In-flight cancellation | B | blocking call | none | E28-3 | cancellable handle |
| 11 | Per-line stdin byte bound | B | `lines` materializes | none | E28-3+ | bounded reader |
| 12 | MCP Python SDK | not adopted | items 1–4 native | n/a | AST/dependency test | n/a |

Byte-compact JSON is no longer listed as a gap.

The host must not construct the capability response: the launcher imports no JSON
module and contains no tool-name, envelope, or protocol literal; `mcp.genia` is the
only place they exist.

## 9. E28-0 clarifications (resolved)

C1–C4 and D2, found while verifying MCP `2026-07-28`, were applied as narrow
**Clarification A1** in the E28-0 contract (`r28-genia-mcp-contract-threat-model.md`
§2.1, §2.2, §2.3, §7.1, §11, §12.2, §14) and ledger entry R28-H14 is closed. This
design and the E28-1 tests implement the clarified contract:

- **C1:** final three-tool surface vs. truthful intermediate surface; `tools` reports
  the advertised set.
- **C2:** `CallToolResult` (`resultType`, `isError`) and verified error codes
  (`-32022`, `-32602`, `-32601`, `-32600`, `-32700`).
- **C3:** mandatory `server/discover`; `ttlMs: 0`, `cacheScope: "public"`.
- **C4:** `execution_profile` reported as governed policy before execution exists.
- **D2:** `serverInfo.version` is the injected `contract_revision`.

## 10. Failing-test plan (implemented in this phase)

`tests/unit/test_r28_mcp_skeleton.py` (wire), `tests/unit/test_r28_mcp_launcher.py`
(launch identity), `tests/unit/test_r28_mcp_architecture.py` (drift). Coverage:
discovery, `tools/list`, `genia_capabilities` exact shape, determinism/statelessness,
unknown tool (including `genia_parse`/`genia_run` at E28-1), closed arguments,
`_meta` validation, unsupported version, legacy `initialize`, resources/prompts
methods, malformed JSON/requests, notifications, framing vectors, startup revision
validation, launcher identity, and Python-ownership drift (AST scans, dependency scan,
host-only-supplies-revision differential, no-authority behavior).

## 11. Future C++ host needs (recorded, not claimed)

To run the same `mcp.genia`: `stdin |> lines`, `json_decode`/`json_encode`,
`representation_match`, map/arm dispatch, `split/trim/join`, argv, `writeln(stdout, …)`;
E28-3 adds a provisioned `execution.process`. No C++ MCP support or parity is claimed.
