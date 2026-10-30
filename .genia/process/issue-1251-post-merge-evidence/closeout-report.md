# #1251 post-merge verification and acceptance reconciliation

## Decisions

1. **Slice C fully integrated and verified on main: NO.** Integration and hosted checks are verified; the fresh local evidence is not fully green. Python full external-host conformance has one retained 10s timeout; a separate fixed Python #1299 stress batch has six retained 10s timeouts. The paired local parity gate correctly fails. No retry, timeout increase, skip, assertion weakening or failure reclassification was used.
2. **#1251 remains OPEN.** Blockers: the retained local verification failures need an explicit evidence-based disposition; documentation correction #1302 awaits review/merge; Slice D/E and the original foundation/intake acceptance remain incomplete without an explicit maintainer-approved scope disposition.
3. **R29: NO-GO.** Complete the required D/E semantics and prerequisite acceptance, or record a bounded maintainer-approved exception defining exactly what R29 may rely on. #1230's removed fallback is independently satisfied and is not resurrected.

The user authorizes criterion-satisfied individual closures. C++#53/#54 and #1299 are evaluated separately below; no #1251 closure, main merge, test waiver or R29 work is performed.

## Exact provenance

GitHub confirms PR [#1270](https://github.com/m0smith/genia-2026/pull/1270) merged on 2026-10-30 at 16:25:11 UTC. Fresh `git fetch origin main` agrees with GitHub; main has not advanced beyond the merge at the final provenance check.

| Identity | SHA |
|---|---|
| Current main / actual #1270 merge | `09804b565a30c2995a7d045d74faf8e880994ff4` |
| Actual merged-main tree | `f8a686c96aaa67034ff5aaab721c107f0e6974e0` |
| Reviewed candidate / second merge parent | `663a727dd5b0cc967fb633255e15aa93e494d566` |
| Reviewed candidate tree | `a2bed8c3fdc10bdac502ca083f217ef0b12ee5fe` |
| First merge parent | `25a9c07013d3ed1169f4b707b7756044256e0a58` |
| Selected C++ source in both workflows | `1f33886606fc94dadab679ed56182a15ca503a4b` |
| Selected C++ tree | `f647b244b43f87eaeefe803c2b79e7934a4fe871` |
| C++ #60 merge | `fef41e58dcd3b80aaedcac98c92943fcfbfd1945` |
| C++ declared authority contract | `6402e668ae85a1e7efe94b3ac3d51f233b730ca4` |

The C++ merge tree equals the selected reviewed-source tree. Its older declared contract is a resolvable authority ancestor: these current-suite C++ results are **compatibility evidence**, not a declaration of full current-contract support.

The actual main tree differs from reviewed candidate663a in five main-only #1285 process files and `tests/unit/test_r28_mcp_conformance_run.py`'s pre-existing removal of a wall-clock assertion. Source/host/spec trees agree, but the complete candidate/main trees do not. The actual main tree also equals the synthetic tree recorded by the final pre-merge report; that historical equality is not substituted for the fresh main runs here. This task changes no test assertion.

Authority code/specs/tests were unchanged during verification. A process-only pre-flight commit was created while checks were active, then moved to a separate documentation worktree; the verification checkout was returned to the exact merge commit. No executable authority file changed. Both local host-evidence documents record checkout09804b. Correction work is isolated on `issue-1251-post-merge-verification`; it is not presented as tested main.

## Fresh external-host results

All 1,044 cases are accounted for in every full run. UNSUPPORTED remains separate from PASS.

| Run | PASS | UNSUPPORTED | FAIL | Protocol error | Crash | Timeout | Invalid |
|---|---:|---:|---:|---:|---:|---:|---:|
| Local Python, full main suite |1,025|18|0|0|0|1|0|
| Local selected C++, full main suite |295|749|0|0|0|0|0|
| Hosted Python, actual main |1,026|18|0|0|0|0|0|
| Hosted selected C++, actual main |295|749|0|0|0|0|0|

The accepted pre-merge comparison was Python1026/18 and C++295/749. A per-case ledger reconstructed from canonical discovery and explicit nonpass records matches all1,044 C++ classifications between fresh local and hosted runs. Python differs only at `r20-cross-module-view-mutual-tail-call`: local TIMEOUT, hosted PASS. No aggregate matching hides a per-case change.

The local case exceeded the unchanged10.0s external-adapter deadline. It performs20,000 mutually recursive linked-view/ordinary calls. The independently scheduled hosted external request passed in3.739s; hosted in-process R20 coverage also passed. Those are separate observations, not a local failure reclassification.

The workspace has a2-CPU cgroup quota (`cpu.max=200000 100000`) and substantial observed throttling. I oversubscribed it by running compilation, external requests and other tests concurrently. Contention is plausible, but this evidence does not establish causation or rule out another defect. The local parity command correctly exits1 with `EVIDENCE FAILURE: python evidence has timeout=1 (must be 0)`. No repeat of the failed full run or timeout case was used to seek green.

## Hosted main evidence

Fresh producer logs confirm checkouts of actual authority09804b and C++1f338866, not just PR-head metadata.

| Workflow / job | Actual result |
|---|---|
| [CI41089720094](https://github.com/m0smith/genia-2026/actions/runs/41089720094) |7,547 PASS/63 existing skips; separate31 loopback PASS; in-process semantic1,044 PASS/0 FAIL/0 invalid |
| Same CI official MCP-client job |42 PASS; VS Code, cheatsheet and doc-coverage jobs also pass |
| [Parity41089720060](https://github.com/m0smith/genia-2026/actions/runs/41089720060) |Python1026/18, C++295/749, every actual failure class zero; gate OK |
| [Docs41089720043](https://github.com/m0smith/genia-2026/actions/runs/41089720043) |217 semantic/doc checks PASS; reference/coverage checks, staged strict build and deployment pass |
| [Code documentation41089720041](https://github.com/m0smith/genia-2026/actions/runs/41089720041) |PASS |
| [LLM instructions41089720087](https://github.com/m0smith/genia-2026/actions/runs/41089720087) |PASS |

The parity artifact [12993966364](https://github.com/m0smith/genia-2026/actions/runs/41089720060/artifacts/12993966364) is1,498bytes, unexpired through2027-01-28; metadata digest `dc7fdf7f3eb5bfe950b602d51bf9266c93dfd5fa9e7db3d8f6d0ecfa68af0d74`. Producer logs and metadata were inspected; the connector supplied a ZIP reference, but ZIP bytes were not independently inspected. This does not imply artifact-byte validation.

There is no automatic Docker-workflow push run for main in the current workflow trigger. Fresh local Docker integration is therefore reported separately rather than mislabelling the old PR Docker run as new main evidence.

## Local regression, documentation and Docker ledger

Selections overlap and are not added together as a distinct-test total.

| Check | Actual fresh result |
|---|---|
| Main Model B A/B/C, optimizer/ownership/keys/consumers, R20, modules/isolation, REPL, Cell/Process and full tests/doc selection |1,339 PASS/35 existing skips,1072.43s; includes143 per-ID Slice C real-protocol checks using their unchanged repository test settings |
| Nearby concurrency, profile, doc-style/cheatsheet and examples selection |223 PASS,130.79s |
| CLI, Outcome, Flow/pipeline and MCP-language/portability selection |336 PASS,113.50s |
| Core IR/shared IR/tagged numeric/process-IR regression selection |89 PASS,31.93s |
| Correction-branch semantic docs, STATE anchors/registry and portability docs |244 PASS/34 existing skips,6.25s |
| Profile/reference generators, coverage/style lint |--check and lint exit0; main reference also checked before correction |
| Staged default and explicit strict MkDocs, correction branch |Both exit0,71.81s/56.65s; default config already strict:true; main strict producer also passes |
| Native GCC Release selected C++ |7/7 CTest PASS;18 direct acceptance checks plus guard-field/capture assertions PASS |
| Fresh Docker image / integration |Pinned Python3.14.7, uv0.12.18, Clang22;12 representative Python tests PASS; independent Release build and7/7 CTest PASS; formatting and clang-tidy exit0 with diagnostics retained; full C++1044/295 PASS/749 UNSUPPORTED and all actual failure classes0 |

The Docker virtual environment was explicitly created with Python3.14.7. Existing .python-version3.12 caused an informational uv --no-sync environment-request warning; commands used the created3.14 environment and were not rerun. This differs from local outer Python3.12/GCC14 and is recorded, not presented as one toolchain.

The five authority files STATE/RULES/REPL README/README/AGENTS remain byte-identical to merged main in the correction PR. STATE is42,997words. Their partial Model B claims already match the implementation; no semantic expansion, book/cheatsheet rewrite or generated-profile change is warranted.

Draft [#1302](https://github.com/m0smith/genia-2026/pull/1302) corrects stale host prose claiming #1299 is unresolved and #1270 remains a candidate awaiting main. The existing gap JSON differs structurally only at `/gaps/18/reason`; values, affected cases, removal conditions, protocol and oracles are unchanged. The prose retains historical failures and separates repair integration from issue/release acceptance. The draft has a pre-flight and bounded author documentation review; it has no new independent approval or merge authorization.

## #1299 acceptance reconciliation

The repaired shared source uses one unset Ref: the boom handler cannot fail at `ref_get(admitted) / 0` until the root finishes all four sends and sets the Ref. Existing FIFO makes1 and2 run first; boom permanently fails; accepted queued3 is discarded. Expected stdout remains `[[1, 2], true, false, true]\n`, stderr empty, exit0. Python and C++ exact post-failure negative requests both return their existing error/exit1 and never print the unreachable marker.

| Original criterion | Disposition |
|---|---|
| Prove mechanism and preserve baseline frequencies |PASS: existing deterministic RED and retained original stress evidence inspected |
| Deterministic admission and meaningful FIFO/fail-stop/postfailure rejection |PASS within reviewed mechanism and fresh checks; no runtime change |
| Repeated corrected stress with zero actual failure classes |**INCOMPLETE:** fresh selected C++1000 PASS/0 other, but Python194 PASS/6 TIMEOUT in200; both max8 concurrent,10s, no retries |
| Final Python/C++ full conformance and hosted parity checked and retained |Executed and retained; local Python full run has a separate R20 timeout, so no all-green local certification |
| Independent review preserves R25§6.2 meaning |PASS: original repair maintainability/final semantic reviews and committed evidence inspected; original fixture scheduling and negative regressions remain present |
| Link repair to #1251/#1270 before release truth signoff |Repair integrated through #1301/663a/#1270; this report links final evidence, but release signoff remains blocked |

**Keep #1299 OPEN.** Authority conformance/test-runtime owner, with m0smith accountable, must disposition the fresh Python deadline failures before this zero-failure stress criterion can be marked complete. Six timeouts are not FIFO failures or unsupported cases, and are not silently discarded. Do not weaken the oracle or increase the production deadline.

Historical observations remain valid: old966 PASS/34 FAIL and reviewed970/30 per1,000; independent198/2 each per200; earlier full294 PASS/1 FAIL/749 UNSUPPORTED; later deterministic-repair RED191/9 and198/2 per200. Pre-merge repaired normal10s successes remain historical evidence, separate from these fresh mixed results. Initial30s exploratory historical batches stay excluded from acceptance. Earlier R28 local7757 PASS/63 skips/21 failures, writable-cache/reaping observations and load-sensitive output results likewise remain retained in the audit record; this task makes no retroactive pristine full-green claim.

## C++#53 and #54 individual acceptance

**C++#53 and #54 are CLOSED as completed**, under this task's explicit criterion-based authorization. Completion comments: [#53](https://github.com/m0smith/genia-cpp/issues/53#issuecomment-6528227010), [#54](https://github.com/m0smith/genia-cpp/issues/54#issuecomment-6528228174).

| Issue / criterion | Verified result |
|---|---|
| #53 separate grouped/nested/guard RED and correction |Original ffb9b80/653a2b4 RED, then separate outstanding guard166fc5b8 RED/e70fad6 fix and Bytesa64b6789 RED/final1f338866 fix retained |
| #53 header capture and approved nested interpretation |Ordinary[0,10], nested pattern6, accepted nested-lambda-arm7, positive/false guarded[6,0]; no unsupported spelling counted as PASS |
| #53 explicit-open refusal / full final YAML |Guard/result free capture stays refused; required ungated shared header case PASS, no actual C++ failures |
| #54 A/B/C and guard-sensitive duplicates |Exact alias/duplicate stderr, exit and provenance PASS; differing guards[1,2]; alpha-renamed equal guards reject; integer/lambda/capture-key controls PASS |
| #54 prior passing R20/shared behavior |Original independent record retains293 prior passes and15 R20 IDs; fresh local/hosted final1044 classifications identical at295/749 |
| Both native / hosted / review / scope |Fresh GCC and Docker/Clang CTest7/7 each;18 direct named acceptance checks plus IR/capture assertions; full exact-pin C++ failure categories all0; original exact-source independent final reviews PASS; no capability/oracle/gap waiver |

The explicit maintainer acceptance of nested-lambda arms is in the committed preflight and issue follow-up; it is not a newly invented scope change. The old R25 baseline exception was explicitly bounded to #60, and historical failures remain retained. The fresh unresolved Python timeouts remain separate #1251/#1299 blockers; closing these two C++ defects does not dispose of them.

No default-open headers, varargs, immutable binding execution or ordinary module linking is inferred for C++. The original actual portability failures are not converted into capability gaps.

## #1251 original acceptance matrix

| Original acceptance item | Current disposition / exact remaining work |
|---|---|
| Exact merged-main commit/tree and default/strict test/host-parity evidence, honestly classified gaps |Provenance and evidence recorded. Hosted gate PASS; local gate FAIL. **Full verification acceptance incomplete** pending explicit disposition of retained local timeouts |
| Positive/negative supported semantics, modules, REPL, CLI, MCP and Core IR |Shipped partial surfaces exercised; bounded C++ guard/capture controls pass. **Full foundation scope incomplete:** ordinary linking/completion and closed publication D/E are absent; parse/lower support is not execution |
| Authority docs, semantic registry/tests, reference, examples and host docs reflect only shipped behavior |Core claims and generators agree; stale host integration prose corrected in reviewable draft#1302. **Pending its review/merge**, not silently treated as main |
| R29 intake resolved dependency or explicit maintainer-scoped exception; independent #1230 gate |**INCOMPLETE:** no approved D/E prerequisite deferral found. #1249/#1250/#1251 remain open. #1230 is separately closed after #1254 removed fallback and strict switch; no historical checkpoint/strict-mode obligation is revived |
| Migration/compatibility and bounded follow-ups with owners |Recorded below; no third-party compatibility certification or broad cleanup claim |

Migration remains breaking where documented: ordinary same-scope clauses accumulate; duplicate typed/alpha-normalized keys reject instead of replacing a group; alias/import declaration attempts fail before relevant effects; eligible differing varargs minima raise ambiguity; fixed strata do not fall back after a fixed miss. Immutable `=:` is fresh/shallow with pre-initializer rejection and commit revalidation. Closed groups parse/lower but fail before child effects with `model-b-not-implemented`. Ordinary module extension remains rejected; explicit R20 extend/use retains its separate authority. No absence of external reliance is established.

Independent audit [6504552997](https://github.com/m0smith/genia-2026/issues/1251#issuecomment-6504552997) and final remediation [6527059284](https://github.com/m0smith/genia-2026/issues/1251#issuecomment-6527059284) were read and reconciled. Their former documentation and fixture-integration blockers are addressed by merged#1300/#1301/#1270; final issue acceptance and D/E do not follow automatically. Original guard final-source independent reviews are [recorded on #60](https://github.com/m0smith/genia-cpp/pull/60#issuecomment-6498106556); repair final-review evidence is retained under `.genia/process/issue-1299-review-and-truth.md` and the final remediation report. Existing reviews establish their stated scopes; no new independent reviewer was fabricated for this task or the draft correction.

## R29 dependencies and sequence

| Remaining dependency | Owner / next bounded action |
|---|---|
| Retained local Python10s failures |Authority test-runtime/conformance maintainer; m0smith accountable. Investigate a defined resource envelope and record an explicit disposition preserving failed runs; no retry-to-green or automatic waiver |
| Slice D |Model B/module owner, m0smith accountable: ordinary completion snapshots, owner metadata projections, explicit contribution authority, atomic duplicate/shape-coherent linking, frozen views, import inertness and failure isolation |
| Slice E |Model B/runtime owner, m0smith accountable: whole-group validation and fresh immutable publication, private self identity, initializing/committed/failed states, annotation/task admission, escaped failed identities, checks before invocation/arity/matching/propagation/reflection and transport/render/consumer/REPL/TCO integration |
| Foundation/intake disposition |m0smith/release owner: reconcile #1249/#1250/#1251 and the R29 contract against completed semantics or approve a precise bounded deferral |
| Documentation correction |Documentation/host maintainer: review/merge#1302 without expanding its evidence claims |

Recommended order: resolve the retained verification failures and review#1302; complete the D contract-linked shared RED/implementation/audit gate; complete E (local E planning may overlap D, but combined negative evidence needs D); then repeat the foundation acceptance and separately decide R29 intake. No R29 implementation has started.

The roadmap already records D/E as unimplemented and #1249→#1250→#1251 as the R29 gate. Keep those blocking relationships. Closing the narrow C++ defects does not remove the broader capability gaps. #1257 runtime-owned write-through is separate; #1101 cleanup, #1236 composition, #1208 count ergonomics, R42 sessions and broad future-host parity can remain deferred within their existing scopes. R32/R33/R38/R41/R42 consumers must not assume planned completion/publication semantics. Do not invent new semantics to avoid a dependency.

**Single highest-value next action:** assign a bounded, resource-controlled investigation/disposition of the retained normal-deadline Python failures under #1251/#1299, preserving this evidence. That is the immediate verification blocker; D/E remains the next semantic-foundation work after it.

## Commands and evidence handling

The local authority checkout is `/workspace/work/1251/main`; selected C++ is `/workspace/work/1251/cpp`; correction checkout is `/workspace/work/1251/docs`. Outside Docker, commands use `UV_CACHE_DIR=/workspace/.cache/uv`, `UV_PROJECT_ENVIRONMENT=/workspace/genia-2026/.venv`, and the corresponding checkout's `src` on PYTHONPATH. Pytest always ran through `uv run --no-sync`.

```text
git fetch origin main
git rev-parse HEAD HEAD^{tree} origin/main origin/main^{tree}
git show -s --format='%H %T%n%P%n%B' 09804b56
uv run --no-sync python -m tools.spec_runner --host-jobs 8 --host '/workspace/genia-2026/.venv/bin/python -m hosts.python.protocol_adapter' --evidence /workspace/work/1251/python-evidence.json
cmake -S /workspace/work/1251/cpp -B /workspace/work/1251/cpp/build -DCMAKE_BUILD_TYPE=Release
cmake --build /workspace/work/1251/cpp/build -j 3
ctest --test-dir /workspace/work/1251/cpp/build --output-on-failure
uv run --no-sync python -m tools.spec_runner --host /workspace/work/1251/cpp/build/genia-adapter --evidence /workspace/work/1251/cpp-evidence.json
uv run --no-sync python -m tools.spec_runner.host_parity_gate --python-evidence /workspace/work/1251/python-evidence.json --cpp-evidence /workspace/work/1251/cpp-evidence.json --known-gaps spec/known_host_gaps.json
uv run --no-sync python /workspace/work/1251/stress.py /workspace/work/1251/cpp/build/genia-adapter 1000
uv run --no-sync python /workspace/work/1251/stress.py /workspace/genia-2026/.venv/bin/python 200
uv run --no-sync python tools/gen_mcp_language_profile.py --check
uv run --no-sync python tools/gen_function_docs.py --check
uv run --no-sync python tools/lint_doc.py --scan-dir src/genia/std/prelude --require-coverage
uv run --no-sync python tools/stage_docs_for_mkdocs.py
uv run --no-sync mkdocs build
uv run --no-sync mkdocs build --strict
```

The stress driver reuses canonical `load_spec`, `execute_spec_via_host`, request builder/comparator and default10s protocol timeout; it executes a predeclared batch once, records every outcome, then checks exact postfailure rejection. No new conformance protocol or capability mechanism was created.

Initial environment setup failures are separate from executed tests: an unwritable default uv cache, cmake missing from shell PATH, buildx trying to write under the read-only home, and an initial Docker `uv sync --locked` with no tracked lockfile. Correcting cache/PATH/buildx state and using the workflow's `uv sync --dev --python python` preceded those checks; the Docker setup-failure log and task command transcript retain those observations. No failed semantic assertion or stress request was retried. The Docker build used the repository's pinned base/tool versions with a scratch BuildKit CA-secret/PIP_CERT adaptation, TLS verification enabled; source Dockerfile and product code were untouched.

Evidence files, the exact regression command selections, outcome ledgers, support driver and log digests are retained in the dedicated #1302 branch under `.genia/process/issue-1251-post-merge-evidence/`. This is reviewable evidence, not merged-main content. Historical producer logs remain linked by their immutable workflow runs above.
