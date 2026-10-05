# VS Code + GitHub Copilot acceptance run (R28 release gate)

Status: **Run 1 failed at `initialize` (2026-10-05); run 2 (same day, after amendment A5) failed at `genia_run`;
run 3 (after the macOS execution repair) is pending.** Contract section 12.2 requires one authentic run of the
repository-configured Genia MCP server from VS Code with GitHub Copilot before R28 may be called complete
(ledger R28-H39).

- **Run 1** (VS Code `1.138.0`, Copilot Chat `0.66.0`, macOS): VS Code sent `initialize` for protocol
  `2025-11-25`; the then stateless-only server answered `-32601`. Fixed by amendment A5
  (`docs/design/r28-genia-mcp-contract-threat-model.md` section 18).
- **Run 2** (same machine, revision `66b50594`): negotiation, three tools, `genia_capabilities`, and both
  `genia_parse` calls (`parse_error` at offset 171, then success) worked in authentic VS Code, so the protocol
  repair (ledger R28-H36) is demonstrated and closed. The canonical `genia_run` returned the sanitized
  `internal_error`: the governed worker did not run on macOS (ledger R28-H47).
- **Run 3** is the rerun after the H47 repair. It must be preceded by the macOS verification below.

Runs 1 and 2 stay in `docs/mcp/acceptance/vscode-copilot-evidence.md` as history and are never edited; run 3 is a
new `evidence run=3` block, and the **latest** run governs the release gate. Official-SDK and Inspector runs do
**not** substitute for it. Expected effort: about 20 minutes.

Expected on run 3: `negotiation_path: initialize`, `negotiated_protocol_version: 2025-11-25` (or
`server/discover` / `2026-07-28` if a future VS Code uses the modern path); both are accepted.

## Step 0: macOS verification (before VS Code)

On the Mac, in the repository, on the repaired branch (`git pull`):

```bash
# 1. One-command diagnosis of the governed worker (prints a JSON report and a final VERDICT line).
uv run --no-project --no-python-downloads python tools/mcp_diagnostics/worker_probe.py
# 2. The execution suite that failed (53 failed on run 2). Expect: Linux-only namespace tests SKIPPED, nothing failed.
uv run pytest tests/unit/test_r28_mcp_run.py -vv
# 3. The portability tests and the lifecycle/cancellation/timeout rows on macOS.
uv run pytest tests/unit/test_r28_mcp_portability.py tests/unit/test_r28_mcp_run_supervisor.py \
  tests/unit/test_r28_mcp_run_worker.py tests/unit/test_r28_mcp_conformance_lifecycle.py \
  tests/unit/test_r28_mcp_stdio_lifecycle.py tests/unit/test_r28_mcp_stdio_launch.py \
  tests/unit/test_r28_mcp_compat_conformance.py tests/unit/test_r28_mcp_conformance_security.py -q
```

Return the **whole output** of command 1 (especially the `VERDICT` line and `limits`) and any failure from 2 and 3.
If command 1 ends `VERDICT OK`, `genia_run` works on this Mac. If it names a failing limit **other than**
`RLIMIT_AS`, stop and report it: that is a contract question, not something to patch around. Do not start VS
Code until commands 1 and 2 pass.

## Before you start

- A Linux or macOS machine with `git`, and `uv` (or Python 3.10+) on `PATH`; VS Code (stable) with the
  GitHub Copilot and Copilot Chat extensions, signed in, Agent mode available.
- Do not paste tokens, account names, e-mail addresses, or home-directory paths into the record. Redact
  them. Do not attach screenshots.

## Steps (the owner's third run)

1. **Check out and update.** `git fetch origin claude/bold-euler-jb7uoy && git checkout claude/bold-euler-jb7uoy &&
   git pull`, then `git rev-parse HEAD` (this is `repository_revision`). Confirm there is no
   `.vscode/mcp.json` (`ls .vscode/mcp.json` must fail): the checked-in configuration is the root `.mcp.json`.
2. **Restart VS Code** completely (quit and reopen the folder: `code .`), trust the workspace when asked
   (`.mcp.json` is executable configuration), and record the VS Code version (`code --version`) and the
   Copilot extension version (Extensions view). Raise the log level to trace if offered
   (`Developer: Set Log Level`).
3. **Start the `genia` server** from `MCP: List Servers` (it should appear without any edit:
   `mcp_json_discovered`). Record the state shown (`server_state_shown`).
4. **Verify initialization succeeds.** In the MCP output log, find the first request VS Code sent
   (`negotiation_path`: `initialize` or `server/discover`) and its response; record the negotiated protocol
   version (`negotiated_protocol_version`) and copy the few redacted log lines into `host_log_excerpt`. If
   initialization fails again, record `failed_at` as the stage that failed (see the gate's stage names) and
   everything after as `not reached`; stop.
5. **Verify exactly three tools:** `genia_capabilities`, `genia_parse`, `genia_run` in the tools picker
   (`tools_visible`), and no MCP resources or prompts (`resources_or_prompts_visible`: `none`).
6. **Capabilities.** In Agent mode ask: *Use the genia MCP tool genia_capabilities and show me the result.*
   The reported `mcp.protocol_version` should equal the negotiated version.
7. **Broken parse.** Ask: *Call the genia MCP tool genia_parse with exactly this source:* followed by the
   **broken** program from `docs/mcp/demo.md` (block `demo-broken`). Record the diagnostic
   (`invalid_source_feedback`; expect `parse_error` at character offset 171).
8. **Corrected parse.** Repeat with the **fixed** program (`demo-fixed`); record the success
   (`corrected_source_parsed`).
9. **Run the canonical demo.** Ask: *Call the genia MCP tool genia_run with the same corrected source.*
   Record the value, stdout `2`, two lines of stderr, and exit code `0` (`run_result`) and whether the
   channels are shown separately (`channel_separation_visible`: `yes`, `no`, or `not exposed by the host`).
10. **Stop the server** (`MCP: Stop Server`) or quit VS Code.
11. **Verify process cleanup.** `pgrep -af "mcp_launch|mcp_host|mcp_worker"` must print nothing
    (`clean_lifecycle_after_disconnect`).
12. **Provide the evidence.** Fill the `evidence run=3` block of
    `docs/mcp/acceptance/vscode-copilot-evidence.md` (`status: EXECUTED`, every field, `failed_at: none` on
    a pass, no secrets, no screenshots, nothing from an SDK client or the Inspector), run
    `uv run pytest tests/unit/test_r28_release_gate.py -q`, commit the file, and return the commit.

## What happens next

- Run 3 with `disposition: PASS`, `failed_at: none`, a negotiation path the contract allows, exactly three tools,
  no resources or prompts, parse and run accepted, and a clean disconnect: R28-H39 and R28-H47 close; the
  completion synchronization listed in `docs/releases/R28.md` follows as a separate reviewed change.
- Run 3 fails: record it as a new run (never edit earlier runs). The failing stage is the next finding; R28 stays
  In Progress.
