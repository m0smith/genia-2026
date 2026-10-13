# F2 P1-B failing-test gate — issue #1067

Baseline: `9f0170d9e3b18dec8f14d144f6d7749ee07fdc08` (merged P1-A #1210).
Branch: `issue-1067-f2-p1-b-tests`. Owner: Codex for maintainer review.

## Scope, authority and readiness

User authorization is conditional on #1210 merging; GitHub confirms that gate
is satisfied. Authorizes failing tests for runtime/entry/unit scope accessors
only, retaining P1's shared-root behavior and debugger compatibility view.
Use the merged design #1207 §2 API candidates `runtime_scope()`, `entry_scope()`,
`unit_scope()`, `inspection_globals_scope()` as the proposed test interface.
Their exact API and design remain reviewable; this test gate does not authorize
implementation. Do not add an entry child, alter lookup/assignment/reflection,
migrate consumers, amend P0, merge, close #1067, or begin P2/P3/F3–F5.

Classification: unnumbered R20 follow-up after R28/before R29. Authority remains
STATE §§0/4/7/9, RULES module/dispatch invariants, REPL README and README.
P0 §§8/10 and P1 design §2 define proposed preparation. D1/D2b/fallback decisions
are already reviewed; their semantic activation is outside this slice.

## Portability analysis (seven fields)

1. Maturity: N/A, Python internal API failing-test gate; no semantic change.
2. Authority/boundary: existing shared-root execution and lexical/module
   ownership; proposed Python Env accessors return existing owner objects.
3. Representation: existing Env/closure/debug hook objects; no new language
   name, AST/Core IR node, metadata scheme or protocol field.
4. Evidence: Python tests for host internal accessors; retain P1-A host-tool
   regressions. Existing shared/native evidence governs portable setup behavior.
   A Python Env accessor cannot be expressed as a portable Genia spec.
5. Applicability: no new capability. Existing `multi_file_eval`,
   `prelude_autoload`, `debugger_stdio` claims are unchanged.
6. Hosts/evidence: Python API only; no C++ implementation/parity or new host
   gap. No new runner or evidence format; future semantic phases still use R16.
7. Truth/MCP synchronization: none now. No implemented behavior/user-facing
   examples change; STATE/book/cheatsheets and language profile remain unchanged.

## Proposed acceptance and verification

Accessors return owner Env by identity, not copied dictionaries. Root remains
entry for factory-created and standalone environments. Child function/block
frames inherit declaring unit; module loading marks its own unit without
changing structural parentage. Runtime state stays on root. `run_source` on a
supplied child/module/prelude does not reset the execution entry. Module debugger
inspection accessor still selects root. Scope ownership must not be inferred
from filenames, rebind-parent settings or mutable R20 module-id strings.
Tests cover repeated entry submissions, caller-provided scopes, actual module
loads/aliases/nested imports, captured function/block/lambda environments,
autoload and independent executions. Calls must leave bindings, metadata,
lookup, assignment, caches and existing host observations unchanged.

Expect genuine missing-API AttributeError failures on this baseline; do not add
stubs, skip/xfail markers or implementation to turn the suite green. Run the
new red suite, P1-A plus module/debug regressions, lint, documentation coverage,
and whitespace. Full regression is deliberately red while required APIs are
missing; P1-B implementation must cite this test SHA and run both full partitions
after approval. P1-A's full regression/CI evidence remains the latest baseline.

## Impact, complexity and phase gates

Files: one Python host-internals test module and this process record. Drift risk:
medium; exact APIs/test expectations require design review. Helpers inspect
existing closures/debug hooks rather than prescribe private reference storage.
Preserves minimalism, lexical pattern-first behavior and host boundaries; this
approved infrastructure preparation supports reliable ordinary composition.
No public metadata generation or reference documentation changes.

Pre-flight → authorized TEST commit → draft failing-test PR → stop for test/design
review. No implementation, audit claim for future runtime, or phase advancement.
GO for this test gate only; reviewer: maintainer. Keep #1067 open.
