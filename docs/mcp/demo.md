# Genia MCP demo: validate records, repair a program, run it

This walkthrough starts the Genia MCP server, connects a client, and runs a small
**Outcome-aware validated record pipeline**: some records are valid, some are not, the valid ones are
kept, and each invalid one produces a structured diagnostic instead of crashing the program. Along the
way you submit a program with a syntax error, read the parse diagnostic, repair it, and run it.

It needs nothing beyond the server itself: no files, network, environment variables, or credentials.

Status of each part, so nothing is mistaken for more than it is:

| Part | Status |
|---|---|
| Server over local stdio, exactly four tools (`genia_language_profile` added by amendment A6) | automated in CI |
| Official MCP TypeScript client (default, `auto`, and pinned negotiation) | automated in CI |
| MCP Inspector 2.9.0, command-line mode | manually executed; not run in CI; the web and terminal UIs were not executed |
| VS Code with GitHub Copilot | **verified by an authentic run** (acceptance run 3, macOS: discovery, three tools, parse diagnostic and success, and this demo's `genia_run`); manual, not in CI (`docs/mcp/vscode-copilot-acceptance.md`) |

## Prerequisites

- **Linux or macOS.** Linux is verified in CI; macOS is verified by the owner (the whole MCP test suite, and an authentic VS Code + GitHub Copilot run of this demo; not in CI). On macOS there is no address-space bound and no network namespace (Linux-only hardening). Windows is not supported.
- `git`, and either `uv` (recommended) or Python 3.10 or newer, on `PATH`. Nothing is installed or downloaded when the server starts.
- A **git clone** of the repository (the server reports the clone's commit as its revision; a copy without
  `.git` refuses to start with one line on stderr).
- Node.js 20 or newer, only if you use the official TypeScript client or the Inspector.

## 1. Get and start the server

```bash
git clone https://github.com/m0smith/genia-2026.git
cd genia-2026
scripts/genia-mcp          # waits for a client on stdin; this is normal
```

`scripts/genia-mcp` takes no arguments and works from any directory. Normally the client starts it for
you. Point your client at the **absolute path** of that script (a stdio server with that command), or open
the repository folder in a client that reads the checked-in `.mcp.json`.

The server speaks two MCP protocol revisions and nothing else: **2025-11-25** (the client sends
`initialize`; this is what VS Code and the official TypeScript client's default mode do) and the stateless
**2026-07-28** (per-request `_meta`, `server/discover`). Either connects with no client configuration and
reaches the same three tools. (The TypeScript client's `versionNegotiation` option selects the era: the default `legacy`, `auto`, or a pin; every choice connects.) Any other `initialize` version is rejected.

## 2. Connect a client

**Official TypeScript client** (`@modelcontextprotocol/client` 2.2.0):

```js
const client = new Client({ name: 'demo', version: '0.0.0' });
// Optional: the default (legacy, `initialize` / 2025-11-25), `{ mode: 'auto' }` and
// `{ mode: { pin: '2026-07-28' } }` all connect; `client.getNegotiatedProtocolVersion()` reports which.
await client.connect(new StdioClientTransport({ command: '/absolute/path/to/genia-2026/scripts/genia-mcp' }));
```

**MCP Inspector, command-line mode** (2.9.0). Save a config file with the absolute path, then:

```bash
cat > genia-mcp.json <<'EOF'
{"mcpServers":{"genia":{"type":"stdio","command":"/absolute/path/to/genia-2026/scripts/genia-mcp"}}}
EOF
MCP_INSPECTOR_SECRET_STORE=memory npx @modelcontextprotocol/inspector@2.9.0 --cli \
  --config genia-mcp.json --server genia --protocol-era auto --method tools/list
```

Without `--protocol-era auto` the Inspector uses its default era and connects too (`2025-11-25` via `initialize`; `auto` connects with `2026-07-28`); both list the same tools (three at the time of the manual check; `genia_language_profile` came later, amendment A6).

**VS Code with GitHub Copilot** discovers the repository's `.mcp.json` when the folder is opened and trusted
(verified on macOS with VS Code 1.138.0 and Copilot Chat 0.66.0: it starts `genia`, negotiates `2025-11-25`, and
`Discovered 3 tools`). To repeat the check, follow `docs/mcp/vscode-copilot-acceptance.md`.

## 3. Discover the tools

List the server's tools. There are exactly four, and no resources or prompts:

- `genia_capabilities`: what this server supports and its limits.
- `genia_parse`: parse Genia source; returns the structure or a diagnostic. Never runs the source.
- `genia_run`: run Genia source in a fresh, restricted, disposable worker.
- `genia_language_profile`: Genia's language model (pattern matching instead of `if`, recursion instead of loops, canonical examples) and 14 static scoped maturity/gap facts mapped to STATE; curated, not exhaustive; no arguments.

## 4. Parse a program that has a mistake

Submit this source as the `source` argument of `genia_parse`. It validates four records, but the
`valid_age` rule ends in a dangling `&&`:

```genia demo-broken
records = [
  {id: 1, name: "Ada", age: 36},
  {id: 2, name: "Grace"},
  {id: 3, name: "Alan", age: -4},
  {id: 4, name: "Edsger", age: 72}
]

valid_age(age) = age >= 0 &&

check(record) =
  validate_record(record, {
    id: (r) -> validate_required("id", r),
    name: (r) -> validate_required("name", r),
    age: (r) -> validate_field("age", valid_age, "age between 0 and 150", r)
  })

report = records |> ((items) -> validate_each(items, check)) |> collect_validated

print(length(report.clean))
report.diagnostics |> each((d) -> writeln(stderr, diagnostic_reason(d))) |> run
report
```

`genia_parse` answers with a failed result (`isError: true`) whose structured content is:

```json
{"schema_version": "genia.mcp.v1", "status": "error", "result": null,
 "error": {"kind": "parse_error", "phase": "parse", "message": "Genia source failed to parse at character offset 171"}}
```

The number is a **character offset** into the source you sent. Offset 171 is the end of the
`valid_age` line (line 8): the parser stopped where the right-hand side of `&&` should have been. The
diagnostic carries the offset only, never your source text, a path, or a stack trace.

## 5. Repair it and parse again

Restore the right-hand side, `age <= 150`:

```genia demo-fixed
records = [
  {id: 1, name: "Ada", age: 36},
  {id: 2, name: "Grace"},
  {id: 3, name: "Alan", age: -4},
  {id: 4, name: "Edsger", age: 72}
]

valid_age(age) = age >= 0 && age <= 150

check(record) =
  validate_record(record, {
    id: (r) -> validate_required("id", r),
    name: (r) -> validate_required("name", r),
    age: (r) -> validate_field("age", valid_age, "age between 0 and 150", r)
  })

report = records |> ((items) -> validate_each(items, check)) |> collect_validated

print(length(report.clean))
report.diagnostics |> each((d) -> writeln(stderr, diagnostic_reason(d))) |> run
report
```

`genia_parse` now returns `status: "ok"` with `result.kind: "parsed"` and the program's structure.

## 6. Run the corrected program

Submit the same source to `genia_run`. The result separates **four** things:

- `value.rendered`, the final expression's value (here the report of clean records and diagnostics):

```text demo-value
{clean: [{id: 1, name: "Ada", age: 36}, {id: 4, name: "Edsger", age: 72}], diagnostics: [{index: 1, kind: error, reason: record_validation_failed, context: some({diagnostics: [{field: "age", status: error, reason: "missing required field", context: {field: "age", reason: "missing required field"}}]})}, {index: 2, kind: error, reason: record_validation_failed, context: some({diagnostics: [{field: "age", status: error, reason: "invalid field", context: {field: "age", expected: "age between 0 and 150", actual: -4, reason: "invalid field"}}]})}]}
```

- `stdout`, what the program printed (the number of clean records):

```text demo-stdout
2
```

- `stderr`, what the program wrote to its error stream (one reason per invalid record):

```text demo-stderr
record_validation_failed
record_validation_failed
```

- `exit_code`, `0`: the program completed.

## 7. Reading the result

- `clean` holds the records that passed every rule, with their validated fields (`id`, `name`, `age`).
- `diagnostics` has one entry per rejected record. `index` is the record's position in the input list
  (`1` is Grace, whose `age` is missing; `2` is Alan, whose `age` of `-4` is outside 0 to 150), and the
  nested diagnostics name the field and the reason. Fixing the data, not the program, is the next step.
- `value.rendered` is Genia's canonical debug text for the value. It is meant for people and agents to
  read. It is not a portable serialization: do not parse it as JSON.
- Program output cannot affect the protocol: whatever the program prints, including text that looks like
  protocol messages, arrives as data inside `stdout` or `stderr`.

A program that fails while running (for example by dividing by zero) returns `status: "error"` with
`kind: "runtime_error"` and a fixed message, with no partial output. The server deliberately does not
return the underlying error text, so test unfamiliar programs with `genia_parse` first and keep diagnostics
in your program's own values, as this demo does.

## 8. Optional grounded-evidence example

`examples/mcp/grounded_evidence.genia` is a second checked-in example for the
same `genia_run` tool. It validates client-supplied document literals, chunks
valid documents with Experimental R12 `chunk/2`, and prints one strict JSON
evidence package on stdout. The final value is still Genia debug rendering; use
stdout, not `value.rendered`, as the machine-readable channel.

The example is Python-reference-host MCP behavior only. It adds no MCP tool,
resource, prompt, authority, builtin, parser/evaluator behavior, or Core IR
form. The package includes `ordinary_example_selection_not_r12_retrieve` because
its tiny `exact_term_overlap` pass is ordinary example code, not R12 `retrieve/4`,
not semantic retrieval, not embedding, not reranking, not RAG, and not answer
generation. Answer generation remains the MCP client's job. Document ids and
metadata are client-asserted labels; Genia preserves the supplied provenance
spans but does not verify origin or trust.

Run it directly:

```bash
genia examples/mcp/grounded_evidence.genia
```

Or submit the file's source to `genia_parse`, then `genia_run`. The stdout JSON
contains `version`, `status`, `question`, `documents`, `evidence`, `sources`,
`diagnostics`, and the selection descriptor. Invalid documents, duplicate ids,
and zero-chunk documents appear as indexed diagnostics and do not abort the
package.

## What the server will not do

Source run through `genia_run` cannot read or write files, see environment variables, read
configuration or secrets, use the network, start processes or shell commands, import modules, or read
input. Such source is rejected with `kind: "policy_denied"`. Each run starts in a fresh worker and
nothing carries over between runs. See `docs/mcp/security-and-deployment.md`. This is a defense-in-depth
profile, not a security sandbox and not production multi-tenant isolation.

## Troubleshooting

- **`Unsupported protocol version` when connecting.** Your client requested a revision other than
  `2025-11-25` or `2026-07-28`; the error's `data.supported` lists what the server serves. Older revisions
  are not served.
- **The server exits immediately.** Run `scripts/genia-mcp` in a terminal: it prints one line. Usual
  causes are a copy of the repository without `.git`, `git` missing from `PATH`, or neither `uv` nor
  Python 3.10+ on `PATH`.
- **Nothing appears for about half a second after start.** Startup takes about 0.5 s; wait for the first
  response.
- **`policy_denied`.** The program used something the restricted profile does not provide (files,
  network, processes, imports, configuration, secrets, input).
- **`timeout`.** A run is limited to 5000 ms.
- **`result_limit` / `input_limit`.** Output channels and the returned value are limited to 1,048,576
  bytes each and the whole result to 3,276,800 bytes; source is limited to 262,144 bytes (UTF-8 bytes).
- **Server messages.** The server writes only protocol messages to stdout. Its own diagnostics, if any,
  appear on stderr and in your client's MCP log.
