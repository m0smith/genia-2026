# VS Code + GitHub Copilot acceptance run (R28 release gate)

Status: **Run 1 executed 2026-10-05 and FAILED at `initialize`; run 2 (the post-amendment rerun) is
pending.** Contract section 12.2 requires one authentic run of the repository-configured Genia MCP server
from VS Code with GitHub Copilot before R28 may be called complete (ledger R28-H39). Run 1 (VS Code
`1.138.0`, Copilot Chat `0.66.0`, macOS) found the server and started it, but VS Code sent `initialize` for
protocol `2025-11-25`, which the then stateless-only server rejected; no tool was reached. Contract
amendment A5 (`docs/design/r28-genia-mcp-contract-threat-model.md` section 18) now serves that
`2025-11-25` era natively. Official-SDK and Inspector runs do **not** substitute for run 2. Run 1 stays in
`docs/mcp/acceptance/vscode-copilot-evidence.md` as history and is never edited; run 2 is a new
`evidence run=2` block, and the **latest** run governs the release gate. Expected effort: about 15 minutes.

Expected on run 2: `negotiation_path: initialize`, `negotiated_protocol_version: 2025-11-25` (or
`server/discover` / `2026-07-28` if a future VS Code uses the modern path); both are accepted.

## Before you start

- A Linux or macOS machine with `git`, and `uv` (or Python 3.10+) on `PATH`; VS Code (stable) with the
  GitHub Copilot and Copilot Chat extensions, signed in, Agent mode available.
- Do not paste tokens, account names, e-mail addresses, or home-directory paths into the record. Redact
  them. Do not attach screenshots.

## Steps (the owner's second run)

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
12. **Provide the evidence.** Fill the `evidence run=2` block of
    `docs/mcp/acceptance/vscode-copilot-evidence.md` (`status: EXECUTED`, every field, `failed_at: none` on
    a pass, no secrets, no screenshots, nothing from an SDK client or the Inspector), run
    `uv run pytest tests/unit/test_r28_release_gate.py -q`, commit the file, and return the commit.

## What happens next

- Run 2 with `disposition: PASS`, `failed_at: none`, a negotiation path the contract allows
  (`initialize` with `2025-11-25`, or `server/discover` with `2026-07-28`), exactly three tools, no
  resources or prompts, parse and run accepted, and a clean disconnect: R28-H39 closes and R28-H36 closes as
  fixed; the completion synchronization listed in `docs/releases/R28.md` follows as a separate reviewed change.
- Run 2 fails: record it as a new run (never edit run 1). The failing stage is the next finding; R28 stays
  In Progress.
