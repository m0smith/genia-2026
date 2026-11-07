# Iteration-2 bounded validation

Codex, 2026-11-07 UTC; implementer static verification, not independent approval.

- `bash scripts/check-genia-branch.sh`: PASS on `issue-1285-g3-evidence-hygiene`.
  Initial `docs/issue-1285-g3-hygiene` branch failed the script's issue-prefix
  requirement; renamed before editing production code or committing. Failure
  was a branch-name check, not a behavioral test. No gate was bypassed.
- Python stdlib JSON parse of every lane JSON file: PASS.
- Python byte equality against the lane's reviewed parent for all original
  receipts except the intentionally amended README: PASS. For G1, recomputed
  all original receipt.evidence_files byte counts and SHA256: PASS.
- `pins.json` byte equality to accepted frontend `fd74a583`: PASS, SHA256
  `958fdd646e305bc38753a5d10b91f0f8927e41b4c2f5e2037dec3225ac25590b`.
- Four authority documents plus AGENTS byte equality to freshly fetched
  `origin/main` (`0b25d2b45722f4397fd712f2f4b8eb3ea294f6e5`): PASS.
- `git diff <reviewed-parent> -- src tests hosts spec docker` and frontend/
  frontend_tests: empty. Only the named lane's precheck directory changed.
- Relative Markdown evidence links resolve; manually checked scope, no new
  environment identifier/proxy URL/credential/raw policy publication: PASS.
- `git diff --cached --check`: PASS. Historical raw HTTP header CRLF bytes are
  separately hash-checked and not changed or normalized by this delta.

Python arithmetic checks against the explicit disk/inode totals: PASS;
feasibility result INFEASIBLE. jq allowlist expression extracted from hygiene.md
was evaluated **offline**, with historical sanitized projection as a fixture:
PASS. Missing-field fixture rejected: PASS. This validates recipe syntax and
field selection only; it is not a fresh Docker or venue receipt.

No runtime regression, CI dispatch, Docker metadata request, container operation,
network-policy/cgroup write, benchmark or acquisition was performed. No tests
were added: this is evidence/design hygiene, not implemented behavior. The
independent delta review requested in the issue handoff remains pending.
