# VS Code + GitHub Copilot acceptance evidence (R28-H39, R28-H36)

Chronological record of authentic VS Code + GitHub Copilot runs. **Run 1 failed** at protocol
initialization and is preserved as it happened; **run 2** (after the contract amendment A5 that adds the
`2025-11-25` compatibility era) is **not yet executed**. The gate test
`tests/unit/test_r28_release_gate.py` reads this file: the *latest* run governs the release, and a run is
exactly one of **not executed**, **executed and failed**, or **executed and passed**. Procedure:
`docs/mcp/vscode-copilot-acceptance.md`.

Rules: one value per field, no secrets, no personal data, no screenshots. Never edit a run after it was
recorded except to fix a transcription error; add a new run instead. A field a failed run could not reach
says `not reached`; a fact the run's author did not record says `not recorded`. Both are allowed **only** in
a run with `disposition: FAIL`, never in a passing run.

## Run 1: 2026-10-05, failed at initialization (before amendment A5)

Environment (recorded by the repository owner): VS Code `1.138.0 (Universal)`, commit
`7debcd0e2acdea1c52de81bf9ee1620444407dda`, dated `2026-09-15T07:24:32Z`, Electron `42.10.0`, Node.js
`24.18.1`; macOS / Darwin x64 `24.6.0`; GitHub Copilot Chat extension `0.66.0` (embedded `@github/copilot`
`1.0.84-4`, `@github/copilot-sdk` `1.0.13`). Server under test: the E28-6 release-candidate branch before the
amendment (the server then implemented only MCP 2026-07-28).

What happened: VS Code discovered `genia-2026/.mcp.json` automatically (no `.vscode/mcp.json` existed), listed
`genia` as `Stopped`, and on start launched `uv run --no-project --no-python-downloads python
hosts/python/mcp_launch.py` (Connection state: Running within 11 ms, so launcher startup and the stdio
transport work on macOS). VS Code then sent the legacy handshake, and the server answered `-32601`:

```text
2026-10-05 09:49:21.338 [info] Starting server genia
2026-10-05 09:49:21.338 [info] Connection state: Starting
2026-10-05 09:49:21.354 [info] Starting server from LocalProcess extension host
2026-10-05 09:49:21.365 [debug] Server command line: uv run --no-project --no-python-downloads python hosts/python/mcp_launch.py
2026-10-05 09:49:21.365 [info] Connection state: Starting
2026-10-05 09:49:21.376 [info] Connection state: Running
2026-10-05 09:49:21.377 [debug] [editor -> server] {"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-11-25","capabilities":{"roots":{"listChanged":true},"sampling":{},"elicitation":{"form":{},"url":{}},"tasks":{"list":{},"cancel":{},"requests":{"sampling":{"createMessage":{}},"elicitation":{"create":{}}}},"extensions":{"io.modelcontextprotocol/ui":{"mimeTypes":["text/html;profile=mcp-app"]}}},"clientInfo":{"name":"Visual Studio Code","version":"1.138.0"}}}
2026-10-05 09:49:22.249 [debug] [server -> editor] {"error":{"code":-32601,"message":"Method not found"},"id":1,"jsonrpc":"2.0"}
2026-10-05 09:49:22.251 [error] Error: MPC -32601: Method not found
```

Consequences: VS Code 1.138.0 does **not** negotiate with `server/discover`; it sends `initialize` for
protocol `2025-11-25`; the pre-amendment server rejected it; tool discovery, parse, run, and the lifecycle
checks were therefore never reached. The same trace also shows what this client advertises (`roots`,
`sampling`, `elicitation`, `tasks`, the MCP Apps UI extension) and that it sends no `_meta`.

```evidence run=1
status: EXECUTED
executed_on: 2026-10-05
vscode_version: 1.138.0
copilot_extension_version: 0.66.0
repository_revision: not recorded
failed_at: initialize
workspace_trusted: not recorded
mcp_json_discovered: yes
server_state_shown: Stopped, then Running (process started) until initialize failed
negotiation_path: initialize
negotiated_protocol_version: none
host_log_excerpt: [editor -> server] initialize protocolVersion 2025-11-25; [server -> editor] error -32601 Method not found
tools_visible: not reached
resources_or_prompts_visible: not reached
parse_invoked_from_host: not reached
invalid_source_feedback: not reached
corrected_source_parsed: not reached
run_invoked_from_host: not reached
run_result: not reached
channel_separation_visible: not reached
clean_lifecycle_after_disconnect: not reached
disposition: FAIL
```

Run 1 also shows (at the strength the trace supports) that on macOS the `.mcp.json` discovery, the `uv`
launcher, the Genia MCP process start, and JSON-RPC request/response over stdio work; it does not show any
Genia tool execution on macOS (ledger R28-H43).

## Run 2: after amendment A5, on revision `66b505949cb17a4a017291115efb8a1cc5970cab`

Executed by the repository owner on 2026-10-05, same machine and versions as run 1 (macOS, Darwin x64 24.6.0,
VS Code `1.138.0`, GitHub Copilot Chat `0.66.0`), against commit
`66b505949cb17a4a017291115efb8a1cc5970cab` of the PR #1082 branch. Reported by the owner (the raw VS Code
trace for this run was not supplied; fields it would have filled say `not recorded`):

- VS Code discovered `.mcp.json`, started Genia, and the server stayed **Running**.
- VS Code reported `Discovered 3 tools`: `genia_capabilities`, `genia_parse`, `genia_run`.
- `genia_capabilities` was invoked successfully.
- `genia_parse` on the broken program returned the expected `parse_error` at character offset 171, and
  `genia_parse` on the corrected program succeeded.
- **`genia_run` of the canonical demo failed** with the sanitized adapter error:

```json
{"schema_version": "genia.mcp.v1", "status": "error", "result": null,
 "error": {"kind": "internal_error", "message": "Internal error while executing", "phase": "adapter"}}
```

Consequences: the amendment A5 protocol compatibility is demonstrated in authentic VS Code (ledger R28-H36
acceptance criteria met). The acceptance run still **fails**, at `genia_run` (ledger R28-H39, new finding
R28-H47: the governed worker does not run on macOS). On the same Mac `uv run pytest
tests/unit/test_r28_mcp_run.py -vv -s` gave 53 failed, 17 passed, 3 skipped: almost every execution test
returned `internal_error` (a worker bootstrap failure; the Linux evidence is unaffected), and the lifecycle
tests failed because the test helper assumed Linux `/proc` (`FileNotFoundError: /proc`).

```evidence run=2
status: EXECUTED
executed_on: 2026-10-05
vscode_version: 1.138.0
copilot_extension_version: 0.66.0
repository_revision: 66b505949cb17a4a017291115efb8a1cc5970cab
failed_at: run
workspace_trusted: not recorded
mcp_json_discovered: yes
server_state_shown: Running
negotiation_path: initialize
negotiated_protocol_version: 2025-11-25
host_log_excerpt: not recorded (owner reported: server Running, Discovered 3 tools, tool calls succeeded; the raw trace was not supplied)
tools_visible: genia_capabilities, genia_parse, genia_run
resources_or_prompts_visible: not recorded
parse_invoked_from_host: yes
invalid_source_feedback: parse_error at character offset 171
corrected_source_parsed: yes
run_invoked_from_host: yes
run_result: FAIL: error internal_error (phase adapter), no value
channel_separation_visible: not applicable (the run failed)
clean_lifecycle_after_disconnect: not reached
disposition: FAIL
```

## Run 3: after the macOS execution repair (pending)

**NOT EXECUTED.** To be performed by the repository owner on the repaired branch with
`docs/mcp/vscode-copilot-acceptance.md`, after the macOS verification commands in that document pass. Do
not fill any field from an SDK client, the Inspector, documentation, or reasoning.

```evidence run=3
status: NOT EXECUTED
executed_on:
vscode_version:
copilot_extension_version:
repository_revision:
failed_at:
workspace_trusted:
mcp_json_discovered:
server_state_shown:
negotiation_path:
negotiated_protocol_version:
host_log_excerpt:
tools_visible:
resources_or_prompts_visible:
parse_invoked_from_host:
invalid_source_feedback:
corrected_source_parsed:
run_invoked_from_host:
run_result:
channel_separation_visible:
clean_lifecycle_after_disconnect:
disposition:
```

## Notes

(Free text after each run: OS and versions, startup time, anything surprising.)
