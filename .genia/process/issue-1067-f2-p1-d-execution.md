# F2 P1-D execution — issue #1067

Authority: user explicitly authorizes behavior-preserving P1-B through P1-H,
with sequential test/implementation gates and no self-merge. Design #1207 §2
and P1-A characterize existing inspection behavior; P1-B provides accessors.

Baseline: P1-C implementation `19472c2`; branch `issue-1067-f2-p1-d`.
Scope: Python-host REPL `:env`, debugger globals and initial entry frame only.
No entry child, unit-local module globals, reflection/lookup change, P2/P3 or
F3–F5 activation. Root remains entry and module globals retain root.

Portability: host-internal accessor selection cannot be a shared Genia spec.
Existing debugger protocol, command rendering and portable behavior remain
unchanged; no Core IR, capability, C++ parity, evidence-format or MCP change.

Failing gate: `b20fde7`, three focused seam tests failed on pre-migration code.
Implementation uses inspection_globals_scope() for globals/:env and
entry_scope() for the initial logical frame; locals stay frame-local.

Verification: focused seam/P1-A/debug foundation/debug stdio/P1-C suites:
24 passed. Ruff and whitespace checked. Five resolved baseline entries removed; code-documentation checker passes
against P1-C. Broad regression belongs to P1-H integration. Issue #1067 remains open.
