# Claude Code and Codex MCP client acceptance — 2026-10-07

Status: **Claude Code PASS; Codex BLOCKED.**

This record preserves two authentic client observations made against the Genia MCP surface after amendments A6/A7. It does not change or define Genia semantics. `GENIA_STATE.md` remains final authority.

## Claude Code — PASS

Environment reported by the client:

- Client: Claude Code, VS Code extension.
- Extension version: not conclusively established; local extension directories included 2.1.289 and 2.1.292.
- OS: macOS 15.7.9 (24G830), x86_64.
- Repository HEAD: `31291459cb377b4f7d2a5a4e69c718773eec9bbe`.
- MCP server revision reported by capabilities: `87537e3f8b22c5167b7128df42f77103a3a66a48`.
- The client reported that the repository `.mcp.json` started the server.

The client could call all four advertised tools:

- `genia_capabilities`
- `genia_parse`
- `genia_run`
- `genia_language_profile`

It consulted `genia_language_profile` before generating source and reported the profile's implemented guidance: branching by pattern matching rather than an `if` expression, no loop forms, recursion with tail-call optimization, first-match pattern dispatch, and the `open` requirement for a multi-clause function's first clause.

The client generated and parsed:

```genia
open gcd(x, 0) = x
gcd(x, y) = gcd(y, x % y)
gcd(48, 18)
```

`genia_parse` returned `ok` with an `OpenFuncDef` containing two clauses followed by a call. `genia_run` returned `ok` / `completed`, rendered value `6`, exit code 0, and empty stdout/stderr.

The client then tested intentionally foreign-looking source:

```genia
gcd(a,b) = if b == 0 then a else gcd(b, a % b)
```

`genia_parse` returned `ok`, but the AST did not represent a conditional: the function body was `Var("if")` and subsequent tokens became separate top-level expressions. `genia_run` returned the normalized `runtime_error`. Using the language profile and AST, the client repaired the source to pattern-matched clauses and again obtained `6`.

Observed limitations of this acceptance run:

1. Parse success alone did not establish that the parsed structure represented the author's intended conditional. Clients should not treat `status: ok` as semantic-intent validation.
2. The language profile already contains a GCD example, so this run proves profile use and execution but is not independent evidence of novel algorithm synthesis.
3. The server revision reported by capabilities was older than repository HEAD.
4. The Claude Code extension version was not conclusively identified.

Verdict: **PASS** for authentic four-tool client use, profile discovery, parse, run, and profile-informed repair.

## Codex — BLOCKED

Environment reported during the investigation:

- Client: Codex session; installed CLI reports `codex-cli 0.160.0`.
- OS: macOS 15.7.9 (24G830), Darwin 24.6.0 x86_64.
- Repository HEAD: `31291459cb377b4f7d2a5a4e69c718773eec9bbe`.
- MCP server revision returned by `genia_capabilities`: `87537e3f8b22c5167b7128df42f77103a3a66a48`.
- Installed Genia plugin app id: `asdk_app_6ac531ee29208191b6d67aceec8b81e8`.

The session exposed exactly three callable Genia entries through its tool registry:

- capabilities
- parser
- runner

Calling capabilities returned ordinary result data listing four tool names, including `genia_language_profile`. That result does **not** prove that this connection's MCP `tools/list` response contained four tool descriptors.

The session could not call `genia_language_profile`, so the required MCP language-profile discovery acceptance scenario could not be completed. It nevertheless used parse/run successfully on recursive pattern-dispatched Genia; for example a GCD/LCM-style program parsed and returned `36`.

### Read-only trace

The investigation attempted to locate the first divergence across three layers:

| Layer | Evidence | Result |
|---|---|---|
| Raw same-connection MCP `tools/list` | No raw response or same-connection capture API was available | Unknown |
| `codex_apps` registered Genia catalogue | Local remote-plugin manifests identify the Genia app but contain no tool definitions | Unknown |
| Session-exposed registry | `ALL_TOOLS` / callable entries inspected | Exactly three callable Genia entries |

Additional observations:

- Local Codex configuration contained approval-mode entries for the original three tools. These are approval settings, not evidence of a three-tool allowlist.
- Plugin Management reported inherited default app permission and exposed no registered tool catalogue.
- Read-only inspection of local logs found catalogue-building/cached-catalogue records for other sessions, but none established this session's raw discovery or a rejection of `genia_language_profile`.
- The available tools arrived through the `codex_apps` Genia connector. The investigation did not establish that this session's connector registry was constructed directly from the repository `.mcp.json`.
- The installed CLI version does not establish which Codex component/version constructed this session's connector registry.

Therefore the first divergence remains **unlocated**. The evidence does not establish whether the fourth descriptor was absent from upstream MCP discovery, lost during connector registration, or filtered during session exposure. It also does not establish defect ownership.

Verdict: **BLOCKED**, not FAIL. The intended Codex language-profile acceptance test could not be performed because the required callable tool was unavailable and the current session did not expose enough connector-side evidence to locate why.

## Follow-up boundary

Do not change Genia semantics, parser behavior, runtime behavior, or the MCP contract to compensate for this Codex observation without evidence locating the divergence in Genia.

A future Codex retest should capture, from the same connection:

1. the raw MCP `tools/list` response,
2. the connector's resulting registered Genia descriptor catalogue, and
3. the final session-exposed tool registry/filtering result.

The first differing layer can then determine ownership and whether any Genia change is warranted.
