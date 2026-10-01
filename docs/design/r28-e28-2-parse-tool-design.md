# R28 E28-2 — `genia_parse` Tool: Design

Status: **Design approved (issue #703, epic #700); contract Clarification A2 resolves
its blocking item (§6); Clarification A3 and §6.1 amend AST transport (H22).**
`GENIA_STATE.md` remains final authority (E28-1 behavior: section 9.41). Governing
contract: `docs/design/r28-genia-mcp-contract-threat-model.md` §2.2, §2.4, §5, §7.1,
§14 (Clarification A1). Findings: `docs/analysis/r28-host-dependency-inventory.md`
(entries cited as `[H##]`).

## 1. Issue reconciliation

Issue #703 asks for "official MCP client contract tests". As with #702 [H13], that
predates the native-Genia architecture: E28-2 uses the same raw newline-delimited
JSON-RPC harness as E28-1 (no SDK) [H02]. Recommendation: correct #703's wording.
Its real constraints stand: no execution, no file reads, no new parser semantics,
and MCP input errors kept distinct from Genia parse failures.

## 2. Reconnaissance (what exists today)

| Fact | Evidence | Consequence |
|---|---|---|
| The approved parse surface is `hosts/python/parse_adapter.parse_and_normalize(source)` | contract §2.4 ("existing normalized parse-surface JSON, unchanged"); used by the R16 `parse` spec category (`hosts/python/exec_parse.py`) | `ast` is that function's `ast` value, unmodified |
| It returns `{"kind":"ok","ast":…}` or `{"kind":"error","type":<Python class>,"message":<raw text>}` | `parse_adapter.py` | the error branch cannot cross the MCP boundary as is: it carries a Python class name and parser text that can quote source tokens (contract §2.2) |
| Parser/lexer failures raise `SyntaxError("… at <pos>")`, where `pos` is a character offset; 72 raise sites, several include token text | `src/genia/parser.py`, `lexer.py` | a safe diagnostic is "parse error at character offset N"; message text is never forwarded |
| `parse_adapter.py` imports `src.genia.interpreter` (repo root on `sys.path`), a second module copy beside `genia.interpreter` | `parse_adapter.py` line 4 | the capability must put the repo root on `sys.path`; acceptable because parsing shares no runtime state, noted for the implementation phase |
| Genia source cannot call the parser: there is no `parse`/`read` builtin, and metacircular `eval` works on quoted values | probe of builtins/prelude | parsing needs a host boundary [H17] |
| E28-0 forbids R28 from adding any builtin or prelude function | contract §1 | the boundary cannot be a new global builtin |
| Precedent for host-provisioned values handed to a Genia app: `hosts/python/exec_ollama_chat.py` runs the program in-process, then calls a Genia function with a host-built authority as an explicit argument | file | E28-2 can reuse this explicit-argument pattern |
| Genia has `byte_length` (UTF-8 bytes) but no code-point length or substring | probes | the byte limit is checked natively; the char `maxLength` guard is subsumed (more than 262,144 chars implies more than 262,144 bytes); line/column cannot be computed natively [H18] |

## 3. Architecture

```text
MCP client --stdio--> mcp.genia
                        decode / validate / dispatch / policy / limits / envelope   (native)
                        |
                        parse_source(source) -> JSON text                            (host capability)
                        |   explicit argument to serve(revision, host), never ambient
                        v
                 parse_adapter.parse_and_normalize (existing, unchanged)
```

### 3.1 The host capability (class A [H17])

`hosts/python/mcp_parse_capability.py` exports one function: given a Genia string,
it returns a **JSON text** with exactly one of these shapes:

- `{"status": "parsed", "ast": <parse_and_normalize ast, unchanged>}`
- `{"status": "syntax_error", "offset": <int or null>}`: a `SyntaxError` from
  lex/parse; `offset` is the trailing ` at <int>` of the message when present
- `{"status": "internal_error"}`: any other exception (for example `RecursionError`)

No exception text, class name, or source fragment crosses back. It reads no file,
evaluates nothing, and resolves no import (parsing only). It contains no tool name,
envelope, or MCP literal. Returning JSON text means `mcp.genia` decodes and validates
the reply natively with `json_decode`, so the host never builds Genia maps.

### 3.2 Explicit provisioning (no ambient authority)

`mcp.genia` gains `serve(revision, host)`, where `host` is a map of provisioned
capabilities. It stays an ordinary Genia function, called explicitly:

- **CLI file mode** (`genia apps/mcp/mcp.genia <rev>`) calls `serve(rev, {})`. No
  parse capability is provisioned, so the server advertises only
  `genia_capabilities`, exactly as E28-1 does today (truthful by construction).
- **The launcher** (`hosts/python/mcp_launch.py`) becomes an in-process host
  bootstrap following the `exec_ollama_chat.py` precedent: build the environment,
  load `mcp.genia`, then call `serve(rev, {parse: <capability>})`. The advertised
  tool list is computed natively from the provisioned keys, in contract order
  (`genia_capabilities`, `genia_parse`).

The launcher still contains no protocol, tool, or JSON logic. Provisioning
validation (a callable under a known key) happens in `mcp.genia`.

### 3.3 Native responsibilities added in `mcp.genia` (class C)

- the `genia_parse` descriptor (`inputSchema`: object, `additionalProperties: false`,
  `required: ["source"]`, `source: {type: string, maxLength: 262144}`) and its
  advertisement only when provisioned;
- argument validation: missing, non-string, or extra properties → `-32602` (protocol);
- size policy: `byte_length(source) > 262144` → `input_limit` envelope
  (`phase: "protocol"`), without calling the capability;
- reply interpretation: decode the capability JSON and pattern-match its three statuses;
- envelopes:
  - `parsed` → `status: "ok"`, `result: {kind: "parsed", ast}`, `isError: false`;
  - `syntax_error` → `parse_error` / `phase: "parse"`, message
    `"Genia source failed to parse at character offset N"` (or without the offset
    when null), `isError: true`;
  - `internal_error` or an undecodable reply → `internal_error` /
    `phase: "adapter"`, fixed message, `isError: true`;
- result limit: if the encoded result envelope exceeds 3,276,800 bytes →
  `result_limit` envelope, AST discarded.

### 3.4 Pinned names and fixed messages (for the failing tests)

| Item | Value |
|---|---|
| Host capability | `hosts/python/mcp_parse_capability.py`, `parse_source(source: str) -> str` (JSON text, §3.1) |
| In-process bootstrap | `hosts/python/mcp_host.py`; the launcher's child command becomes `python -c "<runs hosts.python.mcp_host>" <apps/mcp/mcp.genia> <revision>` |
| Native entry | `serve(revision, host)`; CLI `main(args)` calls `serve(revision, {})` |
| Parse success | `status: "ok"`, `result: {kind: "parsed", ast}`, `error: null` |
| Parse failure | `kind: "parse_error"`, `phase: "parse"`, message `Genia source failed to parse at character offset N`, or `Genia source failed to parse` when no offset |
| Oversized source | `kind: "input_limit"`, `phase: "protocol"`, message `Genia source exceeds the 262144-byte limit` |
| Oversized result | `kind: "result_limit"`, `phase: "adapter"`, message `Result exceeds the 3276800-byte limit` |
| Capability failure | `kind: "internal_error"`, `phase: "adapter"`, message `Internal error while parsing` |

The source byte limit is checked before the capability is called. The result limit is
measured on the single-line JSON encoding of the result envelope (`structuredContent`).

## 4. Native vs host ledger (E28-2 slice)

| # | Responsibility | Class | Note |
|---|---|---|---|
| H17 | Reach the existing parser from Genia | A | parser is runtime; boundary is one explicit capability, no builtin |
| H18 | Code-point length / substring (char `maxLength`, line/column) | B | byte check subsumes `maxLength`; offset-only diagnostics |
| H19 | Contract §2.4 "invalid Unicode → `input_limit`" vs strict `json_decode` | N (contract) | resolved by Clarification A2 (§6) |
| H20 | Capability provisioning needs an in-process host bootstrap | A (relates H05) | `exec_ollama_chat.py` precedent; explicit argument |
| H21 | Stale #703 "official MCP client" wording | N | corrected (#703 body rewritten) |

## 5. Failing-test plan

1. CLI-mode server still advertises only `genia_capabilities`; `genia_parse` is an unknown tool there.
2. Launcher-mode discovery lists `[genia_capabilities, genia_parse]` with the exact schema; `genia_capabilities.tools` matches.
3. Parse parity: for every `spec/parse/*.yaml` source, `result.ast` equals `parse_and_normalize(source)["ast"]`.
4. Parse error: `parse_error`, `phase: "parse"`, `isError: true`, fixed message with offset; no source fragment, Python class name, or raw parser text.
5. Limits: exactly 262,144 bytes parses; 262,145 bytes → `input_limit` without invoking the capability (multibyte cases included); result over 3,276,800 bytes → `result_limit`.
6. Arguments: missing/extra/non-string `source` → `-32602`.
7. No evaluation and no authority: source with side effects (`print`, file, network calls) produces no output or file activity; `import` is parsed, not resolved.
8. Internal failure: a capability `internal_error` or a malformed reply → `internal_error` envelope with a fixed message.
9. Drift: the capability module has no MCP literals; `mcp.genia` owns the `genia_parse` descriptor, validation, limits, and envelopes; changing only the revision changes only revision bytes.
10. Framing and determinism as in E28-1 (repeated requests give identical bytes).

## 6. Contract conflict found (resolved by Clarification A2)

Contract §2.4: "Invalid Unicode input or a larger encoding returns `input_limit`
without parsing." With the verified MCP framing and strict `json_decode`, a request
whose `source` holds invalid Unicode (for example a lone surrogate escape `"\ud800"`)
is rejected as malformed JSON before any tool is dispatched (`-32700`, protocol
error, as E28-1 already does). The server never sees an "invalid Unicode source"
value it could answer with `input_limit`.

Proposed narrow clarification (Clarification A2): invalid Unicode anywhere in a
request is a JSON-RPC parse error (`-32700`); `input_limit` applies to well-formed
source whose UTF-8 encoding exceeds 262,144 bytes. The alternative, decoding
loosely so invalid Unicode reaches `genia_parse`, would weaken the strict JSON
boundary and is not recommended.

Per the R28 rule, this was recorded as [H19]. **Resolved** by contract
Clarification A2 (PR #1062, contract §2.4, §7.1, §15): invalid Unicode is `-32700`
at the JSON-RPC boundary and invokes no tool; `input_limit` applies only to a
well-formed decoded `source` over 262,144 UTF-8 bytes. The test plan above tests
both sides of that boundary.

## 6.1 Amendment: lossless AST transport (H22, contract Clarification A3)

Found during implementation. `parse_and_normalize` can return integer literals beyond
the R9 portable-JSON range (for example `9007199254740992`, or
`123456789012345678901234567890`). Probes showed the first rejection is native
`json_decode` of the capability reply (`_strict_json_int`), with a second behind it in
native `json_encode`. The R9 limit is a data-boundary rule, not an AST or wire rule, so
the AST must not pass through those calls (contract §16).

Amended §3.1/§3.3 (everything else in this document is unchanged):

- **Capability reply.** `parse_source` returns text of exactly one of:
  - parsed: `{"status": "parsed"}` + `"\n"` + `<AST fragment>`, where the fragment is
    the unchanged `parse_and_normalize` AST serialized by the host with Python
    `json.dumps` (exact integers; `sort_keys`, `ensure_ascii=False`,
    `allow_nan=False`, separators `","` and `": "`, so it has no raw newline);
  - syntax error: `{"offset": <int or null>, "status": "syntax_error"}` (no fragment);
  - `{"status": "internal_error"}`.
  The host owns only this lossless serialization. It still contains no tool name,
  envelope, or MCP literal.
- **Native handling.** `mcp.genia` splits the reply at its first newline. The header
  is small and is decoded natively with `json_decode` (it never carries an AST).
  The AST fragment is never decoded. For `parsed` it checks that a fragment is present,
  is a non-empty object text (starts with `{` and ends with `}`), and that the header
  has no other keys; otherwise `internal_error`.
- **Splice.** The success envelope is built natively with a fixed placeholder at the
  `ast` position, encoded with `json_encode`, and the placeholder is replaced by the
  fragment using ordinary string operations (`split`/`join`), once for `structuredContent`
  and once, JSON-string-escaped by `json_encode`, inside the text content item. Exactly
  one placeholder occurrence is required (else `internal_error`). This is local to
  `genia_parse`, not a Genia facility, and not a generic raw-JSON helper.
- **Limits.** The source limit is unchanged and checked before the capability call.
  The result limit is measured on the final single-line `structuredContent` text
  including the fragment; an oversized result is replaced by `result_limit`.
- **Trust.** The fragment is produced by repository host code from the existing
  normalized AST; native code does not re-validate its JSON grammar. A
  serialization failure (for example an unserializable value) is `internal_error`.
- **Unchanged.** R9 `json_decode`/`json_encode`, Genia integer semantics, parser,
  normalized AST shape, A2, and every non-AST MCP behavior.

Client note: lossless on the wire does not mean lossless in an IEEE-754-only client
decoder; see contract §16.

## 7. Out of scope

`genia_run`, workers, timeouts/cancellation, OS isolation, VS Code configuration,
C++ support, any change to `parse_adapter.py` or parser behavior.
