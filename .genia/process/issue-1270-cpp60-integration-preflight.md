# #1270 reviewed C++ #60 integration preflight

Owner: Codex; maintainer controls acceptance. Work only on the existing dedicated
branch claude/nice-brahmagupta-1e17ws, starting at
d55524dff62c036951301143781e62eb5310ef68. User explicitly authorizes the two
workflow pin changes, bounded host/provenance documentation, verification,
independent review, push and report. No #1270 merge, issue closure or R29.

Read latest AGENTS first (unchanged from fetched authority), then STATE, RULES,
REPL README, README, host integration/porting, executable-conformance and
run-change/preflight procedures. STATE is final authority. Contract behavior
and Python semantics are unchanged; this is a reviewed-host integration.

Merged genia-cpp #60 contains implementation
1f33886606fc94dadab679ed56182a15ca503a4b; merge
fef41e58dcd3b80aaedcac98c92943fcfbfd1945. Pin the reviewed implementation,
replacing 1af65fd2425526573f9ca765b3a027e37dfa5c74 in parity and Docker.
Independent final implementation reviews and native/code-doc CI passed.
Accepted clean candidate evidence: 1,044 /295 PASS /749 UNSUPPORTED, all failure
classes zero. Current-main 901-case and declared-contract 793-case evidence have
their own scopes; do not conflate them or the adapter's old semantic pin.

The R25 fixture race remains OPEN #1299. Preserve the failing full run
(294 PASS/1 FAIL/749 UNSUPPORTED), baseline stress 966/34 and new-host 970/30,
and the separate clean 295/749 run. The recorded scoped #60 acceptance exception
does not waive failures, permit red required CI, resolve the fixture, or approve
#1270/#1251/R29. No retries-to-green, skips, oracle/test/runtime changes or masks.
If a new run fails, record it and report its exact scope rather than suppress it.

Scope: two pins; host matrix/container provenance; truthful bounded guard/capture
status in the five authority docs as needed, retaining Python/default-open/D/E
boundaries and STATE's 43,000-word limit. Qualify STATE's existing REPL grouping
sentence as closed groups, consistent with already-reviewed #1298 truth evidence;
ordinary REPL group behavior does not change. No broader #1298 changes imported.
Excludes YAML oracles, manifests/capabilities/gaps, comparators, normalizers,
runtime/optimizer, baselines, lifecycle fixes and feature development.

Portability: (1) authority existing STATE/R20; (2) boundary existing Core IR/R16;
(3) evidence unchanged full host suites and native guards; (4) applicability
existing manifest/requires; (5) claims bounded C++ source only, not default-open
support; (6) gaps unchanged, #1299 explicitly unresolved; (7) synchronize pins,
host provenance and authoritative bounded status, record exact source/tree.
MCP knowledge impact: none; Python MCP/profile facts do not change. Keep the
registry/profile/golden unchanged and run its check.

Validation: local docs/semantic synchronization and relevant host checks; exact
pin hosted parity and Docker, strict docs/code docs, LLM validation and PR CI.
Retain evidence artifacts, compare per-case outcomes with accepted #60 data,
request independent final-SHA review, then record results and limitations on
#1270. Hosted pull-request checkouts may be synthetic merges: inspect their
identity and tree differences instead of claiming exact-candidate identity.
No new contract/design/RED is needed for a source-pin/documentation integration;
reuse the independently reviewed RED/fix history of #60. GO within user scope.
