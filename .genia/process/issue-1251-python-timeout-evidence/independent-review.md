# Independent final review — bounded cancellation repair

Reviewer: Codex acceptance_review agent, independent of implementation and documentation authors. I authored no repair code and made no branch edits. Reviewed 2026-10-30.

Exact reviewed HEAD: `1f068de7f665543a87e6b3925230118aa99a2cc3`; tree `48e9c77b62e799b6c1c38f7f940b3b755f033745`; clean checkout at review. Actual diff against main `09804b565a30c2995a7d045d74faf8e880994ff4` inspected, including all five new process records, protocol helper/caller, unit regression and both documentation additions. This review supplements reviewer C's earlier implementation review; it does not certify #1302's separate branch.

## Verdict

**PASS for maintainability, bounded behavior, documentation truth and the specified finite resource-envelope acceptance. GO to publish the focused repair and attributable evidence.** No blocking code or documentation findings. **NO-GO for claiming the original seven Python timeout causes established or adequately resolved.** Neither verdict closes #1251/#1299, authorizes R29, or merges anything.

The helper is localized at the existing generic transport boundary and applies equally to Python and C++ adapter invocations. POSIX `start_new_session=True` gives an owned process group; communication timeout/caller exception kills that group and reaps the direct adapter. It avoids killing the runner's ambient group. Timeout exception diagnostics and existing taxonomy flow through the unchanged caller. Success returns normal output/classification; non-POSIX retains its existing subprocess.run path. Only already-gone groups are ignored, while other cleanup OS errors propagate as documented. No language runtime, Core IR, wire envelope, oracle, capability declaration, case discovery, timeout default or baseline was edited. No unnecessary abstraction or duplicated semantic mechanism was added.

The Linux-only subreaper controller is justified for observing/reaping fixture grandchildren in a container. Timeout and injected caller cancellation assert that live child work stops; the success control explicitly retains the prior success boundary. RED actually records 2 failures/1 pass with surviving children; GREEN records 56 passing focused tests. I independently executed `/workspace/genia-2026/.venv/bin/python -m pytest -q tests/unit/test_spec_runner_timeout_cleanup.py tests/unit/test_spec_runner_protocol.py` at exact HEAD: **40 passed in 2.64s**. This was a separate small regression, not a replacement acceptance run. Existing nearby 55-pass, documentation 244-pass/34-existing-skip, checker/lint/profile and strict staged MkDocs logs were inspected; no full repository pytest claim is made.

Both durable documentation edits accurately distinguish POSIX same-group ownership from detached descendants, direct-child reaping from grandchild ownership, non-POSIX limitations, and finite evidence from determinism. Root authority documents and MCP facts need no new semantic claim for this infrastructure-only correction. The process records consistently retain historical failures and do not attribute their cause to this repair. Distillation into tool and process documentation is proportionate.

## Evidence validation

I parsed every diagnostic batch and every acceptance result, checked sample counts/index completeness and classifications, inspected raw full logs/events, driver code, lifecycle/phase data and RED/GREEN evidence. The driver uses canonical discovery and `execute_spec_via_host` comparison, fixed sample counts, no retries, original 10-second requests and two concurrent slots. Full Python/C++ invocations explicitly retain `--host-timeout 10 --host-jobs 2`. Acceptance begin records the exact reviewed commit/tree, Python 3.12.14, C++ source `1f33886606fc94dadab679ed56182a15ca503a4b` and binary SHA256 `8f8c6fd62d699b5b413ed8752eb433a3d4af73788142968f1ca87ba2a5d45d98`.

Resource envelope: two CPU quota (`200000 100000`), 8 GiB memory ceiling, no competing scheduled tests/builds. Cgroup counters are retained; for full Python, wall 226.597s, child user/system CPU 410.752/36.756s, throttled periods rose 410 and throttled time 1.450s. Historical memory max events exist, but no acceptance OOM/OOM-kill increment or causal link to old requests is demonstrated.

| Observation | Independently checked outcome |
| --- | --- |
| Frozen 22-batch diagnostic matrix, concurrency 1/2/4/8 and controlled two burners | 291 PASS; no actual failures; no missing samples |
| Normal eight-worker full Python diagnostic | 1,026 PASS / 18 UNSUPPORTED / zero actual failures, all 1,044 cases |
| Exact-head full Python acceptance | 1,026 PASS / 18 UNSUPPORTED / zero actual failures, all 1,044 cases |
| Exact-head runner with selected C++ acceptance | 295 PASS / 749 UNSUPPORTED / zero actual failures, all 1,044 cases |
| Capability parity gate | exit 0, existing declared gaps retained; UNSUPPORTED is not PASS |
| Python FIFO/fail-stop acceptance | 200/200 PASS; request wall range 0.472–0.705s |
| C++ FIFO/fail-stop acceptance | 1,000/1,000 PASS; request wall range 0.00196–0.00977s |
| Python R20 acceptance | 8/8 PASS; request wall range 0.874–1.161s |
| Post-failure send negatives | Both match exact existing host diagnostics, empty stdout and exit 1; unreachable print absent |
| Instrumented evaluation probes | Nine PASS; three malformed capability controls retained as PROTOCOL_ERROR, excluded from semantic success counts |

I recomputed all five original evidence digests against baseline.json: unchanged. Original full Python remains 1,025 PASS / 18 UNSUPPORTED / 1 TIMEOUT; original stress remains historical 194 PASS / 6 TIMEOUT, not overwritten by acceptance. All acceptance request_end records total 1,208 with complete fixed indices and PASS classifications. Both full runs, parity and both negative stages completed; the event stream ends normally.

## Hypothesis assessment

* CPU quota/scheduling and excessive external concurrency: supported as latency contributors. For example, uncontented R20 scaling median grows from 0.988s at one slot to 5.821s at eight; fixture medians grow from 0.543s to 2.533s. Controlled contention also raises latency. Neither experiment reproduces the original ten-second failures; their causal attribution remains unresolved. Choosing two slots is a supported operational envelope, not proof of a historical fix.
* Startup/interpreter costs: phase probes show measurable startup/evaluation costs, but no reproduced ten-second startup failure. Three capability controls have an instrumentation sentinel defect and cannot support successful capability timing claims. Historical startup causation remains unresolved.
* Mutual-recursion performance/regression: tested correctness passes through unchanged canonical expectations; sampled latency is concurrency-sensitive. No regression is demonstrated, and finite samples cannot exclude one under an unobserved condition.
* Process/Ref synchronization/lifecycle: canonical FIFO/fail-stop stress and exact post-failure rejection pass on both hosts. No runtime synchronization defect is reproduced. These observations do not prove absence of rare races or independently satisfy every #1299 administrative acceptance item.
* Harness cancellation/reaping: a distinct real defect is established. The baseline synthetic canonical ten-second probe returned TIMEOUT at 10.009s with direct adapter gone and same-group child still sleeping, reaped only at 15.048s. RED reproduces timeout and caller-cancellation leaks; repaired tests stop that work. Python's second-interpreter launch shares this exposure. No evidence proves a real Genia descendant survived any of the original seven requests or that such survival caused them.
* Interactions and historical memory/scheduling conditions: plausible but unresolved; retained cgroup history is insufficient for request-level attribution. A green baseline eight-worker diagnostic already precedes repair, further preventing causal credit for new success being assigned to the patch.

## Limits and disposition

The guarantee is POSIX same-group cancellation, not a sandbox, detached-child killer, grandchild reaper or universal bounded kernel termination guarantee. Runtime semantics and Windows behavior are unchanged. Finite two-worker acceptance does not establish determinism or acceptance at arbitrary load. C++ unsupported surfaces remain unsupported; R20 cross-module support is not inferred for C++. No independent live GitHub status review or #1302 exact-head review is included in this delegated code/acceptance review; those require the parent's separately collected evidence.

Publish this narrow repair/evidence with historical timeout causation explicitly unresolved. Keep #1251 and R29 blocked; reconcile #1299's original criteria individually before any closure. The selected-envelope verification and demonstrated cancellation fix pass, while the broader original-timeout objective remains open.

## Invocation-compliance addendum

The direct-venv pytest invocation above is retained as a separate observed 40-PASS result; it did not follow AGENTS.md's required `uv run` invocation. Corrected that workflow detail by executing the same small regression exactly once through the mandated runner, with no competing tests:

```sh
UV_CACHE_DIR=/workspace/.cache/uv UV_PROJECT_ENVIRONMENT=/workspace/genia-2026/.venv PYTHONPATH=/workspace/work/python-timeouts/authority/src uv run --no-sync pytest -q tests/unit/test_spec_runner_timeout_cleanup.py tests/unit/test_spec_runner_protocol.py
```

Executed in `/workspace/work/python-timeouts/authority`: **exit 0, 40 passed in 2.67s**. Raw log: `/workspace/work/python-timeouts/evidence/independent-final-review-uv-regression.log`. This corrects invocation compliance; it does not replace a failed assertion or rerun the finite acceptance matrix.

Parent reports main has subsequently advanced through authorized #1302 documentation merge `4fc63420` / tree `88045e`. This review and its acceptance evidence remain explicitly pinned to repair HEAD `1f068de7f665543a87e6b3925230118aa99a2cc3` / tree `48e9c77b62e799b6c1c38f7f940b3b755f033745`, compared against prior main `09804b565a30c2995a7d045d74faf8e880994ff4`; no review of an integrated or rebased repair head is implied. I made no Worker A branch mutation.

## Independent integration carry-forward review

Independently inspected actual git objects and diff for accepted `1f068de7f665543a87e6b3925230118aa99a2cc3` → integrated `45e263cc9e15f3ae14080346d4835090285b4e4e` (tree `b1edab3fe5b31c7ff5ebe5107c525ea3de80101d`), after current main `4fc63420e34ee54a7eb8b623ca9ee83bfafaa6ef` was merged. Checkout was clean. **PASS for carry-forward of the existing code/behavior review.** The `src`, `hosts`, `tests`, and `tools` tree objects are byte-for-byte identical between the two commits; all five authority document blobs (`GENIA_STATE.md`, `GENIA_RULES.md`, `GENIA_REPL_README.md`, `README.md`, `AGENTS.md`) are also identical. Recorded exact object IDs in `/workspace/work/python-timeouts/evidence/independent-integration-objects.json`.

The known-gap JSON was parsed recursively with identical container types, dict keys and list lengths required. Exactly one scalar changed: `/gaps/18/reason`, the explanatory reason for `default_open_functions`. Capability, affected host/tests, tracking and removal fields are unchanged. Inspected wording accurately states integrated fixture repair and retained historical evidence/individual acceptance; it does not fabricate C++ support or waive failures. Remaining merged differences comprise #1302 documentation and process/evidence artifacts; there is no production source, host, test or tools code change. The preserved process evidence includes executable support scripts, but these are historical evidence under `.genia/process`, not modified runtime/runner code.

Full acceptance remains **executed at `1f068de7`**, not relabelled as executed at `45e263cc`. Object equality supports carrying its code/test behavior evidence forward; this static integration review does not constitute a new runtime execution or an independent repeat of #1302's full build/review. No new runtime tests were run for this follow-up. Subsequent process-report/archive commits are not pre-approved by this exact-head inspection; they can carry evidence forward only with their scope separately verified. Historical causes remain unresolved and issue/R29 limits above remain unchanged.
