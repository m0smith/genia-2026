# D2a RED revision 2 evidence (#1250)

TEST ONLY. No D2a implementation or public activation. Accepted design: merged
PR #1311, baseline `cc262127c11071f0722f5487e6dcf75452382b75`.
Parent RED: `cff05d06410014622ff2557fd642dfa8c2eac3f6`.
Independent review requiring this revision:
https://github.com/m0smith/genia-2026/issues/1250#issuecomment-6581469533
Original failures remain evidence:
https://github.com/m0smith/genia-2026/issues/1250#issuecomment-6569248656

`results.json` records each of the 58 selected cases, its immediate result, source
blob hashes, environment and evidence limits. Final selection: **56 missing-seam
failures, 2 existing-behavior guards pass**. No skips/xfails or acceptance stubs.
Initial revision draft had 55 cases / 53 failures / 2 passes; three additional
snapshot/dispatch cases increased failures without changing their classification.
The original 35-case RED and independent-review diagnostic runs are not replaced.

## Finding-by-finding response (pending independent acceptance)

| Finding | Test-only correction |
| --- | --- |
| 1: atomicity | Trace each executed builder/validator Python-line occurrence (including repeated scan lines) with a distinct injected failure, unchanged structural/identity state and successful retry. Independently fault actual sort entry and actual view construction after real constructor work. Retain semantic duplicate-selection/duplicate-key and checked immutable-writer failures. Snapshot bindings, metadata contents, immutable names, both contribution stores, completed/loading caches, projections and prior view. Prepare all dependency modules before the snapshot. |
| 2: bounded concurrency | Reject same-thread lock re-entry before acquire; time-bound other acquisitions. Guard actual lookup/renderer code even through aliases. Observe two barrier-started publishers at every checked-writer boundary; validate complete identity, structure and callable behavior during the race. Block a real module initialization at an event while publication completes. Contain threads in disposable child processes; terminate/kill/reap on deadline. |
| 3: dispatch | Matcher err exact identity/no guard-body-fallback effects through a published ordinary-base view; 60,000-step ordinary identifier-header self TCO and 60,001-step mutual TCO through two views. Actual some invocation, cross-arity absence exclusion, multi-candidate guard counters/no ambiguity bodies, fixed miss without varargs fallback and identifier-header termination. |
| 4: completion/snapshots/keys/diagnostics | Unfinished/failed/retried origin authority negatives; shared Ref/Cell/runtime literal handles with cleanup; post-freeze slot, alias, help metadata and contribution-list/store changes; nested lambda/immutable-guard structural keys; matcher/guard/body/get/renderer sentinels; real import permutations; reverse shape orientation, payload spans and first-pair/first-key conflict precedence. |
| 5: private layout | Remove cross-view contributor object-id constraint and Python `__all__` constraint. Preserve ordered semantic selection, per-view clause isolation, exact target identity and Genia source-access/rendering/module-equality privacy. Private signature adapters remain adaptable with independent review. |
| 6: reproducibility | Preserve constructor-only target shim and fixture probe in `tests/unit/model_b_d2a_diagnostic.py`; retain results and commands here. No completion/linking/publication stub. Clearly distinguish old-runtime fixture diagnostics, seam failures and unexecuted linked-view assertions. |

## Exact reproduction

Run from repository root on the recorded candidate. Use the existing uv project
environment; `--no-sync` makes its use explicit because this environment has no
uv.lock and executor network access is broken. It is not a claim of locked,
portable or full-suite verification. Set `UV_CACHE_DIR` to a writable scratch
cache if needed. Log paths below are scratch, not a conformance protocol.

```bash
mkdir -p work/d2a-red2
export UV_CACHE_DIR="$PWD/work/uv-cache"
uv run --no-sync pytest -q -n 2 --maxfail=20 --tb=short --junitxml=work/d2a-red2/core-lookup.xml tests/unit/test_model_b_d2a_link_core.py -k 'd2a_01 or d2a_02'
uv run --no-sync pytest -q -n 2 --maxfail=20 --tb=short --junitxml=work/d2a-red2/core-keys.xml tests/unit/test_model_b_d2a_link_core.py -k 'd2a_03 or d2a_04'
uv run --no-sync pytest -q -n 2 --maxfail=20 --tb=short --junitxml=work/d2a-red2/core-order.xml tests/unit/test_model_b_d2a_link_core.py -k 'd2a_05 or d2a_09'
uv run --no-sync pytest -q -n 2 --maxfail=20 --tb=short --junitxml=work/d2a-red2/dispatch.xml tests/unit/test_model_b_d2a_link_dispatch.py
uv run --no-sync pytest -q -n 2 --maxfail=20 --tb=short --junitxml=work/d2a-red2/publish.xml tests/unit/test_model_b_d2a_link_publish.py
```

Observed failures/passes by command: 10/0, 12/0, 6/1, 17/0, 11/1. Each command stays
below the 20-failure limit, including all in-flight xdist cases.

```bash
uv run --no-sync pytest -q -n 2 --maxfail=20 --tb=short tests/unit/test_model_b_d1_completion.py tests/unit/test_model_b_d1_preparation_failures.py tests/unit/test_model_b_slice_c_identity.py tests/unit/test_model_b_slice_c_ownership.py tests/unit/test_model_b_slice_c_keys.py tests/unit/test_r20_open_functions_cross_module.py tests/unit/test_r20_open_functions_annotations.py tests/unit/test_r20_open_functions_diagnostics.py tests/unit/test_host_binding_classification_p1_e.py tests/spec/test_model_b_d1_preservation.py tests/spec/test_r20_open_functions_shared_specs.py
uv run --no-sync pytest -q --maxfail=20 tests/unit/test_host_binding_classification_p1_e.py
PYTHONPATH=src uv run --no-sync python -m tests.unit.model_b_d2a_diagnostic
PYTHONPATH=src uv run --no-sync python -m tests.unit.model_b_d2a_diagnostic --target-shim-pytest -q --maxfail=20 --tb=short tests/unit/test_model_b_d2a_link_dispatch.py
git diff --check
```

Observed: preservation **223 passed**; final classification guard **18 passed**
(overlaps the 223, do not sum). Diagnostic probe exit 0: matcher err identity,
existing-group self/mutual recursion fixtures, nested keys and literal
base/contributor sources, constructor duplicate validation/identity/closure
retention, lock rejection and bounded-process timeout/reaping. These are not
linked-view acceptance. Shim-assisted dispatch: **17 failures**, all at missing
`genia.function_linking`; no seam suppression or manufactured passes.

## Environment, defects and limits

Linux 6.18.57 x86_64 / glibc 2.41, Python 3.12.14, pytest 9.1.1. Existing uv
environment reused; no dependency installation or production changes. The
editable installation points to the original baseline checkout; pytest's existing
`pythonpath = ["src"]` and explicit diagnostic `PYTHONPATH=src` select the candidate.

Executor git fetch failed: `Failed to connect to proxy port 8080 after 0 ms`.
GitHub connector reads/writes work. Restored signed RED commit objects using their
GitHub verification payload/signature, then reconstructed both trees from the
four exact test blobs on the local baseline. Verified Git hashes:

- Parent commit `149f675fff7696c0dcb4c35e3165cad9109517c4`, tree `684945afc7236c36d8cbd772574f5cc7804f9204`.
- Current RED `cff05d06410014622ff2557fd642dfa8c2eac3f6`, tree `46684f6ec8845999b5edc8c37503533fae44edbb`.

Restored and used the existing branch
`claude/genia-1250-d2a-test-seh3z1`, as explicitly requested. The repository branch
checker expects `issue-N-*` and rejects this existing Claude branch; that naming
check is retained as a process mismatch, not test RED. No branch renamed.

Separately identified original harness defect: the former atomicity test captured
`loaded_modules` **before** loading `clash`/`twin`; a later comparison would therefore
fail even with correct linking. Revision 2 prepares all modules before snapshotting.
This is a static downstream fixture defect, not a newly executed D2a failure.
The original author's temporary shim was not supplied; the committed diagnostic
shim is an inspectable replacement, not a claim to have recovered that artifact.
A scratch evidence-generation command initially used host Python without pytest;
it was corrected to uv Python. This was not a test run or a D2a failure.

All linked-view downstream assertions (including new race/fault tests) remain
unexecuted beyond missing seams. No runtime implementation or mock linker was
introduced to exercise them. Fault tracing/sort/constructor adapters may need
reviewed adaptation if the future private layout changes; these are instrumentation,
not language requirements. The bounded race harness is Python/Linux host-local.

No full-suite rerun or cross-host acceptance claimed. The author's historical
169 baseline failures and later missing-uv.lock failure remain separate evidence;
the focused preservation run does not resolve them. Required full regression
partitions remain later implementation/acceptance obligations. Authority docs,
production code, shared specs and historical R20 oracles are unchanged. D2b,
Slice E and R29 are not authorized; #1250/#1251 are not closed by this task.

Next: publish revision SHA and this matrix on #1250, then obtain fresh independent
Codex review. The test author does not approve this RED or authorize GREEN.
