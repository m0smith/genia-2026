# Python timeout investigation, bounded cancellation repair and #1302 acceptance

## Four decisions

1. **Python timeout cause established and adequately addressed: NO for the original seven failures.** The original one full-suite TIMEOUT and six fixture-stress TIMEOUTs remain unchanged. Controlled diagnostics establish latency sensitivity and a separate POSIX adapter-child cancellation defect; they do not identify the historical failures' cause. The narrow cancellation correction passes independent review and fixed resource-envelope acceptance.
2. **#1299 remains OPEN.** Its admission-order repair is integrated and meaningful; fresh bounded stress and negative checks pass. Historical deadline failures still need an explicit causal/evidence disposition, and the new transport correction has not been merged/verified on main. A newer green batch is not automatic closure.
3. **#1302: independently reviewed GO and MERGED.** Final reviewed head `ee06fff6a04a827e44f523ba36848f044197ab56`, tree `88045eaae54fd7f632840284893a503a3d288a63`; actual main merge `4fc63420e34ee54a7eb8b623ca9ee83bfafaa6ef` has exactly that tree. All six applicable final-head hosted workflows passed before merge. The expected-head guard was used; no repository protection was bypassed.
4. **#1251 stays OPEN; R29 stays NO-GO.** Remaining blockers are the historical timeout disposition and applicable transport-repair acceptance, plus Slice D/E and foundation/intake acceptance or a precise maintainer-approved scoped deferral. Documentation #1302 is no longer an outstanding merge blocker. #1230's retired fallback remains separately satisfied; no R29 work started.

**Recommended single next action:** review the separately published POSIX cancellation repair for merge after its applicable hosted checks; it fixes a demonstrated resource-ownership defect without pretending to resolve historical latency.

## Provenance and separation

| Evidence / action | Exact identity |
|---|---|
| Frozen main used for diagnostic experiments |`09804b565a30c2995a7d045d74faf8e880994ff4`, tree `f8a686c96aaa67034ff5aaab721c107f0e6974e0` |
| Original #1302 head independently rejected |`b58b94e3e5a225ec1c6ec7b18304c742691c44d2` |
| Corrected #1302 head, independently reviewed |`ee06fff6a04a827e44f523ba36848f044197ab56`, tree `88045eaae54fd7f632840284893a503a3d288a63` |
| Actual #1302 merge/current main |`4fc63420e34ee54a7eb8b623ca9ee83bfafaa6ef`, same reviewed tree |
| Cancellation RED |`0d5b77ec613d17e028547a25b476c70bdce4b599` |
| Cancellation implementation |`9c67cb677b2569e5cc37f06719c0971746f88a9d` |
| Independently accepted repair candidate |`1f068de7f665543a87e6b3925230118aa99a2cc3`, tree `48e9c77b62e799b6c1c38f7f940b3b755f033745` |
| Current-main integration into repair branch |`45e263cc9e15f3ae14080346d4835090285b4e4e`, tree `b1edab3fe5b31c7ff5ebe5107c525ea3de80101d` |
| Selected reviewed C++ source |`1f33886606fc94dadab679ed56182a15ca503a4b` |
| C++ binary SHA256 |`8f8c6fd62d699b5b413ed8752eb433a3d4af73788142968f1ca87ba2a5d45d98` |
| C++ declared authority contract |`6402e668ae85a1e7efe94b3ac3d51f233b730ca4`, resolvable ancestor |

Worker A owned the investigation/repair branch. Worker B used its own worktree for #1302 review/fixes; neither modified the other's branch. Reviewer C authored neither original #1302 nor the twelve-line comment/docstring fix. A further independent acceptance reviewer authored no repair changes and inspected raw results and actual source.

All full candidate acceptance below executed at **1f068de7**, not at later integration/evidence commits. The independent follow-up verified identical `src`, `hosts`, `tests`, `tools` trees and all five authority blobs at45e263cc versus1f068de7. The merged known-gap JSON differs only in its explanatory `/gaps/18/reason`. Combined documentation tests and strict build were rerun after integration; runtime acceptance was not relabelled as a new final-head execution. Subsequent process evidence additions do not change those executable trees.

Five original artifact SHA256 digests were recorded before experiments and independently checked again unchanged. Original Python full evidence remains **1025 PASS/18 UNSUPPORTED/1 TIMEOUT**; original Python fixture stress remains **194 PASS/6 TIMEOUT**. Historical individual request wall/CPU/startup measurements were not recorded; their timeout classifications alone cannot supply that missing attribution.

## Predeclared resource envelope and matrix

The plan was written before any diagnostic execution and retained unchanged. Requests use the canonical E16 transport, discovery and comparator, never a new language oracle or capability scheme. Supplementary JSON is measurement evidence, not replacement conformance evidence.

- Python3.12.14, explicit existing project virtual environment; source selected by frozen checkout/PYTHONPATH. Initial main/tree and environment are in baseline.json.
- Cgroup CPU quota `200000 100000`: two CPU bandwidth units. Memory ceiling8GiB; initial memory.current3343257600bytes (about3.11GiB), leaving about4.89GiB below that ceiling, not a reservation/guarantee of available RAM.
- Initial `memory.events:max=59689`, OOM/OOM-kill0. No max/OOM/OOM-kill increments were observed during the diagnostic matrix or acceptance. Old limit events are historical, without request timestamps tying them to the seven failures.
- No other scheduled compilation/test/documentation workload during isolation, scaling, recovery, full diagnostic or acceptance. Managed background services remain present. The two deliberately controlled CPU burners were the only scheduled competing workload in contention batches; they have a finite180s safety cap and are stopped after each batch.
- Exactly291 targeted requests in22 batches; configured concurrency1/2/4/8; one normal full1044-case eight-worker diagnostic; twelve phase probes; one synthetic timeout lifecycle probe. No failed sample was repeated/replaced or timeout increased.
- The phase/control driver mistakenly used a noncanonical capability sentinel, so three controls return PROTOCOL_ERROR. These remain three harness errors; no replacement probes were run. Nine instrumented evaluation probes pass their original expectations.
- Acceptance was separately reserved and chosen once at two workers under the documented two-CPU envelope: one full Python/C++ pair,200Python/1000C++fixture requests, eightR20 requests and both postfailure-send negatives, all real request deadlines10s.

| Phase | Case | Requests | Configured / peak active | PASS / other | Wall median / p95 / max (s) | Median reaped-child CPU (s) | Throttled delta (s) |
|---|---|---:|---:|---|---|---:|---:|
|isolated|r20|3|1 / 1|3 / 0|1.012 / 1.030 / 1.030|1.006|0.000|
|isolated|fixture|8|1 / 1|8 / 0|0.548 / 0.594 / 0.594|0.545|0.000|
|scaling|r20|8|1 / 1|8 / 0|0.988 / 1.058 / 1.058|0.986|0.000|
|scaling|fixture|32|1 / 1|32 / 0|0.543 / 0.619 / 0.703|0.538|0.000|
|scaling|r20|8|2 / 2|8 / 0|1.199 / 1.408 / 1.408|1.170|0.285|
|scaling|fixture|32|2 / 2|32 / 0|0.578 / 0.708 / 0.730|0.565|0.361|
|scaling|r20|8|4 / 4|8 / 0|1.856 / 3.513 / 3.513|1.140|3.559|
|scaling|fixture|32|4 / 4|32 / 0|1.334 / 1.873 / 2.052|0.660|10.141|
|scaling|r20|8|8 / 8|8 / 0|5.821 / 6.137 / 6.137|1.446|5.899|
|scaling|fixture|32|8 / 8|32 / 0|2.533 / 3.663 / 3.788|0.651|10.486|
|controlled_contention|r20|4|1 / 1|4 / 0|1.666 / 1.732 / 1.732|1.076|6.620|
|controlled_contention|fixture|16|1 / 1|16 / 0|0.949 / 1.005 / 1.005|0.597|14.625|
|controlled_contention|r20|4|2 / 2|4 / 0|1.736 / 3.648 / 3.648|1.104|5.025|
|controlled_contention|fixture|16|2 / 2|16 / 0|1.399 / 2.091 / 2.091|0.637|11.884|
|controlled_contention|r20|4|4 / 4|4 / 0|3.826 / 3.946 / 3.946|1.154|3.920|
|controlled_contention|fixture|16|4 / 4|16 / 0|1.899 / 2.606 / 2.606|0.622|7.965|
|controlled_contention|r20|4|8 / 4|4 / 0|3.561 / 3.946 / 3.946|1.216|3.940|
|controlled_contention|fixture|16|8 / 8|16 / 0|3.499 / 4.574 / 4.574|0.696|7.733|
|recovery|r20|4|1 / 1|4 / 0|1.008 / 1.037 / 1.037|1.007|0.000|
|recovery|fixture|16|1 / 1|16 / 0|0.547 / 0.630 / 0.630|0.545|0.000|
|recovery|r20|4|8 / 4|4 / 0|2.240 / 2.420 / 2.420|1.161|2.215|
|recovery|fixture|16|8 / 8|16 / 0|2.433 / 3.718 / 3.718|0.664|5.105|

All291 targeted results are PASS; all FAIL/UNSUPPORTED/protocol_error/crash/timeout/exception/incomplete counts in those batches are zero. The table's p95 uses nearest-rank ceiling recomputed from retained individual walls; raw files are unchanged. Worker-local reaped-child CPU is attributable for these completed samples; timeout CPU would be censored, and global cgroup counters include background/burner work. Configuredc8 with only four R20 requests has an observed peak of four in contention/recovery; it is not evidence of eight simultaneous R20 requests there. The scalingc8 R20 batch genuinely reaches eight.

The original matrix driver writes whole batch files after completion rather than streaming every result and can wait for pool shutdown. No batch was interrupted or missing in this execution; all fixed indices were independently checked. That limitation prevents claiming comprehensive interruption robustness. Acceptance streams request-begin/end events and preserves full-stage statuses. The subreaper diagnostic supervisor observes/reaps adopted exits; it changes no Genia runtime semantics and is not evidence of universal process-tree cleanup.

## Startup, evaluation and cancellation observations

Nine valid instrumented eval requests delegate unchanged adapter main/handle/run_case and preserve protocol stdout and comparators. Side-channel instrumentation has overhead. Observed adapter import boundaries are about0.17–0.22s. `run_case` ranges: arithmetic0.154–0.181s, R200.715–0.787s, repaired fixture0.275–0.344s. `run_case` includes the second interpreter startup, so these do **not** cleanly separate interpreter startup from parsing/evaluation. No10s startup failure was reproduced. Three malformed capability controls are retained as PROTOCOL_ERROR and cannot count as successful capability timing checks.

The single synthetic transport probe uses an adapter spawning a blocking Python child. With the canonical10s deadline, TIMEOUT returns at10.0087s, the adapter is gone, and its same-group synthetic child is still sleeping. The diagnostic supervisor reaps the child at15.0484s, status0. This demonstrates direct-adapter cancellation does not stop same-group descendants; it does not prove a real Genia evaluator survived any original request. Source inspection shows Python exec_eval.py can launch a second interpreter exposed to this ownership boundary. On POSIX, subprocess.run kills/waits for the direct adapter on timeout; it does not wait for inherited pipe EOF in that timeout branch. The observed failure is surviving work, not a falsely claimed15s transport return.

Before any production edit, new host-mechanics RED tests produce **2FAIL/1PASS**: timeout and injected caller cancellation leave a fixture child live; the successful-request control passes. An isolated subreaper controller reliably cleans/reaps its fixture children, including PID-file recovery on unexpected exceptions. Unit artificial1s timeout is confined to transport stubs; every real diagnostic/conformance/acceptance request keeps10s.

## Competing hypotheses and conclusion

| Hypothesis | Supported, rejected or unresolved |
|---|---|
| CPU quota/scheduling contention |Supported as a present latency contributor by controlled work, resource counters and wall-versus-childCPU separation. Not established as the cause of the original ten-second failures; the matrix does not reproduce them. |
| Excessive external concurrency |Raises measured latency (for example R20 median0.988s atc1 versus5.821s atc8), but full normalc8 already passes before the repair. Concurrency alone is insufficient to reproduce the historical failures here. |
| Adapter/interpreter startup latency |Measurable and material; no reproduced10s startup failure and incomplete historical timing. Attribution remains unresolved. |
| Mutual-recursion performance/regression |Unchanged R20 correctness passes. Current latency is resource sensitive; no version-to-version regression experiment was performed, so a regression is not categorically excluded under unobserved conditions. |
| Process/Ref synchronization or lifecycle defect |No Genia synchronization defect reproduced. FIFO/admission/fail-stop and postfailure checks pass in finite samples; rare/unobserved races are not disproved. |
| Harness scheduling/cancellation/reaping |Separate same-group cancellation defect is established and corrected by RED/GREEN mechanism evidence. It is not established as the trigger or amplifier of any original seven failures. |
| Memory/IO/scheduling interactions |Plausible, unresolved: historical memory-limit events lack request attribution; pressure interfaces were unavailable; current memory counters do not reproduce pressure. No synthetic memory stress was added outside the frozen matrix. |

**Historical root-cause evidence is insufficient.** A clean eight-worker full diagnostic **before** the patch already returns1026PASS/18UNSUPPORTED/all actual failures0, with the R20 request5.258s. Therefore later green acceptance must not be credited to the patch as proof that it repaired historical latency. The appropriate demonstrated correction is owned POSIX cancellation; the resource-aware two-worker procedure is an evidenced operating envelope, not a timeout waiver or universal determinism claim.

## Narrow remediation and verification

The existing generic transport now starts a private POSIX session/process group for each adapter request. On communication timeout or caller cancellation it kills that group and reaps the direct adapter, then re-raises the original exception so TIMEOUT taxonomy and captured partial stdout/stderr remain intact. Both Python and C++ use this existing transport. Successful-request descendant behavior is unchanged. Non-POSIX retains the original subprocess.run path; detached descendants are outside the bounded group guarantee. This is not a sandbox or a promise to reap grandchildren the caller does not own.

No Genia runtime, syntax, Core IR, wire envelope, capability declaration, semantic expectation, case selection, comparator, timeout default, existing assertion or checker baseline changed. Tool README documents ownership limits; run-change documents resource-aware sequencing and preservation of failures. STATE/RULES/REPL README/README/AGENTS and MCP facts require no semantic expansion.

| Check | Actual result |
|---|---|
| Committed RED |2expectedFAIL/1controlPASS,5.32s, before implementation |
| Focused cleanup/protocol/Python-adapter GREEN |56PASS,4.04s |
| Nearby host-executor/capability/evidence |55PASS,1.24s |
| Independent exact-candidate transport regression |40PASS via uv run,2.67s; an earlier explicit-venv40PASS is separately retained, not substituted |
| Changed-code lint / maintained-code ratchet |PASS; no baseline additions/refresh |
| Candidate docs/registry/portability |244PASS/34existing skips; profile--check and strict buildPASS |
| Main-doc integration check at45e263cc |244PASS/34existing skips; strict build7.74s; checker9973records/2793legacy/1exclusion/0errors |
| Full Python acceptance at1f068de7 |1044 total:1026PASS/18UNSUPPORTED; FAIL/protocol_error/crash/timeout/invalid all0;226.597s, child user/system410.752/36.756s |
| Full selected C++ acceptance at1f068de7 |1044 total:295PASS/749UNSUPPORTED; every actual failure class0;1.58s; historical declared contract means current-suite compatibility, not full current-contract support |
| Canonical declared-gap parity |OK, exit0; unsupported stays separate from PASS |
| Python corrected fixture acceptance |200/200PASS atc2/10s; wall range0.472–0.705s |
| C++ corrected fixture acceptance |1000/1000PASS atc2/10s; wall range0.00196–0.00977s |
| Python R20 acceptance |8/8PASS atc2/10s; wall range0.874–1.161s |
| Post-failure sends |Both exact host-specific errors, empty stdout/exit1, unreachable print absent |

Every acceptance index and stage is present; the event stream ends normally. No FAIL/TIMEOUT/protocol_error/crash/invalid/exception was discarded. The existing fixture still gates boom on an unset Ref until all sends return, preserving FIFO1,2, accepted queued3 discard, permanent failure and original expected output. Full shared expectations remain unchanged. Test selections overlap; do not add them as a distinct-test total. Existing platform/skip markers are not silently removed; the new Linux observer test is explicitly host-internal, not a shared-semantic exclusion.

## Independent review and #1302 disposition

Worker B published the original-head [NO-GO review5716361448](https://github.com/m0smith/genia-2026/pull/1302#pullrequestreview-5716361448): maintained-code CI found missing shell module documentation and stress helper documentation in newly archived support files. The fix adds only twelve comment/docstring lines, preserving shell executable lines and Python docstring-stripped AST; no baseline was changed.

Reviewer C independently inspected the entire finalhead, all five authority identities, reason-only known-gap edit, historical failure visibility, all27 archived log digests/lengths and complete four1044-case/two stress ledgers. Fresh final-head docsync244PASS/34existing skips, checker26PASS, maintained-code0errors, generators/coverage lint and default/strict builds pass. Public independent [review5716568287](https://github.com/m0smith/genia-2026/pull/1302#pullrequestreview-5716568287) and [final GO5718787155](https://github.com/m0smith/genia-2026/pull/1302#pullrequestreview-5718787155) are coordinator-transmitted attributable reviews, not author self-approval.

All final-head workflows succeeded: [CI41101717162](https://github.com/m0smith/genia-2026/actions/runs/41101717162), [Docker41101717198](https://github.com/m0smith/genia-2026/actions/runs/41101717198), [Docs41101717338](https://github.com/m0smith/genia-2026/actions/runs/41101717338), [code-doc41101718059](https://github.com/m0smith/genia-2026/actions/runs/41101718059), [parity41101717165](https://github.com/m0smith/genia-2026/actions/runs/41101717165), [LLM41101717167](https://github.com/m0smith/genia-2026/actions/runs/41101717167). Actual PR head was rechecked unchanged; main/ruleset reads exposed no blocking rule. The user explicitly authorized this conditional merge, which used the expected-head guard and produced4fc63420/same reviewed tree. This does not relabel premerge checks as new postmerge executions.

For the separate cancellation repair, reviewer C independently inspected actual implementation/RED/design and final docs, with scoped PASS. The independent acceptance reviewer then inspected actual candidate diff and every raw diagnostic/acceptance record, ran the compliant40-test regression, verified old digests unchanged and reported PASS for maintainability, bounded behavior, docs and finite acceptance. It explicitly gives NO-GO to claiming historical timeout cause resolved. Final integration was independently checked by object identity; no new runtime tests were represented as executed there.

## #1299 original acceptance matrix

| Original criterion | Current disposition |
|---|---|
| Prove original admission race and preserve failures |Prior deterministic RED/old-vs-new failure frequencies remain documented, unchanged. Historical966/34 and970/30 per1000,294PASS/1FAIL/749UNSUPPORTED and later RED observations are not erased. |
| Deterministic admission, meaningful FIFO/fail-stop and postfailure rejection |Integrated Ref gate is preserved; structural ordering, original output and both exact negative checks remain meaningful. No runtime/capability/oracle change. |
| Corrected stress with zero actual failures |Finite candidatec2 acceptance200Python/1000C++PASS; original uncontrolledc8 Python194PASS/6TIMEOUT remains a separate failed observation. Broader deadline-failure attribution/disposition is still incomplete. |
| Final full Python/C++ and hosted parity checked and retained |Main's prior hosted1026/18 and295/749 retained; new candidate local full pair/parity passes. The cancellation correction is not yet merged or certified by a postmerge main run. |
| Independent review preserves R25section6.2 |Original fixture independent reviews remain; new independent transport/acceptance review passes. Neither is a blanket release authorization. |
| Link resolution to#1251/#1270 before final signoff |Repair integration and this report are linked; final acceptance/signoff remains open. |

**Leave #1299 open.** m0smith/authority conformance-test-runtime owner must disposition the original resource/cancellation observations and the focused repair's eventual main acceptance. No issue criterion is silently rewritten or waived. #1251 retains that evidence limitation and D/E semantic-foundation gates; R29 is not unblocked by documentation or bounded C++ issue closure.

## Reproducibility and retained evidence

The frozen plan, baseline/resource snapshots, all22 batch JSON files, full diagnostic logs/E16 evidence, twelve phase streams, synthetic lifecycle records, RED/GREEN/check logs, full acceptance streams/E16 evidence, all1208 indexed acceptance comparisons, both negatives, derived distributions and independent review are retained with SHA256/byte manifest under `.genia/process/issue-1251-python-timeout-evidence/`. Immutable scratch scripts are archived with their executed sources; they are measurement support, not new maintained runtime/conformance mechanisms.

Principal commands used the explicit project venv, writable uv cache and each named checkout's src/PYTHONPATH. Pytest acceptance/check invocations use `uv run --no-sync pytest`; the independently corrected invocation is separately recorded. The canonical full runs are:

```text
python -m tools.spec_runner --verbose --host-jobs 8 --host '<venv-python> -m hosts.python.protocol_adapter' --evidence full-diagnostic-python-evidence.json
python -m tools.spec_runner --verbose --host-jobs 2 --host-timeout 10 --host '<venv-python> -m hosts.python.protocol_adapter' --evidence python-evidence.json
python -m tools.spec_runner --verbose --host-jobs 2 --host-timeout 10 --host '<selected-genia-adapter>' --evidence cpp-evidence.json
python -m tools.spec_runner.host_parity_gate --python-evidence python-evidence.json --cpp-evidence cpp-evidence.json --known-gaps spec/known_host_gaps.json
uv run --no-sync pytest -q tests/unit/test_spec_runner_timeout_cleanup.py tests/unit/test_spec_runner_protocol.py tests/unit/test_python_protocol_adapter_762.py
uv run --no-sync pytest -q tests/unit/test_spec_runner_host_executor.py tests/unit/test_spec_runner_capabilities.py tests/unit/test_spec_runner_evidence.py
uv run --no-sync pytest -q tests/doc/test_semantic_doc_sync.py tests/doc/test_state_anchors_and_registry_sync.py tests/doc/test_portability_contract_sync.py
uv run --no-sync python -m tools.code_documentation --base-ref <main-sha> --inventory <evidence-inventory.json>
uv run --no-sync python tools/gen_mcp_language_profile.py --check
uv run --no-sync python tools/stage_docs_for_mkdocs.py
uv run --no-sync mkdocs build --strict
```

Timed batch commands/sampling, CPU-burner safety bounds and phase instrumentation are fully preserved in the frozen plan and executed scratch-source archive. Failed capability controls, RED assertions, the intentional synthetic timeout and historical failures remain explicit. No runtime timeout increase, retry-to-green, semantic failure reclassification, capability downgrade, skipped required case, weakened assertion or unrelated cleanup was introduced.
