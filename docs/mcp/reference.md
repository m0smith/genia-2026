# Genia MCP reference (R28, Python reference host)

Status: **R28 reference (complete release).** `GENIA_STATE.md` is the final authority for implemented
behavior; the contract is `docs/design/r28-genia-mcp-contract-threat-model.md`. R28 is complete (see
`docs/releases/R28.md`). This page documents only what is implemented and tested.

## Surface

- Transport: **local stdio** only. Messages are newline-delimited JSON-RPC, one message per line, split on
  `\n` only. stdout carries protocol messages and nothing else.
- Protocol revisions: exactly two (contract amendment A5), selected per request.
  - **2026-07-28** (stateless): every request carries
    `params._meta["io.modelcontextprotocol/protocolVersion"]` and `...clientCapabilities`. `initialize`
    carrying that `_meta` is `-32601`.
  - **2025-11-25** (any request without that `_meta` key): begins with `initialize`. One process-local state
    bit (NEW, then INITIALIZED); nothing else is remembered, and nothing survives the process.
- Methods: `server/discover` (2026-07-28 only), `tools/list`, `tools/call`, `initialize` and `ping`
  (2025-11-25), and the notifications `notifications/cancelled` and `notifications/initialized` (accepted,
  never answered; the latter changes nothing). Everything else is `-32601`.
- Tools: exactly `genia_capabilities`, `genia_parse`, `genia_run`, `genia_language_profile`, in that order (the fourth is amendment A6).
- **No MCP resources. No MCP prompts. No HTTP transport. No C++ MCP implementation.**
- Platform: Python reference host, POSIX. Verified on Linux (CI) and macOS (owner-run, not in CI; on macOS there is no address-space bound and no network namespace, ledger R28-H47); Windows is not
  supported.

## The 2025-11-25 era

`initialize` params: object with string `protocolVersion`, object `capabilities`, object `clientInfo` with
string `name` and `version`; other members are ignored. Result (exactly):

```json
{"protocolVersion": "2025-11-25", "capabilities": {"tools": {}},
 "serverInfo": {"name": "genia-mcp", "version": "<40 hex git commit>"}}
```

| Situation | Answer |
|---|---|
| `protocolVersion` other than `2025-11-25` (including `2025-06-18`, `2025-03-26`, `2024-11-05`, `2026-07-28`, `""`) | `-32602 Unsupported protocol version`, `data: {supported: ["2025-11-25"], requested: ...}`; state stays NEW; never negotiated down |
| malformed or missing member, non-object params | `-32602 Invalid params` |
| second `initialize` once initialized | `-32600 Invalid request` |
| `tools/list` / `tools/call` before a successful `initialize` | `-32602 Invalid params` |
| `ping` (any state) | `{}` |
| `server/discover` without its `_meta` | `-32602` |
| `resources/*`, `prompts/*`, `completion/*`, `logging/*`, `tasks/*`, `roots/*`, `sampling/*`, `elicitation/*`, anything else | `-32601` |

Wire shape differences from 2026-07-28: `tools/list` returns `{tools}` only; `tools/call` returns
`{content, structuredContent, isError}`; the members `resultType`, `ttlMs`, `cacheScope`, and `_meta` are
omitted. Descriptors, the envelope, the fixed messages, limits, cancellation, and policy are identical.
`genia_capabilities` reports `mcp.protocol_version` of the era that served the call. **Client capabilities
(`roots`, `sampling`, `elicitation`, `tasks`, `extensions`, any other) are validated for shape and
discarded: they change no behavior and grant no authority.** The server never sends a request or a
notification.

## Result envelope (every dispatched tool call)

`CallToolResult` (in 2026-07-28 with `resultType: "complete"` and serverInfo `_meta`), `isError`, one text item holding the single-line JSON of the
envelope, and the envelope as `structuredContent`:

```json
{"schema_version": "genia.mcp.v1", "status": "ok" | "error", "result": {...} | null,
 "error": null | {"kind": "...", "message": "...", "phase": "..."}}
```

`status: "ok"` has a non-null `result` and null `error`; `status: "error"` has a null `result`, so a
failure never carries partial stdout, stderr, value, or AST. `isError` is `true` exactly when `status` is
`"error"`. Messages are fixed, server-owned strings: they never contain source text, values, paths,
exception text, class names, or traces.

### Error kinds

| `kind` | `phase` | `message` |
|---|---|---|
| `parse_error` | `parse` | `Genia source failed to parse at character offset N` |
| `policy_denied` | `policy` | `source requests a capability unavailable in the MCP v1 profile` |
| `runtime_error` | `execution` | `Genia source failed during evaluation` |
| `timeout` | `execution` | `Execution exceeded the 5000 ms limit` |
| `cancelled` | `execution` | `Execution was cancelled` |
| `input_limit` | `protocol` | `Genia source exceeds the 262144-byte limit` |
| `result_limit` | `adapter` | `Result exceeds a 1048576-byte channel limit` or `Result exceeds the 3276800-byte limit` |
| `internal_error` | `adapter` | `Internal error while executing` (`genia_run`) / `Internal error while parsing` (`genia_parse`) |

`invalid_request` is part of the closed `kind` enumeration but is not emitted by any tool; protocol-level
problems are JSON-RPC errors.

### JSON-RPC protocol errors (no envelope)

`-32700 Parse error` (malformed JSON, **including invalid Unicode such as a lone surrogate escape**, before any tool
runs), `-32600 Invalid request`, `-32601 Method not found`, `-32602 Invalid params` (including `Unknown
tool` and any argument not in the closed schema), `-32022 Unsupported protocol version` (its `data` lists
the supported versions).

## `genia_capabilities`

Input: `{}` (closed; `arguments` may be omitted). Result (closed object):

```json
{"server": {"name": "genia-mcp", "contract": "genia.mcp.v1"},
 "mcp": {"protocol_version": "2026-07-28" | "2025-11-25", "transport": "stdio"},
 "genia": {"host": "python-reference", "contract_revision": "<40 hex git commit>",
           "portable_mcp_implementation": false},
 "tools": ["genia_capabilities", "genia_parse", "genia_run", "genia_language_profile"],
 "execution_profile": {"name": "source-only-isolated-v1", "source_max_bytes": 262144,
   "timeout_ms": 5000, "stdout_max_bytes": 1048576, "stderr_max_bytes": 1048576,
   "value_max_bytes": 1048576, "diagnostic_max_bytes": 65536,
   "filesystem": false, "environment": false, "configuration": false, "secrets": false, "network": false}}
```

`execution_profile` states the **governed policy**: the five flags are `false` because no such Genia
authority is provisioned. They do not assert an operating-system mechanism; the response never mentions
namespaces or any OS isolation, which is best effort and may be absent on a given host.
`contract_revision` is the clone's `git rev-parse HEAD`; `portable_mcp_implementation: false` states that
only this host implements MCP.

## `genia_language_profile`

Input: `{}` (closed; `arguments` may be omitted; any non-empty `arguments` is `-32602`). Needs no host capability, so every
server advertises it. Result: the common envelope with `result = {"language": {...}}`, a fixed description of Genia's
language model and selected maturity/host gaps for assistants. It is MCP adapter text, not language behavior (`GENIA_STATE.md` governs):

- `name` (`"Genia"`), `contract_revision` (the same value `genia_capabilities` reports);
- `control_flow`: `conditionals: "pattern_matching"`, `if_expression: false`, `loops: false`, `recursion: true`,
  `tail_call_optimization: true`;
- `supported_forms`, `absent_forms` (`if_expression`, `while_loop`, `for_loop`), `patterns` (function-argument, literal,
  wildcard, tuple, list, map, and guard patterns; `ordered_resolution: "first_match"`), `idioms` (branching, repetition, and
  the `open` rule for multi-clause functions);
- `examples`: `gcd` and `factorial`, each a runnable program (`gcd(48, 18)` is `6`, `fact(5)` is `120`). Several clauses of
  one function with a literal first parameter must declare the first clause with `open`; the same text without `open` is
  rejected by the language, so the profile does not use it.

Amendment A7 (#1086) also returns `discovery`, exactly `{coverage, facts}`:
`coverage: "curated_non_exhaustive"` and an ordered array of 12 static facts.
Each fact has exactly `id`, `scope`, `status`, `maturity`, `summary`, and
`state_sections` (ordered strings referencing STATE at `contract_revision`).
The IDs, scopes, statuses, maturity labels, and section mappings are listed in
`GENIA_STATE.md` section 9.50; exact summaries are in contract section 20.

Status is one of `implemented`, `partial`, `planned`, `scaffolded`,
`unsupported`, within the stated scope. Maturity is `Experimental`, `Partial`,
`Stable`, or JSON null for unspecified; none of these 12 facts is Stable.
Partial shared Flow coverage does not mean missing Python Flow, bounded C++
language support does not mean C++ MCP, and browser scaffolding is docs only.
The catalogue grants no governed execution authority; omitted facts imply
nothing. Discovery JSON is at most 16,384 UTF-8 bytes, summaries at most 256
bytes; these bound the static payload, not execution. There are no live reads
or host probes, including in plain file mode.

The output is byte-identical across calls, protocol eras, and namespace modes. Members are emitted in the encoder's sorted
order; object member order is not a claim. The fact array order is fixed by A7.

## `genia_parse`

Input: `{"source": string}` (closed; `source` at most 262,144 **UTF-8 bytes**, enforced in bytes; the schema's
`maxLength` is an early character guard only). Never evaluates, reads files, resolves imports, or acquires
authority.

- Success: `result = {"kind": "parsed", "ast": <normalized parse output>}`. The AST is the repository's
  existing normalized parse surface, returned unchanged. It is intentionally coarse: many nodes (for
  example a negative literal) appear as `{"kind": ...}` only. **Integers are exact**: values beyond the JSON
  safe-integer range are emitted as exact JSON number tokens (never rounded, never strings), so a client
  that decodes JSON numbers as IEEE-754 doubles will lose precision.
- Failure: `parse_error` with a **character offset** (not bytes, and no line/column). Source over the byte
  limit is `input_limit` and is not parsed.
- Empty, whitespace-only, and comment-only source parse to an empty program.
- Non-ASCII identifiers are not accepted by the current parser; the failure is reported as `parse_error`.

## `genia_run`

Input: `{"source": string}` (closed; same limit). Source only: no mode, argv, stdin, filename, environment,
configuration, secret, network, timeout, or limit argument. Evaluation uses **command-source semantics**:
`main` is **not** dispatched (unlike `genia -c`), there is no REPL persistence, and nothing carries over
between calls: each call runs in a fresh disposable worker.

Success:

```json
{"kind": "completed",
 "value": {"rendered": "<canonical debug rendering of the final value>"},
 "stdout": "<program stdout>", "stderr": "<program stderr>", "exit_code": 0}
```

- `value.rendered`, `stdout`, `stderr` are separate channels. The value is Genia's canonical debug text,
  **not** a portable or lossless serialization; callable values render as host text (a Python function
  representation with an address). `none("nil")` is a present value.
- `exit_code` is always `0` for a completed run; failures use the error envelope.
- Program output is data. Text that looks like JSON-RPC, method names, or cancellation notices stays inside
  `stdout`/`stderr` and cannot affect framing or cancel the run.
- Limits (UTF-8 bytes): stdout 1,048,576; stderr 1,048,576; rendered value 1,048,576; whole result
  3,276,800. Crossing a limit aborts the worker and returns `result_limit` with nothing partial.
- Time: a fixed **5,000 ms** deadline measured from worker readiness (worker start-up is bounded separately
  at 30 s and is an `internal_error` if exceeded). `timeout` kills and reaps the worker.
- Cancellation: `notifications/cancelled` with `requestId` equal to the running request's id (a string
  never matches a number) kills and reaps the worker; the response is `cancelled`. The first terminal state wins; a cancel
  for another id, a finished request, or with no `requestId` is ignored. While more than 8 MiB of client
  input is pending the server stops reading and cannot observe a cancellation.
- Authority: the program cannot read or write files, see environment variables, read configuration or
  secrets, declassify protected values, use the network, listen, start processes or shell stages, `import`,
  read stdin (it is at end of input) or terminal input, or reach model or retrieval providers. Source that
  names such a capability is `policy_denied`; the restrictions are enforced by static policy over the raw
  parser AST, a default-deny pruned environment, and runtime stubs (see
  `docs/mcp/security-and-deployment.md`). `argv()` is `[]`. A protected value that reaches a result is
  `policy_denied` with nothing partial.
- Known host limitation: UTF-16 surrogate `\u` escapes in program strings cannot cross the JSON boundary
  unchanged (a valid pair becomes one character; a lone surrogate is `internal_error`).

## Evidence

Every statement above is backed by the conformance matrix (`docs/mcp/conformance-matrix.md`), which lists
the test that proves each row and every known limitation. The demo is `docs/mcp/demo.md`.
