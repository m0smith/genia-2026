# #1251 post-merge documentation truth correction

Base: authority 09804b565a30c2995a7d045d74faf8e880994ff4,
tree f8a686c96aaa67034ff5aaab721c107f0e6974e0. PR1270 merged reviewed
663a727dd5b0cc967fb633255e15aa93e494d566 on 2026-10-30. Selected C++
1f33886606fc94dadab679ed56182a15ca503a4b is unchanged in both workflows.

## Documentation / bounded review
Correct stale host prose saying #1299 is unresolved and describing #1270 as a
candidate awaiting main integration. The separate reviewed #1301 repair is now
integrated. Record the actual mechanism and fresh hosted parity, retaining the
historical 294/1/749 full run and 34/30 failures per1000 on old/new binaries.
Do not turn an image/pin/clean run into fixture-determinism or R29 certification.

The known-gap JSON structural diff is exactly /gaps/18/reason. All capabilities,
case applicability, removal conditions, protocols, runners, comparators, expected
results and checker baselines remain unchanged. STATE/RULES/REPL README/README/
AGENTS are byte-identical to the base; STATE stays42997words. No implemented
language fact changed, so book/cheatsheet/profile/reference regeneration is not
warranted. Existing partial D/E and C++ boundaries remain accurate.

No new or modified runtime/helper code: maintainability-code review is N/A.
This is a factual documentation review by the correction author, not an
independent approval of this PR. Independent original repair/guard reviews are
linked in #1251 and genia-cpp#60. Keep this PR reviewable; do not merge it here.

## Fresh correction-branch validation
Environment prefixes select the existing project venv, writable uv cache and
this checkout's src. Commands use uv run --no-sync.
- pytest -q tests/doc/test_semantic_doc_sync.py
  tests/doc/test_state_anchors_and_registry_sync.py
  tests/doc/test_portability_contract_sync.py:244PASS/34existing skips.
- python tools/gen_mcp_language_profile.py --check:exit0.
- python tools/gen_function_docs.py --check:exit0.
- python tools/lint_doc.py --scan-dir src/genia/std/prelude --require-coverage:exit0.
- python tools/stage_docs_for_mkdocs.py:exit0.
- mkdocs build:exit0,71.81s; mkdocs build --strict:exit0,56.65s.
  The repository's default MkDocs configuration already has strict:true.
- git diff --check:PASS; structural JSON comparison:reason-only as above.

## Evidence limits / remaining acceptance
Hosted merged-main parity41089720060 executed both hosts:Python1026PASS/
18UNSUPPORTED; C++295PASS/749UNSUPPORTED; all actual failure classes zero.
Local merged-authority Python run separately returned1025PASS/18UNSUPPORTED/
1TIMEOUT in r20-cross-module-view-mutual-tail-call at the unchanged10s deadline;
its paired local parity gate correctly FAILS. The case's hosted external request
passed in3.739s. Local cgroup quota is2CPU; concurrent compilation/test load and
throttling are observed, but causation is not established. Do not replace or
reclassify this local result using the hosted success or a retry.
Local C++ full run is295PASS/749UNSUPPORTED/all actual failures zero; fresh1000
corrected-fixture requests pass at10s/max8, with exact post-failure-send rejection.
Other still-running native/Docker/regression checks are recorded separately on
#1251 when complete. This docs correction does not certify a fully green local
run, close #1251, dispose of the timeout or authorize R29.

## Distillation
Durable implementation/evidence facts belong in the existing host matrix,
development-container page and existing descriptive gap reason. No report or
process narrative was added under docs/. Remaining semantic-foundation scope
and issue acceptance belong on #1251. Temporary coordination handoffs are safe
to discard; no temporary handoff is committed.
