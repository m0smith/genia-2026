# R28 — Genia MCP Server Contract and Threat Model

Status: **Proposed contract; no MCP server is implemented.** This is E28-0,
issue #701, under epic #700 and the approved R28 pre-flight #1055.
`GENIA_STATE.md` remains final authority for implemented Genia behavior.
This document constrains later R28 tickets; it does not make any MCP surface,
host capability, or transport current merely by naming it.

Clarification A1 (issue #702, ledger entry R28-H14) narrowly aligns this contract
with the verified MCP `2026-07-28` specification; see section 14. It changes no
architecture, authority, limit, or threat-model decision.

Clarification A2 (issue #703, ledger entry R28-H19) narrowly places invalid Unicode
at the JSON-RPC decoding boundary rather than in `genia_parse`; see section 15.

## 1. Purpose and boundary

R28 publishes a small, governed Model Context Protocol (MCP) server authored
primarily in native Genia and composed with existing Genia parsing and
evaluation. MCP is an integration boundary, not a second semantic authority.
The server may select a narrower execution policy than the ordinary Genia CLI,
but it must not reinterpret accepted source.

The v1 product path is:

```text
explicit MCP request on stdin
  -> native Genia decode / validation / dispatch / policy
  -> narrow host boundary where authority is required
  -> existing Genia parse or evaluation surface
  -> bounded, normalized MCP result
```

The release is approved infrastructure work that can expose an existing
Outcome-aware validated-data pipeline to MCP clients. It adds no Genia syntax,
parser rule, AST or Core IR node, evaluator behavior, builtin, prelude function,
MCP client, or ambient authority.

### 1.1 Native-Genia architecture requirement

R28 delivers an MCP server application authored primarily in Genia. Host
implementation code is permitted only for capabilities that Genia cannot
currently express or safely enforce. The implementation must minimize that
surface, document every host dependency, and distinguish intrinsic host
capabilities from missing reusable Genia facilities.

The intended ownership is:

```text
MCP client -> stdio -> mcp.genia
                         |
                         +-- protocol/value pipeline in Genia
                         |
                         +-- narrow explicit host capabilities
                               |-- existing Genia runtime/parser/evaluator
                               `-- OS isolation and enforcement
```

MCP is a protocol, not a reason to move application logic into a host adapter.
An MCP SDK is optional implementation machinery, not architectural authority
or a requirement. When current Genia facilities can correctly implement a
protocol or application responsibility, native Genia is the required default.
The fact that R28 initially executes on the Python reference host describes the
runtime used to run `mcp.genia`; it does not make the server application a
Python MCP server.

No statement in this section claims that every required facility already
exists. E28-0 adds no language or runtime behavior merely to reach this target.

## 2. Locked v1 public surface

### 2.1 Names and discovery

The **final R28 v1 surface** exposes exactly these MCP tools, in this order:

- `genia_capabilities`
- `genia_parse`
- `genia_run`

Final R28 acceptance (release audit) requires discovery to return exactly these
three. Before final acceptance, each ticket's development server advertises
**only tools whose behavior that ticket has implemented** (E28-1:
`genia_capabilities`; E28-2 adds `genia_parse`; E28-3 adds `genia_run`), preserving
the order above. An unadvertised tool name is an unknown tool (section 7.1); a
server never advertises a tool it deliberately leaves nonfunctional, and
intermediate evidence never presents one as a completed capability.

V1 exposes no MCP resources and no MCP prompts. In particular, it does not
publish files, source trees, environment values, configuration, logs, schemas,
or release documents as resources. MCP's standard tool discovery is the only
operation discovery mechanism; `genia_capabilities` reports the governed Genia
profile and versions without duplicating language truth.

All input and output schemas are closed: `additionalProperties` is `false` at
every object level declared below. Integers exclude JSON booleans. Tool names,
field names, enum members, and schema version strings are case-sensitive.

### 2.2 Common result envelope

Every successfully dispatched v1 tool call returns one JSON object as MCP
structured content and the byte-identical JSON object encoded as the sole MCP
text-content item for clients that do not consume structured content:

```json
{
  "schema_version": "genia.mcp.v1",
  "status": "ok",
  "result": {},
  "error": null
}
```

or:

```json
{
  "schema_version": "genia.mcp.v1",
  "status": "error",
  "result": null,
  "error": {
    "kind": "policy_denied",
    "message": "source requests a capability unavailable in the MCP v1 profile",
    "phase": "policy"
  }
}
```

The envelope schema is exactly:

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": ["schema_version", "status", "result", "error"],
  "properties": {
    "schema_version": {"const": "genia.mcp.v1"},
    "status": {"enum": ["ok", "error"]},
    "result": {"type": ["object", "null"]},
    "error": {
      "oneOf": [
        {"type": "null"},
        {
          "type": "object",
          "additionalProperties": false,
          "required": ["kind", "message", "phase"],
          "properties": {
            "kind": {
              "enum": [
                "invalid_request", "parse_error", "policy_denied",
                "runtime_error", "timeout", "cancelled",
                "input_limit", "result_limit", "internal_error"
              ]
            },
            "message": {"type": "string"},
            "phase": {
              "enum": ["protocol", "parse", "policy", "execution", "adapter"]
            }
          }
        }
      ]
    }
  }
}
```

`status: "ok"` requires a non-null `result` and null `error`; `status:
"error"` requires null `result` and a non-null `error`. JSON-RPC/MCP framing,
protocol-version, unknown-tool, and argument-schema failures remain MCP protocol
errors. Once a known tool with schema-valid arguments is dispatched, expected
Genia, policy, limit, timeout, and cancellation outcomes use this envelope.
Transport loss may prevent any envelope from being delivered and must not be
misreported as a Genia result.

**MCP `2026-07-28` wire mapping (Clarification A1).** The envelope above is the
tool result's `structuredContent`. The `tools/call` result is a `CallToolResult`:
`resultType: "complete"`, `content` (the single text item), `structuredContent`
(the envelope), `isError`, and `_meta`. `isError` is `false` when the envelope
`status` is `"ok"` and `true` when it is `"error"`. The text item is the
single-line JSON encoding of that same envelope (one protocol line; not required to
be byte-minimized). Protocol
failures use JSON-RPC errors as defined in section 7.1, never the envelope.

Messages are fixed, server-owned summaries. They must not include source text,
rendered runtime values, native paths, environment values, raw host exceptions,
Python class names, stack traces, process identifiers, or SDK error text.

### 2.3 `genia_capabilities`

Input schema:

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {}
}
```

The successful `result` has this exact shape:

```json
{
  "server": {"name": "genia-mcp", "contract": "genia.mcp.v1"},
  "mcp": {"protocol_version": "2026-07-28", "transport": "stdio"},
  "genia": {
    "host": "python-reference",
    "contract_revision": "<40 lowercase hexadecimal Git commit>",
    "portable_mcp_implementation": false
  },
  "tools": ["genia_capabilities", "genia_parse", "genia_run"],
  "execution_profile": {
    "name": "source-only-isolated-v1",
    "source_max_bytes": 262144,
    "timeout_ms": 5000,
    "stdout_max_bytes": 1048576,
    "stderr_max_bytes": 1048576,
    "value_max_bytes": 1048576,
    "diagnostic_max_bytes": 65536,
    "filesystem": false,
    "environment": false,
    "configuration": false,
    "secrets": false,
    "network": false
  }
}
```

The object and its nested objects are closed. `contract_revision` is the exact
repository revision used to build the server; it is evidence of identity, not a
claim that every Genia capability is available through MCP. Later implementation
must obtain version/build data without reading request-selected paths or exposing
a dirty workspace description.

**Clarification A1 — `tools`.** The example above shows the final v1 value. The
`tools` array reports exactly the tools the running server advertises in
`tools/list` (section 2.1), in the fixed order `genia_capabilities`,
`genia_parse`, `genia_run`; a development server reports the implemented subset
(E28-1: `["genia_capabilities"]`). It never reports an unimplemented tool.

**Clarification A1 — `contract_revision` and identity.** `contract_revision` is
server-owned build/launch metadata supplied through the narrow host boundary as an
inert 40-lowercase-hex value; it is not hard-coded in `mcp.genia`, and the host does
not construct the capability result. `mcp.genia` validates the value and refuses to
start when it is absent or not exactly 40 lowercase hexadecimal characters. The
server identity reported in MCP result `_meta` under
`io.modelcontextprotocol/serverInfo` is `{"name": "genia-mcp", "version":
"<contract_revision>"}`.

**Clarification A1 — `execution_profile` is governed policy.** The profile states
the fixed policy this server is governed by. A server that does not yet execute
source (E28-1, E28-2) still reports it: every authority flag is literally `false`
because no such authority exists, and the limits are the policy later enforced by
the execution ticket. Reporting the profile is not evidence that any limit is
enforced or that `genia_run` exists; enforcement is proven only by the tests of the
ticket that implements it.

### 2.4 `genia_parse`

Input schema:

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": ["source"],
  "properties": {
    "source": {"type": "string", "maxLength": 262144}
  }
}
```

`maxLength` is an early character-count guard only. The normative limit is
262,144 bytes after UTF-8 encoding. A well-formed, successfully decoded `source`
string whose UTF-8 encoding exceeds 262,144 bytes returns `input_limit` without
parsing. Invalid Unicode never reaches this tool: a request containing it (for
example a lone surrogate escape such as `"\ud800"`) is malformed JSON and is
rejected at the JSON-RPC boundary with `-32700` before any tool is dispatched
(section 7.1, Clarification A2).

Success result:

```json
{
  "kind": "parsed",
  "ast": {}
}
```

`ast` is the existing normalized parse-surface JSON, unchanged. A Genia parse
failure is `status: "error"`, `kind: "parse_error"`, `phase: "parse"`, with a
bounded normalized diagnostic summary. Parsing never evaluates source and does
not open files, resolve imports, acquire providers, inspect environment state,
or perform network I/O. The result-size policy in section 5 applies to the
normalized AST.

### 2.5 `genia_run`

Input schema:

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": ["source"],
  "properties": {
    "source": {"type": "string", "maxLength": 262144}
  }
}
```

V1 is deliberately **source-only**. It has no execution-mode, argv, stdin,
filename, working-directory, environment, configuration-provider, secret,
network, fixture, module-map, timeout, or limit argument. Accepted source uses
the existing command-source evaluation semantics: no file-mode `main`
dispatch, pipe-mode input, test discovery, REPL persistence, server mode, or
implicit entrypoint. An execution-mode argument is deferred; later work must
version the contract rather than silently widen v1.

Success result:

```json
{
  "kind": "completed",
  "value": {"rendered": "<existing canonical debug rendering>"},
  "stdout": "<program stdout only>",
  "stderr": "<program stderr only>",
  "exit_code": 0
}
```

`value.rendered`, `stdout`, and `stderr` are distinct channels. The returned
value is rendered by the existing canonical debug renderer; it is not claimed
to be lossless JSON or a new Genia serialization. The narrow execution boundary
must capture output-sink writes separately and must not derive `value` by
scraping CLI stdout. A successful `none("nil")` remains a present rendered
value. No MCP, host, or SDK logging may enter either program channel.

A parse failure uses `parse_error`; a rejected authority request uses
`policy_denied`; a Genia evaluation failure uses `runtime_error`. Failure
responses contain no `result` and therefore no partial stdout, stderr, value,
or AST. `exit_code` is fixed to `0` for a completed v1 evaluation and is not a
second outcome taxonomy; failed execution uses the error envelope.

## 3. Native Genia ownership and existing surfaces

The server is expected to express the following in `mcp.genia`, using existing
ordinary values, functions, pattern matching, Outcomes, Templates/validation,
strict JSON boundaries, and explicit I/O:

- MCP/JSON message interpretation after transport framing yields one request;
- protocol-version and closed request-shape validation;
- tool discovery and `genia_capabilities` value construction;
- tool-name dispatch and argument validation;
- policy decisions over normalized request and parse data;
- composition of the parse/execution operations supplied at the narrow host
  boundary;
- normalized success/error selection and result value construction; and
- response encoding and explicit stdout production when the current JSON/I/O
  surfaces can satisfy the exact framing and byte-bound requirements.

`stdin |> lines`, `json_decode`/`json_encode`, callable Templates and ordinary
pattern dispatch, Outcome-aware composition, and `write`/`writeln`/`flush` over
`stdout` provide real current building blocks. This list is an architectural
allocation, not a claim that those facilities by themselves already satisfy
the complete MCP framing, compact encoding, isolation, cancellation, or byte
enforcement contract. Flow is appropriate only where it naturally expresses
ordered request input; R28 does not require a Flow-specific server framework.

The narrow runtime boundary reuses, without changing them:

- the existing normalized parse surface for `genia_parse`;
- the existing parser/evaluator and canonical debug renderer for
  `genia_run`;
- existing output sinks for program stdout/stderr capture; and
- existing normalized Genia diagnostics, followed by stricter MCP boundary
  redaction and size checks.

The R16 host-adapter subprocess protocol is useful precedent for closed JSON,
capability/version reporting, process isolation, channel ownership, timeout
classification, and revision evidence. It is **not** the MCP wire protocol and
is not tunneled through MCP. In particular, its `parse`, `lower`, `eval`,
`cli`, and `capabilities` operations and evidence documents are not exposed as
MCP resources or tools. R28 must not create a second language contract,
conformance runner, evidence format, Core IR format, or capability registry.

The ordinary CLI remains unchanged. MCP policy rejection is not a new Genia
parse/evaluation diagnostic and must not appear when the same source is run
directly outside this adapter profile.

### 3.1 Required host-dependency classification

Every non-Genia dependency proposed in design or implementation must be entered
in a bounded R28 host-dependency inventory with its file/symbol, purpose,
authority, inputs/outputs, affected host, tests, and removal condition. Each
entry has exactly one classification:

1. **Intrinsic host capability** — inherently needs runtime/OS authority and
   remains behind a narrow explicit boundary.
2. **Current Genia capability gap** — belongs conceptually in `mcp.genia`, but
   current Genia cannot express or enforce it cleanly and safely.
3. **Native Genia responsibility** — current Genia is sufficient; host-side
   application logic is prohibited and must move into `mcp.genia`.

Anticipated candidates for the first class are parser/evaluator bootstrap, hard
OS process isolation, forceful worker termination/reaping, OS-enforced
filesystem/network/process denial, hard monotonic deadlines, and incremental
encoded-byte enforcement. These are provisional hypotheses, not pre-approved
host code: design and failing evidence must verify each one against current
Genia before implementation. Compact MCP response framing and any stdin loop
glue must likewise be evaluated rather than presumed host-owned.

## 4. Authority and isolation policy

`mcp.genia` must cause `genia_run` to execute in a fresh, disposable worker for
every call through the narrow host boundary. No bindings,
modules, configuration, credentials, caches, filesystem mutations, processes,
or runtime state persist between calls. The worker receives only the explicit
source and server-owned fixed policy data.

Before evaluation, native Genia policy composition rejects syntax or normalized
runtime access outside a minimal ordinary-computation profile wherever current
facilities permit. Defense must be layered: application policy or AST checks
alone are insufficient. The worker host capability must also omit or disable
prohibited builtins/modules/capabilities and establish the required OS-level
restrictions. Failure at either layer is `internal_error`; it is never
permission to run broadly.

V1 policy is:

- **Filesystem:** no request-selected path, workspace discovery, file-mode
  execution, resource I/O, bare file helpers, import/load from disk, temporary
  file API, Git access, or current-working-directory observation. The worker's
  private implementation directory is not program authority.
- **Environment:** start with a fixed allowlist needed only to launch the host;
  no inherited user variables are Genia-visible. No request may add variables.
- **Configuration and secrets:** provision no R10/R13 provider, `.env` source,
  declassification authority, model provider, embedding/retrieval/reranking
  provider, or other credential-bearing object. Ambient lookup remains absent.
- **Network:** provision no outbound HTTP authority/transport and no listening
  socket. `import web`, HTTP send/serve surfaces, model/provider networking, and
  any equivalent network-capable path are denied.
- **Processes and shell:** shell-pipeline stages, `execution.process`, host
  subprocess capabilities, arbitrary commands, and host interop are denied.
- **Modules:** v1 rejects source import/load forms, including packaged modules;
  no caller-supplied multi-file map exists. Autoloaded pure prelude behavior
  needed by ordinary evaluation may remain only when it cannot acquire a
  prohibited authority.
- **Input:** stdin is immediate EOF and argv is the empty list. There is no tty.
- **Time/randomness/concurrency:** no guarantee of deterministic values beyond
  existing Genia semantics. Calls remain bounded by the worker deadline; the
  adapter makes no scheduler, cancellation, or replay semantics part of Genia.

Later tickets may implement stricter isolation. R28 is not a production
multi-tenant sandbox, and this contract must never be used to advertise it as
one.

## 5. Cancellation, timeout, and size policy

Limits are measured on UTF-8 encoded bytes after normalized `\n` line endings:

- source: 262,144 bytes;
- execution wall-clock deadline: 5,000 ms, fixed by the profile;
- stdout: 1,048,576 bytes;
- stderr: 1,048,576 bytes;
- rendered value: 1,048,576 bytes;
- normalized diagnostic message: 65,536 bytes; and
- complete structured tool result: 3,276,800 bytes.

Workers enforce channel limits incrementally rather than buffering unbounded
content and checking afterward. Crossing any result/channel limit terminates
and reaps the worker, discards all partial result data, and returns
`result_limit`. Source overflow returns `input_limit` before a worker starts.
A diagnostic that would exceed its limit is replaced by a fixed bounded
summary, never naively truncated through a secret or malformed UTF-8 sequence.

MCP cancellation requests cancel the corresponding worker. Cancellation and
timeout both require termination and reap before the call completes; no owned
work may survive. If the transport can still answer, cancellation returns the
`cancelled` envelope and timeout returns the `timeout` envelope. A transport
closure may make delivery impossible. Cancellation has no Genia-level value or
cleanup guarantee beyond terminating the disposable worker, and races resolve
by the first terminal state recorded by the supervisor. No partial output is
returned for either outcome.

The deadline bounds the entire worker parse/policy/evaluation/render operation,
not server startup, MCP framing/dispatch, or queue time. Infinite Flow
consumption, recursion, sleep, busy loops, output floods, and oversized/infinite
value rendering are therefore bounded at the server boundary without adding
Genia semantics.

## 6. Protected values and diagnostic hygiene

R10/R13 protected-value behavior remains authoritative. MCP is not a protected
sink and has no declassification authority. A protected value must never appear
in source echoes, AST diagnostics, `value.rendered`, stdout, stderr, error
messages, logs, traces, or capability metadata.

`mcp.genia` and its host boundaries must apply the existing recursive
protected-value rejection at every value boundary they can reach and preserve
existing redacted display/debug behavior. If a protected carrier nevertheless
reaches an MCP result path, the call fails closed with `policy_denied`, all
partial fields are discarded, and a
fixed message is returned. Catch-all host exceptions become `internal_error`
with a fixed message. Raw exception text, reprs, traceback frames, native file
paths, provider contexts, request source, and SDK diagnostics never cross the
MCP response boundary or ordinary server logs.

Redaction is defense in depth, not a substitute for the no-provider,
no-environment, no-filesystem, and no-network policy.

## 7. MCP protocol, SDK, and transport policy

V1 adopts the current MCP protocol version `2026-07-28` only. It follows that
revision's stateless request model: R28 defines no MCP initialize exchange,
negotiated session, or session-carried authority. A request using another
protocol revision fails at the MCP protocol layer before a Genia tool is
dispatched. A future protocol version requires an explicit compatibility
review; MCP protocol dates and `genia.mcp.v1` are independent version axes.

An MCP SDK is optional implementation machinery, not contract authority or an
architectural requirement. Protocol behavior that existing Genia facilities
can implement belongs in `mcp.genia`. If a later design proves a narrow SDK
dependency necessary, it must support MCP `2026-07-28`, be recorded in the
host-dependency inventory, expose no application policy, and have its exact
resolved version pinned in the repository lockfile and server metadata. SDK
addition or update requires protocol/schema/security regression review and may
not silently widen tools, transports, logging, roots, sampling, elicitation,
resources, prompts, or authority.

### 7.1 MCP `2026-07-28` request/response requirements (Clarification A1)

Verified against the `2026-07-28` specification and schema (stdio transport,
`basic/index`, `basic/versioning`, `server/tools`, cancellation pattern, and
`schema.ts`). The server is stateless: no `initialize`, no session, no state
carried between requests.

- **Framing.** One JSON-RPC message per line, `\n`-delimited, no embedded
  newlines; server stdout carries only valid MCP messages; logging only on stderr;
  the server exits when stdin reaches EOF.
- **Per-request metadata.** `params._meta` must carry
  `io.modelcontextprotocol/protocolVersion` (string) and
  `io.modelcontextprotocol/clientCapabilities` (object); `clientInfo` is optional
  and never changes server behavior. A missing or malformed required field is
  JSON-RPC `-32602`. An unsupported version is `-32022` with
  `data: {"supported": ["2026-07-28"], "requested": <version>}`.
- **`server/discover` (required).** The server implements `server/discover`,
  returning `resultType: "complete"`, `supportedVersions: ["2026-07-28"]`,
  `capabilities` of exactly `{"tools": {}}` (no resources, prompts, logging,
  completions, subscriptions, or list-changed), `ttlMs: 0`, `cacheScope: "public"`,
  and `_meta` serverInfo (section 2.3). It carries no `instructions` in v1.
- **`tools/list`.** `resultType: "complete"`, `tools` in the order of section 2.1
  (each with `name`, `description`, and the closed `inputSchema` of its tool),
  `ttlMs: 0`, `cacheScope: "public"`, `_meta` serverInfo. There is no pagination; any
  `cursor` is `-32602`. (`ttlMs: 0` because the advertised set changes between
  tickets.)
- **`tools/call`.** Result per section 2.2. An unknown or unadvertised tool, a
  missing or non-string `name`, a non-object `arguments`, or arguments that violate
  the tool's closed schema are protocol errors (`-32602`), not envelopes.
- **Decoding boundary (Clarification A2).** Each request line is decoded with
  strict JSON decoding before any validation or dispatch. Malformed JSON,
  including invalid Unicode such as an unpaired surrogate escape (`"\ud800"`) or
  bytes that are not valid UTF-8, is a JSON-RPC parse error (`-32700`) and invokes
  no MCP tool. MCP tools validate only values that successfully cross this
  boundary; a decoded string is always valid Unicode, and tool-level limits
  (such as `genia_parse` `input_limit`) apply to it.
- **Protocol error codes.** Unparseable JSON `-32700`; invalid JSON-RPC object
  (including a `null`, boolean, fractional, or object `id`) `-32600`; unknown method
  (including legacy `initialize`, resources, and prompts methods) `-32601`;
  invalid params, unknown tool, missing or malformed `_meta` `-32602`; unsupported
  version `-32022`. The server never emits `-32002`, `-32042`, or an undefined code
  in `-32020`..`-32099`. Error responses carry a fixed server-owned `message`
  (never caller strings) and omit `id` when it cannot be read.
- **Notifications.** A message without `id` gets no response. `notifications/cancelled`
  is accepted; before the execution ticket there is no cancellable work, so it is
  ignored.
- **Result identity.** Every result carries `resultType: "complete"`; the server
  does not use `input_required` in v1.

V1 transport scope is local **stdio only**. Server stdout is reserved for MCP
frames; server logs go to a separately controlled stderr and obey section 6.
Streamable HTTP is explicitly deferred from R28 v1 and is not required for
release completion. No legacy HTTP+SSE transport is in scope.

## 8. Portable and host-specific contract portions

The following are host-neutral server requirements a future implementation
can adopt: the three tool names, closed JSON schemas, envelope taxonomy,
source-only profile, channel separation, limits, denial policy, protected-value
requirements, MCP version, stdio transport, and capability-reporting fields.
They do not become Genia language semantics or an R16 host capability merely
because they are portable to another adapter.

R28 runs the native `mcp.genia` server on the Python reference host because that
is the initial host for the required parse/evaluation and isolation boundaries.
Python-specific objects and conventions must not leak into `mcp.genia` or its
closed values. Normalized AST details and rendered/evaluated observations remain
whatever current authoritative Genia contracts define.

The portability target is the same `mcp.genia` program running on a future C++
host, with each host supplying the minimal explicit capabilities that program
actually requires. R28 does not implement or claim that C++ support. Another
host may claim MCP v1 only after shared evidence proves applicable observations
and it reports its own identity; `portable_mcp_implementation` therefore remains
`false` in R28. The host-dependency inventory and parity evidence must make a
future multi-host decision evidence-based rather than designing the application
around Python now.

## 9. Threat model

### 9.1 Assets and trust boundaries

Protected assets are host files and workspace, process environment,
configuration and secrets, network and listening authority, subprocess/shell
authority, server availability, other requests, diagnostics/logs, and Genia's
semantic integrity. Source text, every tool argument, client metadata, and MCP
cancellation/timing behavior are untrusted. The MCP client is outside the trust
boundary; `mcp.genia`, its fixed policy, the narrow host capabilities, and the
disposable worker supervisor are inside it. Evaluated Genia source remains
hostile even after it parses.

### 9.2 Threats and required mitigations

| Threat | Required v1 control | Failure |
|---|---|---|
| Hostile source exploits parser/evaluator or invokes hidden authority | Fresh worker, pre-execution AST policy, restricted runtime surface, fixed empty inputs, catch-all normalization | `parse_error`, `policy_denied`, or `internal_error`; no partial result |
| Filesystem/workspace disclosure or mutation | No paths/modes/imports/resource/file helpers; private cwd; no MCP resources/roots use | `policy_denied` |
| Environment/configuration/secret disclosure | Sanitized launch environment; no providers or authorities; recursive protected rejection and fixed diagnostics | `policy_denied` or `internal_error` |
| Network-capable Genia code performs outbound or listening I/O | No network capability, web/provider modules denied, OS isolation where available | `policy_denied`; no attempt |
| Shell/process escape | Shell syntax and process/interop surfaces denied; no process capability | `policy_denied`; no child command |
| Infinite recursion, Flow, sleep, busy loop, or cancellation refusal | Fixed deadline; supervisor kill and reap; one worker per call | `timeout` or `cancelled` |
| Oversized source, AST, output, diagnostics, or value | Preflight source bytes; incremental per-channel and aggregate bounds; discard partial data | `input_limit` or `result_limit` |
| Diagnostic, exception, or log leakage | Fixed messages; bounded normalized diagnostics; no source/raw exception/path/provider/SDK text; sanitized stderr logging | Normalized error only |
| Cross-request state or confused authority | Stateless disposable workers; no sessions; no cached user values or ambient provider | Fail closed |
| Protocol confusion or schema smuggling | One MCP version; closed schemas; reject unknown fields/tools; separate MCP and Genia taxonomies | MCP protocol error or `invalid_request` |
| Remote HTTP authentication, origin, DNS rebinding, CSRF, session theft, or denial of service | No HTTP transport in v1 | Not reachable; any HTTP listener is out of contract |

### 9.3 Residual risk and HTTP deferral

The Python parser/evaluator is not asserted to be a hardened hostile-code
sandbox. Process isolation, least authority, resource bounds, and fail-closed
normalization reduce impact; they do not justify exposing v1 to untrusted
multi-tenant users or a remote network. Operators must treat stdio clients as
local trusted principals even though submitted source is processed defensively.

Any later Streamable HTTP proposal requires a separate contract amendment and
threat review covering bind defaults, authentication and authorization, TLS
termination, Origin validation, DNS rebinding, CSRF, session ownership,
request/concurrency/rate/body limits, reverse proxies, cancellation on
disconnect, audit logging, and tenant isolation. It must not reuse local stdio
trust assumptions or describe R28 as a production sandbox.

## 10. Native-Genia gap audit and follow-up rule

The host-dependency inventory is a release deliverable, not a temporary design
note. Every host-side implementation of pure policy, validation, dispatch,
protocol interpretation, result/error selection, composition, or other value
transformation must be reviewed as presumed application logic. Before R28 is
complete:

- accidental host application logic must move into `mcp.genia`;
- intrinsic host capabilities may remain only with their explicit inventory
  entry and boundary tests; and
- genuine current Genia capability gaps must become owned follow-up proposals.

The final R28 release audit (currently E28-6/#707; if the issue plan later adds
a distinct audit ticket, that ticket inherits this obligation) must publish the
bounded inventory and disposition. Each proposed gap follow-up must identify:

1. the missing reusable Genia capability;
2. concrete R28 implementation evidence showing why it is needed;
3. affected hosts;
4. expected shared conformance requirements;
5. exact host code removable once the capability exists;
6. an owning issue and completed pre-flight proposal; and
7. roadmap placement through the normal roadmap process.

E28-0 assigns no release number and authorizes no speculative language feature
for these follow-ups. Temporary host code must not become permanent architecture
merely because R28 can ship with it.

## 11. Verification obligations for later R28 tickets

Before any tool is claimed implemented, later phases must provide tests for:

1. exact closed schemas, discovery names (the implemented subset at each ticket;
   exactly the three contract tools at final acceptance), duplicate text/structured
   content, protocol-version rejection, `server/discover`, stateless repeated
   requests, and deterministic capability ordering;
2. parse parity with the existing normalized Python parse adapter;
3. run parity for representative accepted programs, including an
   Outcome-aware validated-data pipeline, with separate value/stdout/stderr;
4. denial of every filesystem, import, environment, configuration, secret,
   network, shell, process, and host-interop route available in current Genia;
5. protected sentinels absent from results, diagnostics, exceptions, logs, and
   every limit/failure path;
6. exact-at-limit and one-byte-over source/channel/value/aggregate cases;
7. endless computation and output, cancellation races, worker termination,
   reap, and no cross-request state;
8. malformed Unicode/JSON, hostile diagnostics, raw host exceptions, and
   host/SDK logging isolation; and
9. stdio framing under programs that write both stdout and stderr;
10. native-Genia ownership of validation, dispatch, policy, composition, and
    result/error shaping, with no equivalent Python application path; and
11. every host-dependency inventory entry's classification, boundary, and
    removal condition.

R16 machinery should be reused only where it honestly proves direct-host
observation parity. MCP protocol behavior and security policy need focused
server tests; unsupported or unexercised cases are never parity evidence.

## 12. VS Code / AI development acceptance

R28 is not complete until the native `mcp.genia` server is proven as a local
development tool from a supported VS Code/GitHub Copilot agent client. VS Code
is the required acceptance client, not the owner of the protocol or application
architecture. This acceptance adds no tool, resource, prompt, transport, Genia
semantic, or client implementation to the v1 surface.

### 12.1 Checked-in discovery configuration

The completed release must check in one credential-free MCP configuration that
a repository clone can use after installing the documented Genia development
prerequisites. Prefer repository-level `.mcp.json` when the then-supported VS
Code/Copilot client accepts it; use `.vscode/mcp.json` only when verified client
requirements make the VS Code-specific location necessary. Do not duplicate the
configuration. The configuration and launch command must:

- start the same local stdio `mcp.genia` server usable by other compatible MCP
  clients, rather than a VS Code-specific implementation;
- use repository-relative or otherwise portable commands and contain no
  credentials, secrets, machine-specific absolute paths, or developer-specific
  settings; and
- grant no filesystem, environment, configuration, secret, network, shell,
  process, import, stdin, argv, or other authority beyond sections 4 and 6.

Configuration-file selection and the supported VS Code/Copilot version must be
verified during implementation against current client documentation. E28-0 does
not add either configuration file or claim current client discovery.

### 12.2 End-to-end evidence

Automated evidence where the client permits it, plus a recorded reproducible
VS Code/Copilot acceptance run, must prove all of the following before the final
release audit:

1. VS Code discovers and starts the repository-configured local stdio server
   with only the documented development prerequisites and enablement steps.
2. Tool discovery at final acceptance returns exactly `genia_capabilities`,
   `genia_parse`, and `genia_run`, with no resources, prompts, or additional tools.
3. An AI coding agent calls `genia_capabilities` and receives the normalized v1
   capability description.
4. The agent submits explicit source to `genia_parse` and receives the
   contract-defined structured parse result or normalized diagnostic.
5. The agent submits explicit source to `genia_run` and receives separately the
   rendered value, program stdout, program stderr, and normalized
   error/diagnostic outcome.
6. One recorded development loop starts with invalid Genia source, uses
   `genia_parse` feedback to revise it, and then executes the corrected program
   successfully through `genia_run`.
7. A program that writes both stdout and stderr cannot corrupt MCP framing;
   protocol output remains isolated from both program channels.
8. The launch configuration and observed process have no authority beyond the
   fixed R28 execution profile.

The evidence must record the client version, repository revision, exact portable
configuration path, enablement steps, tool-discovery result, requests, redacted
responses, and pass/fail disposition. It must not include secrets or promote
unexecuted manual claims to automated evidence.

### 12.3 Release and developer documentation

The documentation phase and final release page must state prerequisites, how VS
Code discovers and starts the server, how to enable it, how to verify the exact
three tools, a short Copilot/Agent example, and troubleshooting for startup or
discovery failures. Those instructions must remain client-thin: no VS Code
extension, VS Code-specific Genia semantics, extra MCP tool, or extra transport.
They are not added during E28-0 because the integration is not implemented.

After the acceptance evidence exists, shared AI-development guidance (including
`docs/ai/LLM_CONTRACT.md` and applicable tool-specific instructions) must direct
Genia development agents to prefer the Genia MCP for appropriate Genia parsing
and execution instead of reconstructing behavior from Python implementation
details. Until then, those documents must not claim the MCP is available.

The final R28 audit must also inventory every agent bypass or fallback to
Python, shell, or internal runtime knowledge. Each observation is evidence for
the section 10 gap process, not automatic authority for a language feature: a
follow-up still requires general utility beyond MCP, an owning issue, pre-flight,
and normal roadmap placement.

## 13. Explicit deferrals and non-goals

E28-0 and v1 do not include:

- runtime code, MCP tools/resources/prompts already implemented, or an SDK
  dependency;
- an MCP client in Genia, autonomous agents, tool selection, planning, or
  orchestration;
- files, workspaces, Git, shell commands, arbitrary processes, MCP roots, or
  implicit environment/configuration/secret access;
- network-capable Genia execution, Streamable HTTP, legacy HTTP+SSE, or a
  production multi-tenant sandbox;
- file, pipe, REPL, test, server, module-map, Core IR/lower, or arbitrary CLI
  modes through MCP;
- caller-selected stdin, argv, timeout, limits, cwd, providers, authorities,
  transports, fixtures, or execution mode;
- new syntax, parser/evaluator semantics, AST/Core IR node, Genia-visible
  builtin, host capability claim, conformance protocol, or evidence format;
- a C++ MCP implementation or cross-host MCP parity claim; or
- SICP material, examples, or learning-surface work.

E28-1 (#702) may begin only after this contract is approved. It must not invent
behavior deferred here. E28-0 stops at this document and does not authorize
work on #702 or later R28 tickets.

## 14. Clarification A1 (issue #702, R28 ledger entry R28-H14)

Recorded while implementing E28-1's design, after verifying the MCP `2026-07-28`
specification. Scope is limited to the items below; every other section, and every
authority, limit, isolation, and threat-model decision, is unchanged.

| Item | Section changed | Clarification |
|---|---|---|
| C1 | 2.1, 2.3, 11, 12.2 | The exact three-tool list is the final v1 surface; development servers advertise only implemented tools; `genia_capabilities.tools` reports the advertised set |
| C2 | 2.2, 7.1 | `tools/call` maps to `CallToolResult` (`resultType`, `isError`); protocol errors use the verified JSON-RPC codes including `-32022` |
| C3 | 7.1 | `server/discover` is required; discover/list results carry `ttlMs` and `cacheScope` |
| C4 | 2.3 | `execution_profile` is governed policy and is reported before execution exists, without implying enforcement |
| D2 | 2.3 | `serverInfo.version` is the injected `contract_revision`; `contract_revision` is build/launch metadata supplied through the narrow host boundary |

A1 adds no tool, resource, prompt, transport, Genia semantic, SDK requirement, or
host capability, and it does not implement anything. Findings it leaves open remain
in `docs/analysis/r28-host-dependency-inventory.md`.

## 15. Clarification A2 (issue #703, R28 ledger entry R28-H19)

Recorded during the E28-2 design, after observing that the server's strict JSON
decoder rejects a request containing a lone surrogate escape (`"\ud800"`) with
`-32700` before tool dispatch. Section 2.4 had required `genia_parse` to answer
invalid Unicode with `input_limit`, a case that cannot reach the tool.

| Input | Outcome |
|---|---|
| Malformed JSON, including invalid Unicode (unpaired surrogate escape, invalid UTF-8) | JSON-RPC `-32700`; no MCP tool is invoked |
| Well-formed JSON whose decoded `source` exceeds 262,144 UTF-8 bytes | `genia_parse` `input_limit` envelope, without parsing |

Sections changed: 2.4 (input limit wording) and 7.1 (decoding boundary). MCP tools
validate only values that successfully cross the JSON-RPC decoding boundary. A2
does not loosen JSON decoding and changes no parser, evaluator, Genia language,
MCP transport, or host semantics; it adds no tool, builtin, or capability, and it
implements nothing.
