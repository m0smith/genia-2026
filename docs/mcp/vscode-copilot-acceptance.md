# VS Code + GitHub Copilot acceptance run (R28 release gate)

Status: **Procedure; not yet executed.** Contract section 12.2 requires one authentic run of the
repository-configured Genia MCP server from VS Code with GitHub Copilot before R28 may be called complete
(ledger R28-H39). The audit environment had no VS Code, no GUI, and no Copilot authentication, so nobody
has run it. Official-SDK and Inspector runs do **not** substitute. Expected effort: about 15 minutes.

The run also decides ledger R28-H36: which protocol path VS Code uses (`server/discover`, the stateless
revision this server implements, or the legacy `initialize`, which it rejects).

## Before you start

- A Linux or macOS machine with `git`, and `uv` (or Python 3.10+) on `PATH`; VS Code (stable) with the
  GitHub Copilot and Copilot Chat extensions, signed in, Agent mode available.
- Do not paste tokens, account names, e-mail addresses, or home-directory paths into the record. Redact
  them. Do not attach screenshots.

## Steps

1. **Revision.** `git clone https://github.com/m0smith/genia-2026.git && cd genia-2026`, check out the
   release-candidate commit, and run `git rev-parse HEAD` (this is `repository_revision`). Confirm there is
   no `.vscode/mcp.json` (`ls .vscode/mcp.json` must fail): the checked-in configuration is the root `.mcp.json`.
2. **Open and trust.** `code .`, and when VS Code asks, trust the workspace folder (`.mcp.json` is executable
   configuration). Record the VS Code version (`code --version`) and the Copilot extension version (Extensions view).
3. **Discovery.** Open the MCP servers list (Command Palette: `MCP: List Servers`). Record whether `genia`
   appears **without any edit** (`mcp_json_discovered`). If it does not, record `no`, stop, and report
   exactly what VS Code showed. (Do not add `.vscode/mcp.json` to the repository: the contract allows it
   only when verified to be necessary, which would be a finding.)
4. **Start.** Start the `genia` server from that list. Record what state VS Code shows (`server_state_shown`),
   for example `Running`. If it fails, copy the one-line error from the server's output (`Show Output`).
5. **Protocol path.** In the MCP output log (raise the log level to trace if VS Code offers it, for example
   with `Developer: Set Log Level`), find the **first request VS Code sent** and record it as
   `negotiation_path`: `server/discover` or `initialize`. Copy the few log lines that show it into
   `host_log_excerpt` (redacted).
6. **Tools.** Open Copilot Chat in **Agent** mode and open the tools picker. Record the `genia` tools
   (`tools_visible` must be exactly `genia_capabilities, genia_parse, genia_run`). Record whether VS Code
   shows any MCP resources or prompts for this server (`resources_or_prompts_visible`: `none` expected;
   for example `MCP: Browse Resources` is empty).
7. **Capabilities.** In Agent mode ask: *Use the genia MCP tool genia_capabilities and show me the result.*
   Confirm the tool call was approved and made by the host.
8. **Parse, diagnose, repair.** Ask: *Call the genia MCP tool genia_parse with exactly this source:* followed
   by the **broken** program from `docs/mcp/demo.md` (the block labeled `demo-broken`). Record that the host
   made the call and the diagnostic it showed (`invalid_source_feedback`: expect `parse_error` at character
   offset 171). Then ask it to call `genia_parse` with the **fixed** program (`demo-fixed`) and record the
   success (`corrected_source_parsed`).
9. **Run.** Ask: *Call the genia MCP tool genia_run with the same corrected source.* Record the outcome
   (`run_result`: expect value, stdout `2`, two lines of stderr, exit code `0`) and whether VS Code shows
   the value, stdout and stderr separately (`channel_separation_visible`: `yes`, `no`, or `not exposed by the host`).
10. **Disconnect.** Stop the server (`MCP: Stop Server`) or quit VS Code, then run
    `pgrep -af "mcp_launch|mcp_host|mcp_worker"`. It must print nothing (`clean_lifecycle_after_disconnect`).
11. **Record.** Fill `docs/mcp/acceptance/vscode-copilot-evidence.md` (the fenced `evidence` block only,
    `status: EXECUTED`, one value per field, no secrets), and run
    `uv run pytest tests/unit/test_r28_release_gate.py -q`. Commit the file to the release-candidate
    branch and return the commit.

## What happens next

- `negotiation_path: server/discover`, `disposition: PASS`, all fields filled: R28-H39 closes, R28-H36 is
  dispositioned as an accepted compatibility limitation (legacy-only clients cannot connect; no legacy
  state is added), and the completion synchronization listed in `docs/releases/R28.md` follows as a
  separate reviewed change.
- `negotiation_path: initialize` (VS Code cannot connect): **stop.** R28 is not complete and nothing is
  implemented. The decision is the contract-amendment proposal in ledger R28-H36.
- Any other failure: record it as `FAIL` with the evidence; it is a release blocker until understood.
