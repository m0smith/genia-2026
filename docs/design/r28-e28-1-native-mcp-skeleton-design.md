# R28 E28-1 — Native Genia MCP Skeleton and Capabilities: Design

Status: **Design phase only (issue #702, epic #700).** No MCP server, `mcp.genia`,
host capability, or test is implemented by this document. `GENIA_STATE.md`
remains final authority for implemented behavior. This document applies the
merged E28-0 contract (`r28-genia-mcp-contract-threat-model.md`); it does not
amend it.

## 1. Issue/contract reconciliation (needs approval)

Issue #702's body predates the E28-0 native-Genia amendment. It says "minimal
Python-reference-host MCP server package using the official MCP Python SDK",
"approved capability/resource metadata", and "local test harness using the
official MCP client". The merged contract overrides it:

| #702 body | Merged contract | Design decision |
|---|---|---|
| Python MCP package | §1.1: server authored primarily in native Genia (`mcp.genia`) | `mcp.genia` is the application; Python is a narrow host boundary |
| Official MCP Python SDK | §7: SDK optional, must be justified and inventoried | No SDK in E28-1 (see §5); a test-only client may be used for evidence |
| "resource metadata" | §2.1: no MCP resources, no prompts | No resources/prompts of any kind |

Recommendation: edit #702's body to match the contract before implementation.

## 2. Capability reconnaissance (evidence table)

Probed with the real CLI (`uv run genia`) on the Python reference host, and
cross-read against `GENIA_STATE.md`.

| Capability | Authority | Usable from `.genia` | Result / MCP-relevant limit |
|---|---|---|---|
| stdin consumption | STATE §(stdin lazy source) | yes: `stdin \|> lines` | works; line-oriented only. Per-line byte limit is not enforceable before the line is materialized (gap) |
| stdout | STATE 1776-1780 | yes: `writeln(stdout, s)` | works; `writeln/1` does not exist (sink is required). `write`/`flush` exist |
| stderr | STATE sink section | yes (sink value) | not yet exercised in proof |
| strict JSON decode | STATE 3218-3254 | yes: `json_decode` | strict; returns `some(represent("json", root), ctx)` — the outer `json` facet hides a bare map pattern; `pattern Json(v) = representation_match("json", v)` is required (verified) |
| strict JSON encode | STATE 3219, 3252 | yes: `json_encode` | **always two-space-indented, sorted keys** → multi-line; not MCP-framing-safe as is |
| compact JSON | — | partial | Verified natively: `split(t, "\n") \|> map(trim) \|> join("")` yields valid single-line JSON (literal newlines in encoded output are structural only; string newlines are escaped). Result keeps `": "` separators, so it is single-line, **not byte-compact**. Byte-compactness is a gap (class B) |
| object key order | STATE 3252 | no | `json_encode` sorts members; contract fixes only array order, so acceptable |
| bytes/Unicode | STATE 3211-3254, `utf8_*` | yes | strict UTF-8 + scalar validation in `json_decode`; UTF-8 byte-length of a string via `utf8_encode` (length helper for bytes not yet verified) |
| functions / pattern matching | GENIA_RULES 45-62 | yes | verified; top-level params are identifiers only — dispatch uses arm bodies (`f(x) = pat -> e \| _ -> e`), not multi-clause heads |
| Outcomes | STATE | yes | verified `some/err` arm matching; `unwrap_or` rejects `err` |
| maps / records | STATE | yes | `{k: v}` literals and partial map patterns work |
| ordered maps | R17 | yes (Experimental) | not needed by E28-1 |
| Templates / `json_schema` | STATE 3255+ | yes | usable for closed request validation (`additionalProperties: false`); to be proven in the test phase |
| Flow | STATE | yes | `map`/`each` are lazy; a terminal `run` is required (verified) |
| modules/imports | STATE | yes (`import`) | v1 worker policy forbids caller imports; `mcp.genia` itself may import packaged modules |
| program entry / CLI | STATE, CLI help | yes | `genia file.genia` calls `main(args)` (verified) |
| error normalization | STATE, R23 | yes | `err(reason, ctx)`; host text not portable. A decode error's `reason` was not a string in my probe and failed `json_encode` — the test phase must pin the reason shape |
| **spawn a worker / run Genia source in a disposable child** | STATE 9.40 | **partially** | `execution.process(cap, {executable, args, timeout_ms})` already gives hard monotonic timeout, SIGKILL+reap, incremental 1 MiB-per-channel limits. But: no Genia-side way to obtain `cap` (bootstrap deferred); child stdin is immediate EOF (source must travel as argv, which Linux caps at 128 KiB per argument < 262,144-byte source limit); blocking call cannot observe MCP cancellation |
| parse surface (`genia_parse`) | `hosts/python/parse_adapter.py` | **no** | not exposed as a builtin (E28-2 scope) |
| eval surface (`genia_run`) | CLI `-c` | **no** as value API | only via CLI/subprocess (E28-3 scope) |

## 3. Native proof (experiment, not committed as product code)

```genia
pattern Json(value) = representation_match("json", value)
enc(o) = some(t, _) -> t | err(_, _) -> "{\"internal\":1}"
route(req) =
  {method: "tools/list"} -> {tools: ["genia_capabilities", "genia_parse"]} |
  _ -> {error: "unknown"}
handle(d) =
  some(Json(req), _) -> enc(json_encode(route(req))) |
  err(reason, _) -> enc(json_encode({error: reason}))
main(args) = stdin |> lines |> map(json_decode) |> map(handle)
  |> each((t) -> writeln(stdout, t)) |> run
```

Piping `{"method":"tools/list"}`, `{"x":1}`, `{bad` produced the tools object,
`{"error":"unknown"}`, and an error line. **Answer: yes** — decode → facet
pattern → map-pattern dispatch → value construction → encode → stdout can live
in Genia. Remaining native-side gaps are framing shape (§2, compact JSON) and
per-line byte bounds, not dispatch/validation/composition.

## 4. E28-1 scope

Authorized by the contract and #702, nothing more:

1. `mcp.genia` — stdin→decode→validate→dispatch→capability value→encode→stdout.
2. `genia_capabilities` exactly per contract §2.3 (closed shape, array order).
3. Discovery lists exactly the three tool names. `genia_parse`/`genia_run` are
   discoverable but **not implemented**: a call returns the fixed
   `internal_error`/`phase: "adapter"` envelope message "tool not implemented
   in this server revision". This is an E28-1 inert boundary; it is not parse or
   run behavior. (Decision requested — see §8.)
4. Unknown tool, unknown protocol version, malformed JSON, unknown arguments →
   MCP protocol errors, per contract §2.2, produced natively.
5. A minimal launcher so `genia mcp.genia` (and later a `.mcp.json` command) can
   start the same server; no VS Code-specific code.

Explicitly not in E28-1: parsing, execution, workers, limits enforcement,
cancellation, timeouts, cross-mode evidence, VS Code acceptance, C++.

## 5. Host-dependency inventory (E28-1)

Classes: A intrinsic host; B Genia capability gap; C native Genia.

| # | Responsibility | Class | Evidence | Proposed host API / authority | Tests | Removal condition |
|---|---|---|---|---|---|---|
| 1 | MCP framing glue: line read, decode, validate, dispatch, tool discovery | C | §3 proof | none | behavioral stdio tests | n/a — must stay native |
| 2 | `genia_capabilities` value, tool array, profile constants, envelope construction, fixed error selection | C | §3 proof, maps/arms verified | none | exact-shape + order tests | n/a |
| 3 | Closed request/schema validation | C | `json_schema` + `additionalProperties:false` exist | none | closed-schema tests | n/a |
| 4 | JSON response single-line framing | C (workaround) + B | `split/trim/join` gives single-line; not byte-compact | none for single-line | framing test: no embedded newline | remove workaround when a compact-encode option exists |
| 5 | Byte-compact JSON (`separators=(",",":")`) | B | `json_encode` fixed pretty/sorted | none in E28-1 | recorded gap only | reusable compact JSON encoder (general utility beyond MCP) |
| 6 | MCP protocol version `2026-07-28` fixed check | C | string compare | none | version-reject test | n/a |
| 7 | Contract revision (40-hex) for capabilities | A/B (open) | Genia has no build-info builtin; must not read request paths or describe a dirty tree | launcher passes one fixed value (see §8 Q2) | format test | a reusable build-identity facility |
| 8 | Launching the worker (`genia_run`) | A (+B) | `execution.process` exists but has no Genia bootstrap | host-provisioned `execution.process` capability bound to one symbol | E28-3 | capability bootstrap API |
| 9 | Hard deadline, kill+reap, incremental byte bounds | A | already in `process_transport.py` | reuse, unchanged | existing 115 tests | n/a |
| 10 | Source to worker stdin / >128 KiB | B | child stdin is EOF; argv cap 128 KiB/arg | none in E28-1 | recorded gap | `execution.process` stdin option |
| 11 | MCP cancellation of in-flight worker | B | blocking call; no signals/handles | none in E28-1 | recorded gap | non-blocking/cancellable process handle |
| 12 | Per-line/stdin byte bounds | B | `lines` materializes whole line | none in E28-1 | recorded gap | bounded line reader |
| 13 | MCP Python SDK | **not adopted** | items 1–6 are native-capable; SDK would own dispatch | n/a | n/a | n/a |
| 14 | Launcher (`genia mcp.genia` entry) | A | existing CLI file mode | existing CLI | launch test | n/a |

Items 8–12 are recorded for E28-3/E28-4 and the final audit; E28-1 adds no host
code for them.

## 6. Python code permitted in E28-1

None beyond test harness code and, if needed, a one-function launcher constant
for item 7. No Python dispatch, schema, policy, or envelope code. Drift is caught
by a behavioral test that runs `mcp.genia` with the Python package's MCP-named
modules absent, plus an architecture test asserting no Python module defines the
tool names or envelope literals (AST string-constant scan, not filename grep).

## 7. Failing-test plan (next phase)

1. `genia_capabilities` response deep-equals the contract §2.3 shape; array order
   fixed; same bytes on repeated calls (stateless, deterministic).
2. Discovery returns exactly the three names; no resources/prompts.
3. Unknown tool, other protocol version, malformed JSON, extra argument
   properties, non-object arguments → protocol errors; no crash; server remains
   usable for the next line.
4. Every response is exactly one line on stdout; stderr carries no protocol data.
5. `genia_parse`/`genia_run` calls return the fixed unimplemented envelope.
6. Architecture/drift: Python sources contain no tool-name/envelope/dispatch
   constants; `mcp.genia` is the sole owner.
7. No-authority: server source has no `import` of file/web/process modules; run
   with cwd elsewhere and empty environment gives identical output.
8. Regression: existing doc-sync and spec suites unchanged.

## 8. Decisions and blockers for approval

- **Q1:** Approve the inert `genia_parse`/`genia_run` behavior in §4.3 (alternative:
  protocol "unknown tool" error, but that contradicts the exact three-name discovery).
- **Q2:** How `contract_revision` is supplied: recommended a server-owned constant in
  `mcp.genia` updated by the release process, guarded by a test that it is 40
  lowercase hex; alternative is a launcher-provided value.
- **Q3:** Accept single-line (not byte-compact) framing as the E28-1 bar and
  record byte-compactness as a gap.
- **BLOCKED:** MCP `2026-07-28` transport text (exact stdio framing, request
  envelope, required fields) could not be fetched — `modelcontextprotocol.io` is
  denied by the egress proxy. Wire-level field names must be verified against the
  spec before the test phase; I will not guess them. Provide the spec text or
  allow the domain.
- **Process:** `AGENTS.md` forbids mixing design and implementation in one step
  and requires stopping between phases; this commit is the design phase. The
  pre-flight (#1055 covers R28) should confirm no separate #702 pre-flight is
  required.

## 9. Future C++ host needs (recorded, not claimed)

To run the same `mcp.genia`: `stdin |> lines`, `json_decode`/`json_encode`,
`representation_match`, map/arm dispatch, `writeln(stdout, …)`, and — for E28-3 —
a provisioned `execution.process`. C++ currently supports strict JSON and pipe
mode (R26/R27); no MCP or C++ parity is claimed.
