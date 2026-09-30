# R28 — Genia MCP Server Contract and Threat Model

Status: **Proposed contract; no MCP server is implemented.** This is E28-0,
issue #701, under epic #700 and the approved R28 pre-flight #1055.
`GENIA_STATE.md` remains final authority for implemented Genia behavior.
This document constrains later R28 tickets; it does not make any MCP surface,
host capability, or transport current merely by naming it.

## 1. Purpose and boundary

R28 publishes a small, governed Model Context Protocol (MCP) adapter over
existing Genia parsing and evaluation. MCP is an integration boundary, not a
second semantic authority. The adapter may select a narrower execution policy
than the ordinary Genia CLI, but it must not reinterpret accepted source.

The v1 product path is:

```text
explicit MCP arguments
  -> closed adapter policy
  -> existing Python reference-host parse or evaluation surface
  -> bounded, normalized MCP result
```

The release is approved infrastructure work that can expose an existing
Outcome-aware validated-data pipeline to MCP clients. It adds no Genia syntax,
parser rule, AST or Core IR node, evaluator behavior, builtin, prelude function,
MCP client, or ambient authority.

## 2. Locked v1 public surface

### 2.1 Names and discovery

V1 exposes exactly these MCP tools:

- `genia_capabilities`
- `genia_parse`
- `genia_run`

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

Messages are fixed, adapter-owned summaries. They must not include source text,
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
claim that every Genia capability is available through MCP. Array order is
fixed as shown. Later implementation must obtain version/build data without
reading request-selected paths or exposing a dirty workspace description.

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
262,144 bytes after UTF-8 encoding. Invalid Unicode input or a larger encoding
returns `input_limit` without parsing.

Success result:

```json
{
  "kind": "parsed",
  "ast": {}
}
```

`ast` is the existing normalized parse-adapter JSON, unchanged. A Genia parse
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
to be lossless JSON or a new Genia serialization. The adapter must capture
output-sink writes separately and must not derive `value` by scraping CLI
stdout. A successful `none("nil")` remains a present rendered value. No MCP,
adapter, or SDK logging may enter either program channel.

A parse failure uses `parse_error`; a rejected authority request uses
`policy_denied`; a Genia evaluation failure uses `runtime_error`. Failure
responses contain no `result` and therefore no partial stdout, stderr, value,
or AST. `exit_code` is fixed to `0` for a completed v1 evaluation and is not a
second outcome taxonomy; failed execution uses the error envelope.

## 3. Mapping to existing Genia surfaces

The MCP adapter reuses, without changing them:

- the Python host's normalized parse adapter for `genia_parse`;
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

## 4. Authority and isolation policy

`genia_run` executes in a fresh, disposable worker for every call. No bindings,
modules, configuration, credentials, caches, filesystem mutations, processes,
or runtime state persist between calls. The worker receives only the explicit
source and adapter-owned fixed policy data.

Before evaluation, the adapter parses source and rejects syntax or resolved
runtime access outside a minimal ordinary-computation profile. Defense must be
layered: AST policy checks alone are insufficient. The worker must also omit or
disable prohibited builtins/modules/capabilities and run with the OS-level
restrictions available to the supported deployment. Failure to establish the
required profile is `internal_error`; it is never permission to run broadly.

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
by the first terminal state recorded by the adapter. No partial output is
returned for either outcome.

The deadline bounds the entire worker parse/policy/evaluation/render operation,
not server startup, MCP framing/dispatch, or queue time. Infinite Flow
consumption, recursion, sleep, busy loops, output floods, and oversized/infinite
value rendering are therefore bounded at the adapter boundary without adding
Genia semantics.

## 6. Protected values and diagnostic hygiene

R10/R13 protected-value behavior remains authoritative. MCP is not a protected
sink and has no declassification authority. A protected value must never appear
in source echoes, AST diagnostics, `value.rendered`, stdout, stderr, error
messages, logs, traces, or capability metadata.

The adapter must apply the existing recursive protected-value rejection at
every value boundary it can reach and preserve existing redacted display/debug
behavior. If a protected carrier nevertheless reaches an MCP result path, the
call fails closed with `policy_denied`, all partial fields are discarded, and a
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

The Python SDK is an implementation dependency, not contract authority. E28-1
must select a released SDK supporting MCP `2026-07-28`, pin its exact resolved
version in the repository lockfile, record it in server version metadata, and
verify schemas and cancellation behavior against that version. Dependency
updates require protocol/schema/security regression review; an SDK major or
behavioral change may not silently widen tools, transports, logging, roots,
sampling, elicitation, resources, prompts, or authority.

V1 transport scope is local **stdio only**. Server stdout is reserved for MCP
frames; server logs go to a separately controlled stderr and obey section 6.
Streamable HTTP is explicitly deferred from R28 v1 and is not required for
release completion. No legacy HTTP+SSE transport is in scope.

## 8. Portable and host-specific contract portions

The following are host-neutral adapter requirements a future implementation
can adopt: the three tool names, closed JSON schemas, envelope taxonomy,
source-only profile, channel separation, limits, denial policy, protected-value
requirements, MCP version, stdio transport, and capability-reporting fields.
They do not become Genia language semantics or an R16 host capability merely
because they are portable to another adapter.

R28 implementation is Python-reference-host-only. Normalized AST details and
rendered/evaluated observations are whatever current authoritative Genia
contracts define; another host may claim MCP v1 only after shared evidence
proves the applicable observations and it reports its own host identity.
`portable_mcp_implementation` therefore remains `false` in R28. No C++ MCP
server, Python/C++ MCP parity, or new entry in the host capability registry is
claimed by E28-0.

## 9. Threat model

### 9.1 Assets and trust boundaries

Protected assets are host files and workspace, process environment,
configuration and secrets, network and listening authority, subprocess/shell
authority, server availability, other requests, diagnostics/logs, and Genia's
semantic integrity. Source text, every tool argument, client metadata, and MCP
cancellation/timing behavior are untrusted. The MCP client is outside the trust
boundary; the adapter, its fixed policy, and its disposable worker supervisor
are inside it. Evaluated Genia source remains hostile even after it parses.

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

## 10. Verification obligations for later R28 tickets

Before any tool is claimed implemented, later phases must provide tests for:

1. exact closed schemas, discovery names, duplicate text/structured content,
   protocol-version rejection, stateless repeated requests, and deterministic
   capability ordering;
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
   adapter/SDK logging isolation; and
9. stdio framing under programs that write both stdout and stderr.

R16 machinery should be reused only where it honestly proves direct-host
observation parity. MCP protocol behavior and security policy need focused
adapter tests; unsupported or unexercised cases are never parity evidence.

## 11. Explicit deferrals and non-goals

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
