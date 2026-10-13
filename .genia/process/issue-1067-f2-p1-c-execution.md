# F2 P1-C execution — issue #1067

Authority: user explicitly authorizes behavior-preserving P1-B through P1-H,
with sequential test/implementation gates and no self-merge. Design #1207 §2
identifies entry consumers; P1-B provides accessors without an entry child.

Baseline: P1-B `add4055`; branch `issue-1067-f2-p1-c`.
Scope: Python CLI main selection, native discovery/registrar ownership, and
serve descriptor orchestration. Root remains entry. Main/1 preference, argv,
native discovery order/errors, import inertness and serve behavior remain
unchanged. Fixture injection is separately owned by P1-E.

Portability: Python host ownership selection has no portable Genia expression;
focused Python tests inspect the accessor seam. Existing portable contracts,
Core IR, C++ host, capabilities, MCP profile and evidence format stay unchanged.

Failing gate: `dfbfaa3`, three expected failures before migration. Implementation
`19472c2` selects entry ownership for main+argv, native registrar/discovery and
server/config/route/CORS descriptor discovery. It creates no new scopes.

Verification: focused CLI/native/serve/pipe plus seam tests: 106 passed.
Ruff and whitespace passed. Required source docstrings added and six resolved baseline entries removed.
Code-documentation checker passes against P1-B; broad regression belongs to
P1-H integration.
PR #1214 is unmerged and stacked on P1-B #1211. Issue #1067 stays open.
