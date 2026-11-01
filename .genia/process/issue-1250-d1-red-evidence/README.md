# #1250 D1 TEST ONLY — accepted RED

Base: merged #1306 `ca0b72e1f48c07a169feb812b6f6dde6caf1e56e`.
Test branch: issue-1250-d1-red; explicit user TEST-only authorization supersedes
the original preflight's proposed implementation-branch name. Accepted B1 and
D1 design are unchanged. No production code, root authority or capability changes.

## Commits and observations

| Observation | SHA / result | Disposition |
|---|---|---|
| Initial working-tree check | 18FAIL/7PASS | 17 expected D1 failures plus one test bug: group has no closure; use its clause record's closure. Retained initial.log, not claimed as committed RED. |
| First committed tests | d1ac504558b25ea22954b4e24783b6e48a65f675, 19FAIL/9PASS | 18 expected D1 failures plus one numeric payload oracle bug found by independent review. red.log/xml retained. Lowered integer literal uses tagged digits, not Python int. |
| Corrected committed RED | **98697c20fae59dadffd36fdb58c3ee7ba6d65c2a**, **19expectedFAIL/9PASS/0errors/0skips**,1.44s | All28 collected.17 missing immutable completion associations;1 incomplete cache publication;1 cache-hit read outside accepted writer synchronization. No setup/collection errors. |
| Documentation-only test-head | 90c41e56f9edc7501cc3c30ab20662abf0eb4baf | Three hook docstrings only; docstring-stripped AST independently checked equal to98697c20. No relabelled execution. |

Exact commands, interpreter/platform, environment selectors, SHA and resource
envelope are in provenance.json/external.json. Raw logs/XML retain every failure,
traceback, test identifier and result. manifest.json records SHA256/bytes for all
10 raw members of raw-evidence.tar.gz. No retry-to-green, failure reclassification,
deadline increase, skipped case or production/test-oracle weakening was used.
Test bugs were corrected and their original observations explicitly retained.

## Setup validity and private protocol

Tests load actual Genia modules through existing Env.load_module. Calls, alias
identity, source construction, grouped/optimized cases, real failures/retries and
cleanup assertions occur before missing-feature assertions wherever applicable.
Two cache-dict observers witness actual publication and cache admission, without
implementing D1. A test-only Cell is stopped/joined in finally even in RED.

Private Python inspection protocol is pinned in the test module docstring and
assertions: `_ordinary_completions` immutable identity pairs; projection clauses,
binding_metadata, projected_doc, help_doc/help_metadata; logical shape/key/ordinal
descriptors; clause materialize returns a fresh existing GeniaFunction record.
These internal names are an adaptable test seam, not approved language syntax,
new portable API, implementation stubs or a model of snapshots. An equivalent
private implementation may adapt inspection with independent review, retaining
all behavioral/mutation/ownership assertions. No new conformance runner exists.

**Limit:** downstream mutation/channel assertions behind the missing association
boundary are specified but unexecuted until D1 exists. They are not claimed as
GREEN proofs. Test fixtures and baseline preconditions execute now. Further
preparation-helper fault injection must use the real implementation boundaries
once available; this phase does not invent copy/preparation stubs to fake coverage.
Existing constructor and final-publication fault controls exercise the real
pre-publication cleanup paths. Do not claim every future copier fault was injected.

## Eight-row coverage / acceptance obligations

| Design / preflight | Test coverage and limits |
|---|---|
| A1 / D1-01 | Real cache-hit identity, unique original projection, dict observer of fully prepared publication, deterministic existing-writer lock witness; no timing/GIL/sleep assumptions. |
| A2 / D1-02 | Detached params/literal numeric payload, fresh execution copies, immutable clause container; grouped shape/key/ordinal/span/header/guard order and mutations of live guard/record list; optimized retained-case syntax isolation; lexical closure/Ref/Cell identity and Ref mutation; host-only shell body accepted without execution. |
| A3 / D1-03 | Canonical binding doc distinct from independent inline-help fallback and category summary; missing doc is absence; binding and help host-map mutation isolation. |
| A4 / D1-04 | Real aliases/re-exports share exact G projection despite later help changes; failed-origin and never-directly-exported escape remain legal, including same-owner-text retry G2. No inferred completion/identity minting. |
| A5 / D1-05 | Six B1 cases: replacement, replacement annotation, import reset, restoration/no resurrection, alias shared help, annotated restoration; G-inline never replaced by H-inline. Subsequent mutation cannot alter completed channels. |
| A6 / D1-06 | Actual source failure, ModuleValue construction MemoryError and final-cache assignment exception: sentinel cleanup, no completed entry, retained old ordinary value, prior effects/dependency cache, fresh retry identity. Earlier future helper-specific injection remains explicitly a subsequent obligation. |
| A7 / D1-07 | Four new shared public-preservation cases; nearby83PASS covers module/cache/cycle/isolation, existing metadata, ordinary ownership and explicit R20 behavior. Private cycles/source-failure/live-group controls pass. Ordinary extension still rejects. No public linking claim. |
| A8 / D1-08 | Separate committed RED SHA and raw evidence/digests; exact base/tree; runtime/root/manifest unchanged; lint/code-doc checks; independent RED review and stop gate. Later implementation still requires maintained-code docs, full applicable checks and independent maintainability/truth audit. |

## Validation and shared host evidence

- Targeted: `uv run --no-sync pytest -q --maxfail=20 --junitxml=<final-red.xml>`
  tests/unit/test_model_b_d1_completion.py tests/spec/test_model_b_d1_preservation.py:
  19expectedFAIL/9PASS. The process's failed result remains RED; it is not an exit0
  acceptance run. Failure cap20 retained; final19 failures never exceed the cap.
- Nearby four modules (exact command in provenance): **83PASS/1.04s** atd1ac5045;
  no later change to those tests or runtime/spec content. No full audit repeated.
- Existing canonical fetch_capabilities/execute_spec_via_host,10s/concurrency1,
  at98697c20: new shared four cases **Python4PASS**, **C++4UNSUPPORTED** under
  multi_file_eval/doc_help gaps. No other actual classes. Unsupported is not PASS.
  Selected existing C++ binary SHA2568f8c6fd62d699b5b413ed8752eb433a3d4af73788142968f1ca87ba2a5d45d98;
  source pin1f33886606fc94dadab679ed56182a15ca503a4b/older declared contract as prior
  accepted evidence. No rebuild or current-pinned/full-current C++ claim.
- Ruff changed tests PASS; whitespace PASS. Maintained-code check initially found
  three missing hook docstrings (retained code-doc.log); corrected without baseline
  changes. Final check10004records/2793legacy gaps/1classified exclusion/**0errors**.
- Runtime/hosts/tools, manifest/gap registry, STATE/RULES/REPL/README/AGENTS,
  semantic facts and generated MCP profile unchanged. No new implemented fact
  warrants language-reference updates. Historical seven Python timeouts untouched.

The four YAMLs are public-preservation controls, not snapshot introspection. They
use existing capabilities and exact output comparators with no oracle reductions.
Future D2 still requires observable shared linking/snapshot RED. Internal success
will not establish portable linking or waive C++ required parser/lowering #50.

## Independent review and final gate

Reviewer /root/acceptance_review authored no tests/edits or publication and inspected
actual source, diff, logs/XML and external records. Initial scope review requested
concrete A2/A3 coverage; those additions are present. First exact-commit review
REVISE identified numeric-payload bug atd1ac5045; corrected at98697c20.

**Final independent PASS at90c41e56:** 19 expected failures/9PASS/zero errors/skips,
17missingassociation+1incompletepublication+1unsynchronizedread. Three final docstrings
do not change the executed tests. Earlier erroneous runs and unexecuted downstream
oracles disclosed. No runtime edits or weakened assertions. **GO to publish this
TEST-only RED evidence. Implementation requires separate authorization.**

This is coordinator transmission of attributable independent review, not author
self-approval or maintainer merge approval. No tests were run by the reviewer;
independence concerns test construction/result inspection, not a claimed rerun.

Next action: explicit implementation-phase authorization citing98697c20, then
implement D1 within the accepted design and satisfy these oracles plus genuine
preparation failure injection and required GREEN/review gates. Do not implement
from this task, enable ordinary linking/closed publication, start E/R29, close
#1250/#1251 or merge an intentionally RED test PR without an explicit later gate.

One coordinator and one independent reviewer. Token usage/savings/review time not
measured. No process artifact added under docs/ and no checker baseline changed.
