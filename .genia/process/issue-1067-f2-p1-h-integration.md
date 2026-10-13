# F2 P1-H integration record — issue #1067

Scope: integration, verification and records only. No language, parser, Core IR,
or scope-topology change; root remains the entry scope. P2/P3 isolation and
F3-F5 follow-ups are not activated or closed.

Ancestry (verified from `origin/*` heads):
- P1-A, P1-B, P1-E (PR #1216) and P1-F are reachable from `main`.
- P1-C (#1214, `dfbfaa3`..`133b5ed`) is contained in P1-D (#1215, `e915421`),
  the original integration base.
- P1-G (#1213, `8d60243`..`a1e2236`) branched from the same pre-P1-E base.

Integration: `main` merged into the integration branch, then P1-G. One content
conflict, `src/genia/test_cli.py::make_test_env`: kept P1-E's
`set_host(..., visibility="entry-only")` fixture/registrar classification and
P1-C's `env.entry_scope()` registration-list attachment; both are required.
The P1-G merge was conflict-free.

CI blockers: `GENIA_STATE.md` is 42865 words after the `main` merge (limit
43000); no limit change. The CI code-documentation job runs with
`--base-ref` (diff-aware), which the plain unit test does not: it reported
`tools/gen_function_docs.py::collect` as a new/changed gap because P1-G edited it
undocumented. Fixed with an accurate docstring and removal of its now-resolved
baseline entry (2841 -> 2840 legacy gaps); no exemption was added.

Verification on the merged tree: `ruff check .`; `pytest -n auto -m "not loopback"`
6659 passed / 60 skipped; `-m loopback` 31 passed; `tools.spec_runner` 822/822;
`test_code_documentation.py` 26 passed and `python -m tools.code_documentation --base-ref <main>` 0 errors; `gen_function_docs.py --check`,
`lint_doc.py --require-coverage` and `gen_mcp_language_profile.py --check` clean.
Not run locally: Node/VS Code and official-SDK MCP stdio jobs, C++ host parity
(CI-only).

Post-merge note: PR #1219 merged this branch into `main` (10ed362f) before this
note was written; no further integration was required.

Deferred audit findings (Low, non-blocking for P1-H, mandatory for P2
completion; tracked in the F2 contract gates section): #1220 direct
`env.root().autoloads` access in reflection/help, and #1221 stub-only
P1-C/D/G accessor tests. Both remain open; no change was made to either in P1-H.
