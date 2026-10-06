# VS Code + GitHub Copilot acceptance run (R28 release gate)

Status: **Run 3 PASSED (authentic, macOS); R28 acceptance is complete.** Contract section 12.2 requires one authentic
run of the repository-configured Genia MCP server from VS Code with GitHub Copilot (ledger R28-H39, closed).

- **Run 1** (VS Code `1.138.0`, Copilot Chat `0.66.0`, macOS) failed at `initialize`: VS Code sent protocol `2025-11-25` to the
  then stateless-only server, which answered `-32601`. Fixed by amendment A5
  (`docs/design/r28-genia-mcp-contract-threat-model.md` section 18).
- **Run 2** (same machine, revision `66b50594`) proved A5 (negotiation, three tools, `genia_capabilities`, both `genia_parse`
  calls) and failed at `genia_run`: the governed worker did not run on macOS (ledger R28-H47, fixed).
- **Run 3** (same machine, revision `0ff058a28e488275f344ee24bbd12d072bd3e9cc`) **passed**: negotiation `initialize` /
  `2025-11-25`, `Discovered 3 tools`, `genia_capabilities`, broken then corrected `genia_parse`, and `genia_run` of the
  corrected canonical demo through Copilot Agent (stdout `"2\n"`, two `record_validation_failed` stderr lines, channels
  separate), then a clean shutdown (no `mcp_launch`, `mcp_host`, or `mcp_worker` process).

All three runs stay in `docs/mcp/acceptance/vscode-copilot-evidence.md` and are never edited; the **latest** run governs the
release gate (`tests/unit/test_r28_release_gate.py`). The steps below remain the reproducible procedure for anyone who wants to
repeat the run (for a new VS Code or Copilot version, add a new `evidence run=N` block). Official-SDK and Inspector runs do
**not** substitute for it. Expected effort: about 20 minutes.

Expected: `negotiation_path: initialize`, `negotiated_protocol_version: 2025-11-25` (or `server/discover` /
`2026-07-28` if a future VS Code uses the modern path); both are accepted.

## Step 0: macOS verification (before VS Code; used before run 3)

On the Mac, in an up-to-date checkout of the revision under test (`git pull`):

```bash
# 1. One-command diagnosis of the governed worker (prints a JSON report and a final VERDICT line).
uv run --no-project --no-python-downloads python tools/mcp_diagnostics/worker_probe.py
# 1b. Does the lifecycle test helper find the live worker? (prints raw ps rows, parsed argv, VERDICT)
uv run --no-project --no-python-downloads python tools/mcp_diagnostics/process_probe.py
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

## Steps (as performed for run 3; repeat for a new run)

1. **Check out and update.** Check out the revision under test (run 3 used the PR #1082 branch
   `claude/bold-euler-jb7uoy`: `git fetch origin claude/bold-euler-jb7uoy && git checkout claude/bold-euler-jb7uoy && git pull`), then `git rev-parse HEAD` (this is `repository_revision`). Confirm there is no
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
12. **Provide the evidence.** Fill the next `evidence run=N` block of
    `docs/mcp/acceptance/vscode-copilot-evidence.md` (`status: EXECUTED`, every field, `failed_at: none` on
    a pass, no secrets, no screenshots, nothing from an SDK client or the Inspector), run
    `uv run pytest tests/unit/test_r28_release_gate.py -q`, commit the file, and return the commit.

## What a new run means

- A new run with `disposition: PASS`, `failed_at: none`, a negotiation path the contract allows, exactly three tools, no resources
  or prompts, parse and run accepted, and a clean disconnect keeps the gate satisfied.
- A new run that fails is recorded as a new run (never edit earlier runs); because the latest run governs, the release gate fails
  until a later run passes, and the failing stage is a new finding.
