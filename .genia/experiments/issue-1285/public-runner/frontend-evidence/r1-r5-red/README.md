# R1–R5 correction: strengthened RED and preflight addendum

Codex, 2026-11-05 UTC. Starting SHA 65c345100f5c36698364522d5ac4fc5a6e7ceef0.
Authority: review issuecomment-6649295319; maintainer issuecomment-6658033204.
Existing scoped preflight in issue-1285-public-frozen-runner.md remains applicable.
This addendum narrows it to public-only R1–R5 corrections, tests, pins and evidence.

Preflight: infrastructure follow-up, maintainer-owned, no release/semantic work.
Latest main 0b25d2b45722f4397fd712f2f4b8eb3ea294f6e5 and starting SHA have identical
AGENTS/STATE/RULES/REPL/README. Read navigation and material authority/process
sections, issue body/review/authorization and accepted design evidence. No conflict.
No syntax, examples, runtime, host capability, conformance or MCP knowledge impact;
Python/C++ source and spec docs require no edits. Maturity N/A for language;
frontend remains a host candidate. Scope is .genia public-runner tests, frontend,
source/input pins, non-authoritative recipe/design/checklist and evidence. No CI,
private work, image/container, paid service, merge, closure or R29 work.
Seven portability fields: authority STATE unchanged; boundary Linux infrastructure;
existing shared evidence unchanged; capability vocabulary unchanged; no host claim;
no host gap/skip change; sync only experiment evidence. Both language hosts unaffected.
Tests: exact diagnostics, zero destination writes, real pinned uv/build fake HOME,
root precondition, cleanup-primary-error preservation, unsupported ZIP compression,
then 47-wheel/A-B/inventory/RECORD/wrapper/import/static preservation verification.
Minimal validation/cache fixes only; no strategy change or broad refactor. Phase
order explicitly authorized RED commit/handoff -> implementation -> verification
-> documentation/handoff -> independent Claude delta review. GO for this revision
only. Strict two-independent-build OCI equality and official 3.12.15 acceptance
remain unproved and required. Incremental spending $0; usage/effort not measured.

The new file uses files= so each adversarial regular member is listed in RECORD
with its actual bytes/hash/size, and assertRaisesRegex fixes the intended check.
Original17 tests remain byte-identical. Real fake-HOME install/build tests remove
ambient UV_CACHE_DIR, supply --cache to build, and assert HOME and retained scratch.

Baseline: 29 tests, 3 failures and 3 errors: real install/build HOME escape, scaffold
bin accepted, root reached argument access, cleanup masked primary sentinel,
unsupported ZIP method99 raised NotImplementedError. All original17 pass with a
declared ambient scratch cache; fake-HOME tests explicitly remove that cache.

Mutation discrimination: six passing baseline tests; 17 isolated require-removal
mutants each killed by assertion failure with zero test errors. These bypass one
specific require diagnostic in child memory, leaving disk/other validators intact.
This is behavioral removal, not code coverage. All raw child outputs retained.
An initial18th invalid .data scheme mutant causes downstream KeyError; it is
retained as negative evidence and excluded from the valid17 kill count. Additional
initial setup run omitted artifact selectors; next run exposed ambient readonly
HOME cache failures; both retained separately. Source was edited for docstrings
while an intermediate run executed, so its traceback line excerpts can differ;
red-final is the stable exact test version before the RED commit.

Host: CPython3.12.14, UID/GID1000, 2CPU quota, 8GiB memory; uv0.13.5 hash pinned.
49 artifacts independently fetched and exact sizes/SHA256 checked; git archive
source and original lock hashes preserved. No target3.12.15 or OCI claim.
