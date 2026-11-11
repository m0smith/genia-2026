# D2b TEST ONLY — original RED archive and authorized oracle correction

> Historical phase evidence, superseded for current implementation/status claims.
> See [GENIA_STATE.md](../../../GENIA_STATE.md) for implemented behavior and the
> [independent cumulative review](https://github.com/m0smith/genia-2026/issues/1250#issuecomment-6773392957)
> for the current conditional-review disposition. Historical review/STOP wording
> below describes its recorded phase; it does not grant D2b acceptance or parity.

The original accepted RED is `b25b8f8c1904dc683f6634c4ef8c5f108d4f3eca`.
Its failure logs, `results.json`, `historical_oracles.json` and C++ evidence remain
unchanged. Their counts describe the original tests, not the corrected inventory.
The independent RED acceptance was subsequently narrowed by
[Claude reconciliation6609143905](https://github.com/m0smith/genia-2026/issues/1250#issuecomment-6609143905):
47 observed failures did not certify assertions masked behind early rejection.
[Maintainer6609232173](https://github.com/m0smith/genia-2026/issues/1250#issuecomment-6609232173)
authorized exactly seven test/evidence corrections, without production changes.

Current correction evidence, inventory and old/new expectations:
[`../model_b_d2b_correction/README.md`](../model_b_d2b_correction/README.md).
That correction-stage review request is historical and superseded by the linked
independent cumulative review. Current implementation truth belongs to STATE;
D2b acceptance and host parity are not established by this archive. The following
is the retained original phase narrative; its original bytes are also archived in
`../model_b_d2b_correction/original_test_and_specs.json`.

---

# Historical original RED narrative (superseded where corrected)

Baseline c377b971b42682207d194aefb0e5182650d4ac10 (merged #1312).
Accepted D2 design: docs/design/pre-r29-model-b-d2-linking-design.md.
No production, authority-document, Core IR, protocol, capability vocabulary or
implementation changes. All proposed behaviors remain RED, not implemented truth.

## Focused prerequisite / preflight delta

The baseline commit and full tree were reconstructed through GitHub connector
objects because executor git networking is broken. Verified commit hash and tree
2009f6f5ae7d915dcb09372ce1c87cdc1ddecf7f. Branch issue-1250-d2b-red passes the branch
checker. D2a tests: 58 passed before the intentional public-boundary transitions.
Exact witness lookup, FrozenOrdinaryBase, shared-engine mixed dispatch, pure
canonical validator, both new error classes, Env.publish_view and inert private
stores exist. Public evaluator branches still require GeniaOpenFunction; builtin
reflection still assumes explicit bases. These are intended missing D2b seams,
not contradictions. D2a's module-cache capture is locked; future ordinary stores
must retain that synchronization when D2b populates them. No material prerequisite
contradiction was found. D2a acceptance issue comments 6591480398/6605246182 and
6605268391 remain prior evidence, not fresh implementation certification.

| Portability field | Delta assessment |
| --- | --- |
| Zone | Portable ordinary callable authority, explicit selection, validation, frozen views and metadata, Python first. |
| Core IR | None; use existing IrOpenContribution/IrOpenUse and R16 modules. |
| Capabilities | Existing multi_file_eval, open_functions, default_open_functions; doc_help for metadata. No invented capability. |
| Shared evidence | 32 new model-b-link cases and four explicit approved historical transitions. Python host assertions supplement publication/races/TCO/internal snapshot identity only. |
| Python host | Later two evaluator branches plus reflection routing; no implementation in this commit. |
| Adapter/wire | Unchanged existing R16 load/execute/compare/applicability. No parallel runner, stderr comparator or request format. |
| Other hosts | Pinned C++ fef41e58dcd3b80aaedcac98c92943fcfbfd1945 reports all 32 new cases UNSUPPORTED. Actual R16 gate results retained, never PASS. #1269 default-open and #1018 multi-file remain owned gaps. |

MCP knowledge impact: D2b activation will change public language knowledge and
requires a GREEN-stage STATE/profile/semantic registry impact check; no client may
be told this RED behavior is implemented. Authority docs remain accurate unchanged.
Existing gap inventory now lists proposed cases; Slice C inventory checks are
restricted to its own prefix so exactness is preserved across additional slices.
The formerly language-ungated two ordinary-target guards move from guard to gated
sets (53/84, total137; with six G1 cases total143/90 gated). This is a capability
applicability correction for the approved activation delta, not a skip mechanism.

## Coverage

- Shared R16: positive ordinary extend/use; import inertness and unselected base
  isolation; alias/reexport/B1 replaced slot; duplicate aliases; import/selection
  order; typed keys and nested guard shadowing; duplicate and disjoint shape
  conflicts; same-unit mix; distinct-key/catchall ambiguities; varargs ambiguity;
  contributor closure; consumer mid-init; Outcome awareness; doc/meta alias
  precedence; explicit-view metadata; no authority for lambda/builtin/local lambda
  alias/nonfunction/view/non-export; original-module declaration ownership.
- Python: actual public checked-writer fault/retry, failed selection preserving
  prior view/state, nonretroactive contribution selection, live-group mutation
  without rewriting completed views, three-channel reflection (including help
  category/provenance/path non-leakage), public TCO, immutable publication target,
  failed-origin escaped G negative, bounded source publication/load race,
  observed barrier-started two-writer race and single writer-lock hold.
- Existing D2a private tests remain relevant. The two public nonactivation guards
  intentionally transition at D2b, as does the historical explicit-R20 duplicate
  unit test; no assertion is silently deleted to make activation pass.

## Approved historical oracle changes (design §8 Δ1/Δ2)

Full original spec documents, expected values and notes are preserved as parsed values
in historical_oracles.json; original source SHA is the baseline above.

1. model-b-c-own-extend-ordinary-rejected and
   model-b-d1-preserve-ordinary-extension-rejection: old exit1 and
   `Error: open-function-target-not-open: 'base.f' is not an open function interface`;
   new exit0 and existing final-value display `<open contribution <entry> -> f>`.
   Explicit-open source analog was executed to verify the existing display shape.
2. model-b-c-own-use-ordinary-base-unchanged: old target-not-open, new unchanged
   incompatible-contribution category because ext declares no unit:
   `Error: open-function-incompatible-contribution: expected a contribution targeting ('base', 'f'), got 'ext'`.
3. error-r20-cross-module-overlapping-unit-ambiguity: old call-time
   `Error: open-function-clause-ambiguity: get/3 matched clauses in more than one unit ['db_ext', 'db_ext2']`;
   new selection-time `Error: open-function-cross-unit-duplicate-clause: get has an identical dispatch key in units 'db_ext' and 'db_ext2' shape=('fixed', 3) (first at db_ext:2, duplicate at db_ext2:2)`.
   The associated Python selection tests do not call the function; failure must
   occur at use. A new distinct-key overlap case retains runtime ambiguity proof.

Authorization: accepted design §8, maintainer decision #1250 comment6561255519,
and explicit D2b TEST ONLY authorization in this task. No other historical oracle
value changes. This correction is not a claim that older oracles were defects.

## Reproduction and actual results

Linux6.18.57 x86_64, Python3.12.14, pytest9.1.1; existing uv project environment.
All pytest calls use `UV_CACHE_DIR=/workspace/work/uv-cache uv run --no-sync pytest`.
No dependency install; uv.lock remains absent. No full-suite or C++ parity claim.

- Before authoring, the three D2a link modules: **58 passed**.
- Final 53 behavioral selections: **47 failed, 6 passed**, retained in results.json
  and final-0.log.json through final-4.log.json. Every invocation uses --maxfail=19; largest
  selection has 16 failures, so no STOP threshold was exceeded.
- New shared cases: 27 failed / 5 passed. Passing authority/ownership negatives are
  existing-behavior controls. Four historical spec transitions fail as intended.
- New host cases: 12 failed / 1 passed; passing failed-origin negative is a control.
  Four historical Python-boundary transitions fail as intended.
- Inventory/gap verification: **5 passed**, 145 unrelated tests deselected.
- Unaffected D1/key/private D2a preservation:
  `tests/unit/test_model_b_d1_completion.py tests/unit/test_model_b_d1_preparation_failures.py tests/unit/test_model_b_slice_c_keys.py tests/unit/test_model_b_d2a_link_core.py tests/unit/test_model_b_d2a_link_dispatch.py tests/unit/test_model_b_d2a_link_publish.py -k 'not d2b'`
  **124 passed, 2 intentionally transitioned public guards deselected**. This is a
  focused preservation selection, not full regression or masking the new RED.
- All 101 logical module source fixtures parse/lower successfully.
- C++: actual fetch_capabilities + execute_spec_via_host with unchanged default10s
  deadline, sequential gate execution: **32 UNSUPPORTED / 0 PASS / 0 failure classes**.
  Source/contract pins and declared capabilities retained in cpp_evidence.json;
  source pin matches accepted-design host pin. Applicability gate rejects before
  module requests are sent; this is not proof of future C++ linking behavior.

The preserved verify.py/final_verify.py scripts are historical, nonportable
sandbox tooling, not clean-checkout or CI reproduction commands: they depend on
original /workspace paths and environments. Their recorded calls use existing
pytest/R16 APIs; no new conformance system is defined. The exact selections remain
in results.json. The original small log wrappers in this directory retain raw_log;
json.load(file)["raw_log"] reconstructs those original logs.

## Failure classification / fixture defects

Most immediate RED is existing OpenFunctionTargetNotOpenError at ordinary extend
or use, before later assertions execute. Explicit Q1 tests fail because use
currently accepts duplicates/shape conflicts. Metadata doc test observes overlay
instead of canonical; meta/help encounter missing FrozenOrdinaryBase metadata
routing. Exact per-case failures are retained in results.json. Public concurrency,
TCO, retry and many semantic expectations behind missing activation have **not**
executed; no activation shim or stub was supplied. They require independent review
and real execution at GREEN, not a claim of verified downstream correctness now.

Draft fixture defects found and corrected separately: varargs error wording used
`from units` instead of existing `contributed by`; three metadata source fixtures
used unsupported `.doc` suffix after a call; the attempted `/doc` correction
was also invalid (division, not map access). The authorized revision uses `map_get`; two transitioned success specs initially forgot the existing final
contribution display. Parse-only checks and explicit-open analog exposed those
issues without implementing D2b. No production failure is reclassified as a pass.
Initial and final failures remain retained; repeated final selections reflect
actual subsequent source/fixture/style changes, not retry-to-green.

## Review and stop

Independent Claude Code review is REQUESTED, not completed: command -v claude
returns no executable and active-tool metadata exposes no Claude service. No Codex
agent is substituted as Claude and the author does not approve these tests.
This candidate establishes executable RED, but RED acceptance remains BLOCKED
pending that required independent review. Supply the candidate SHA to Claude Code
for semantic/fixture/transition/portability review and publish its verdict on #1250.
Any modified RED requires a new SHA, appropriate verification and re-review.
STOP after RED; no D2b production, Slice E/R29, merges or issue closures.


## Compact archive and history retention

The seven correction/strength pytest dumps are compact outcome tables. Each keeps
its original label, production source HEAD, Python version, counts and every case's
class/name/status/failure. Each run keeps its exact command and return code;
`case_indices` indexes the shared `cases` table in original order. Raw logs are
replaced by their SHA256 hashes and the original file's commit/blob/SHA256 link.
No historical failure, skip or unsupported outcome is reclassified as a pass.

Full original dumps remain at [archive commit 6ae23288](https://github.com/m0smith/genia-2026/tree/6ae23288363c4e5effb0e56b6852dc33dd692ef8/tests/data).
Semantic/test-history anchors are original RED `b25b8f8c1904dc683f6634c4ef8c5f108d4f3eca`,
correction integration `d1be59c66a23c635e81f88d592d32a9bb6ac1b9d`, and strength integration
`6230bd947e12b97d2a5d7d88bc8664da4f8e752a`. These are historical evidence, not
new exact-head execution proof.

**Retention requirement:** preserve the candidate's ancestry with a merge commit.
Do not squash/rebase away these commits unless durable tags are created and
independently verified first, or the omitted raw evidence is restored. A source
URL alone does not guarantee retention of otherwise unreachable Git objects.
The inventories, oracle/C++ evidence and both `.genia/process` STOP records are
unchanged. Sandbox scripts are retained only as historical artifacts.
