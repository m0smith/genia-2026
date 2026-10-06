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

## Run 3: after the macOS execution repair, on revision `0ff058a28e488275f344ee24bbd12d072bd3e9cc`

Executed by the repository owner on macOS (Darwin x64 24.6.0) from the repository-configured `.mcp.json`, against
commit `0ff058a28e488275f344ee24bbd12d072bd3e9cc` of the PR #1082 branch, after the owner's macOS verification
(`1141 passed, 18 skipped, 0 failed` for `pytest tests/unit -k "r28 or mcp"` at `d0e4f2a4`, ledger R28-H47/H48;
CI green on the branch head). VS Code `1.138.0` and Copilot Chat `0.66.0` are the owner's environment from runs 1 and 2
(the run-3 report did not restate them). The owner reported **PASS** with these observations (the raw VS Code
trace for this run was not supplied; the entries below are the owner's reported results, not log lines):

- VS Code started the `genia` MCP server successfully and reported `Discovered 3 tools`.
- **`genia_capabilities` (Copilot Agent): PASS.** MCP protocol `2025-11-25`; transport `stdio`; tools exactly
  `genia_capabilities`, `genia_parse`, `genia_run`; execution profile `source-only-isolated-v1`; timeout `5000` ms;
  filesystem, environment, configuration, secrets, and network all `false`.
- **Broken canonical demo through `genia_parse`: PASS.** `status: error`, `kind: parse_error`, `phase: parse`,
  character offset `171`.
- **Corrected canonical demo through `genia_parse`: PASS.** `status: ok`, `kind: parsed`, AST returned.
- **Corrected canonical demo through Copilot Agent `genia_run`: PASS.** `status: ok`, `kind: completed`, `exit_code: 0`,
  stdout exactly `"2\n"`, stderr exactly `"record_validation_failed\nrecord_validation_failed\n"`; the rendered value
  contains the clean records Ada and Edsger and the two expected structured validation diagnostics; value, stdout,
  and stderr stayed separate.
- After stopping the MCP server, `pgrep -af "mcp_launch|mcp_host|mcp_worker"` returned no processes.

How each field was established (stated at its actual strength; nothing below is promoted beyond the owner's report):

- `negotiated_protocol_version: 2025-11-25` is the value `genia_capabilities` returned as `mcp.protocol_version`
  (A5.6: the revision serving the request), and `negotiation_path: initialize` follows from that, because only
  `initialize` selects that era (the first authentic trace, run 1, shows VS Code sends `initialize` for `2025-11-25`).
- `workspace_trusted: yes` and `server_state_shown: Running`: the server started from the workspace's `.mcp.json`
  (VS Code does not start a workspace MCP server from an untrusted workspace); the owner did not separately
  report the trust prompt.
- `resources_or_prompts_visible: none`: the server advertises only `capabilities: {tools: {}}` and answers every
  `resources/*` and `prompts/*` request `-32601` (automated: conformance matrix K5/K6), and VS Code reported exactly
  `Discovered 3 tools`; the owner did not report separately opening the VS Code resources or prompts views.
- `executed_on` is the date of the owner's report; the run took place on or just before it.

```evidence run=3
status: EXECUTED
executed_on: 2026-10-06
vscode_version: 1.138.0
copilot_extension_version: 0.66.0
repository_revision: 0ff058a28e488275f344ee24bbd12d072bd3e9cc
failed_at: none
workspace_trusted: yes
mcp_json_discovered: yes
server_state_shown: Running
negotiation_path: initialize
negotiated_protocol_version: 2025-11-25
host_log_excerpt: VS Code reported "Discovered 3 tools"; genia_capabilities returned mcp.protocol_version 2025-11-25, transport stdio
tools_visible: genia_capabilities, genia_parse, genia_run
resources_or_prompts_visible: none
parse_invoked_from_host: yes
invalid_source_feedback: status error, kind parse_error, phase parse, character offset 171
corrected_source_parsed: yes
run_invoked_from_host: yes
run_result: status ok, kind completed, exit_code 0, stdout "2\n", stderr "record_validation_failed\nrecord_validation_failed\n", rendered value with records Ada and Edsger and two structured validation diagnostics
channel_separation_visible: yes
clean_lifecycle_after_disconnect: yes
disposition: PASS
```

Run 3 satisfies contract section 12.2 items 1 to 8 as follows: (1) discovery, start, and a supported negotiated
revision; (2) exactly the three tools, no other tool, resource, or prompt advertised; (3) `genia_capabilities`;
(4) `genia_parse` diagnostic and success; (5) `genia_run` with value, stdout, and stderr separately; (6) the
recorded loop invalid source, `genia_parse` feedback, corrected source, successful `genia_run`; (7) a program
writing both stdout and stderr did not corrupt MCP framing; (8) the configuration and the observed process hold
no authority beyond the fixed profile (capabilities report all authority flags `false`; no worker or launcher
process remained).

## Notes

(Free text after each run: OS and versions, startup time, anything surprising.)

### macOS verification of SHA `48467fcd` (owner; not a VS Code run, not an evidence run)

Worker probe `VERDICT OK`; Darwin `setrlimit(RLIMIT_AS)` raises `ValueError: current limit exceeds maximum limit`;
supervised `1 + 2` returns `3`; `uv run pytest tests/unit/test_r28_mcp_run.py -vv`: 64 passed, 5 failed, 4 skipped.
All normal `genia_run` tests pass; the 5 failures were the lifecycle helper not finding the worker through the
Darwin `ps` backend (ledger R28-H47 sub-finding). Repaired and re-verified at `c4cf1743`: `process_probe.py` `VERDICT OK`, and the five tests pass (`-k "deadline or cancel or other_requests"`: 8 passed, 1 skipped). This is supporting
evidence for run 3 only; it does not replace it. Full R28 suite on the Mac at `44ec62cd`: 1135 passed, 18 skipped, 3 failed
(test assumptions and platform facts, ledger R28-H48; none is a `genia_run` failure); the three affected files then passed at `b65e7218` (188 passed, 7 skipped), and the full R28/MCP suite passed at `d0e4f2a4` (1141 passed, 18 skipped, 0 failed).
