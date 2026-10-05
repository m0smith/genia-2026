# VS Code + GitHub Copilot acceptance evidence (R28-H39)

Status: **NOT EXECUTED.** No authentic VS Code + GitHub Copilot run exists. Do not fill any field below
from an SDK client, the Inspector, documentation, or reasoning. Procedure:
`docs/mcp/vscode-copilot-acceptance.md`. The gate test `tests/unit/test_r28_release_gate.py` enforces the
shape and blocks any "R28 complete" claim until this record is `EXECUTED`, complete, secret-free, and
`PASS` with `negotiation_path: server/discover`.

One value per field, no secrets, no personal data, no screenshots. Allowed values are noted in comments.

```evidence
status: NOT EXECUTED            # EXECUTED once the run happened
executed_on:                    # date, YYYY-MM-DD
vscode_version:
copilot_extension_version:
repository_revision:            # 40-hex commit under test
workspace_trusted:              # yes | no
mcp_json_discovered:            # yes | no  (genia listed with no edit)
server_state_shown:             # e.g. Running
tools_visible:                  # exactly: genia_capabilities, genia_parse, genia_run
resources_or_prompts_visible:   # none | describe
parse_invoked_from_host:        # yes | no
invalid_source_feedback:        # e.g. parse_error at character offset 171
corrected_source_parsed:        # yes | no
run_invoked_from_host:          # yes | no
run_result:                     # value / stdout / stderr / exit code as seen
channel_separation_visible:     # yes | no | not exposed by the host
negotiation_path:               # server/discover | initialize
clean_lifecycle_after_disconnect:   # yes | no
host_log_excerpt:               # redacted lines showing the first request
disposition:                    # PASS | FAIL
```

## Notes

(Free text after the run: anything surprising, the OS and version, how long startup took.)
