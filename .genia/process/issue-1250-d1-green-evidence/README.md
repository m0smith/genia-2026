# #1250 D1 implementation — acceptance BLOCKED

Candidate: c38b4dffafdc50a8ba7f369c8e477eddc8ca1199 (tree
9ea50abfb140fc5265dbf9280eb2a00fa031df89), based on mainca0b72e1.
Accepted RED98697c20 remains in history; documented RED90c41e56 tests/YAMLs
are byte-identical through GREEN. No original oracle altered.

## Scope and eight-row evidence

| Acceptance | Implemented and exercised boundary |
|---|---|
| D1-01 | Capture once under writer lock before complete ModuleValue/cache publication; cache hits synchronize and reuse original association. Existing deterministic cache observers retained. |
| D1-02 | Detached syntax, shape/key/declaration/arm/span provenance, fresh materializations; shared closure/Ref/Cell/runtime literal identity. Covers grouped and optimized retained cases and host-only body. |
| D1-03 | Owned immutable binding-map, independent projected doc and G-owned help channels. Inline fallback only from original G; missing doc remains absent. No renderer/autoload execution. |
| D1-04 | Exact-G aliases deduplicate; re-export reuses original witness. Equal owner text, failed/never-exported origins and escaped old identities cannot mint witnesses or block ordinary export. |
| D1-05 | Accepted B1 replacement/annotation/import-reset/restore/alias-help cases retain their original expectations. No replacement-inline substitution or metadata resurrection. |
| D1-06 | Real faults at binding-map/help-map/copy/projection construction plus existing ModuleValue/final-cache faults; no completed entry, sentinel/lock cleanup, preserved effects/dependency caches, fresh retry identity. |
| D1-07 | Shared preservation for metadata/cache/re-export/ordinary-extension rejection; existing module, Slice C and explicit R20 regressions. Cycles/live aliases/reflection/module isolation retain behavior. |
| D1-08 | Original committed RED retained, supplemental failed tests and interrupted runs preserved below; no capability/adapter/IR changes. Maintained-code docs and independent reviews; full gates recorded separately. |

Production changes are restricted to ordinary_completion.py, Env.load_module and
private ModuleValue field. No public snapshot API or D2 ordinary linking, E closed
publication, new capability or Core IR version. C++ implementation is unchanged.

## Failed and incomplete observations retained

| Observation | Provenance | Result/disposition |
|---|---|---|
| Accepted original RED |98697c20 |19expectedFAIL/9PASS; immutable original archive retained unchanged. |
| Literal identity boundary |70dec5b3 source + supplemental test working tree |1FAIL; source retained in history; fixedad9ef661. Runtime literal list identity must remain shared. |
| Opaque kind classification |d97eb7b8 |3FAIL; fixed6f47c0e5 after independent maintainability finding. |
| Opaque key probe / committed regression |c893a090 probe /684ee436 |RuntimeError reproduced /1FAIL; fixed044269c9 after independent semantic finding. |
| Preliminary full regression |c893a090 |867PASS/35skip then explicit interrupt (exit2) for known opaque-key finding. Incomplete; never acceptance. |
| Existing scope guard / incomplete full |044269c9 |Hosted fast check1FAIL/1824PASS/35skip; local1FAIL/3335PASS/35skip then explicit interrupt (exit2). Fixedc38b4dff .runtime_scope(); existing guard unchanged. |
| Required full non-loopback partition |c38b4dff |**22FAIL/7125PASS/62skip/856.49s, exit2**; maxfail20 stopped xdist after22. All22 remain FAIL. Required STOP/report; local full partition union incomplete. |

No failed result replaced or relabelled. No deadlines/oracles/capability gates
weakened. Source changed to resolve each defect before new acceptance. The seven
historical Python10s TIMEOUTs retain their original provenance and unresolved
causation; finite GREEN cannot explain them or prove determinism. Accepted A/B/C,
#1299/#1302/#1304 evidence reused at original pins; no Slice C audit repeated.

## Independent reviews

Maintainability: Codex /root/acceptance_review, read-only independent agent.
Actual diff, loader/writer/callable/map/IR callers and tests inspected for readability,
cohesion, complexity, ownership, synchronization, cleanup, testability and scope.
REVISEad9ef661 for arbitrary kind hashing under lock; fixed/reviewed6f47c0e5.
Further key guardPASS044269c9. Final explicit runtime accessorPASSc38b4dff.
No outstanding blocking or untracked findings; reviewer ran no tests/edits.

Semantic/documentation truth: Codex /root/docs_review, independent read-only agent.
Inspected B1 channels, detached syntax/runtime identity, exact-G witnesses,
coherent publication/failure/cache cleanup and public preservation. Key equality
hook finding atc893a090 reproduced and retained; fixed/reviewed044269c9. Corrected
stale future design wording; final accessor change reviewed semantically neutral.
**PASS atc38b4dff**. No tests or edits by reviewer; no unresolved audit finding.

Neither review substitutes for execution gates or maintainer merge approval.

## Documentation truth and distillation

STATE/RULES/REPL README/README plus relevant contract/design/book/host/IR reference
surfaces describe private Python completion only. STATE42999words within43000budget.
No D2/E/C++ parity claim. AGENTS remains accurate unchanged; no workflow changed.
MCP registry/profile and generated function references need no new public fact;
checks verify they remain current. No capability, semantic fact registry or adapter
changes; existing host gaps still owned. Private capture does not discharge future
D2 shared observable linking/metadata or E lifecycle obligations.

Final design status and structure are durable documentation; phase logs stay in
.genia/process. Distillation reuses reviewed compact wording, adds no duplicate
semantic prose and removes no failed evidence. Temporary handoffs may be deleted
only after this durable record is committed. Usage/review time/savings not measured.

## Validation receipt

**GREEN acceptance is BLOCKED.** Focused D1/scope checks:82PASS/2.78s atc38b4dff.
Previous focused D1+nearest regression:121PASS/2.23s at044269c9 (not exact-head
execution; only subsequent change is reviewed runtime accessor replacement).

Required local full non-loopback:22FAIL/7125PASS/62skip/856.49s, exit2. Maxfail20
with two workers stopped after22. Observed failures include default uv cache
/home/agent/.cache/uv read-only, missing worktree uv.lock, socket creation EPERM,
and multiple MCP sessions closing stdout before expected response. These traces
**do not establish causation for every failure**. No failure is reclassified.
No implementation regression was established by this inspection; absence of a
proven implementation regression is not acceptance.

Process docs/process/03-implementation.md§3 requires: “If more than 20 tests fail
→ STOP and report instead of continuing.” No subsequent tests or source changes
were performed. Local full loopback partition and remaining local checks were
not run after this mandatory stop. Hosted non-slow loopback is separate evidence.

All six workflows PASS for source candidatec38b4dff on merge checkout0a8fc887,
whose tree was checked equal to candidate9ea50abf. CI non-slow non-loopback:
7590PASS/63skip/418.93s; non-slow loopback31PASS/10.54s; in-process semantic specs
1048PASS/0FAIL/0invalid. Docs strict build/reference/style, maintained-code docs,
LLM instructions, Docker, official MCP client and extension jobs PASS. Exact run
links and counts are in external.json; producer logs and artifact ZIP are retained.

Hosted full external protocol, unchanged10s deadline: Python1030PASS/18UNSUPPORTED;
C++295PASS/753UNSUPPORTED; both zero actual failure/protocol-error/crash/timeout/
invalid. Four new shared preservation cases pass Python, unsupported C++. Selected
C++ source1f338866 declares older authority6402e668 (resolvable ancestor); this is
compatibility evidence, not full current-contract support. Existing host gaps stay.

Independent final disposition review /root/acceptance_review confirmed BLOCKED /
STOP from the actual log and process rule. Observed setup failures do not explain
all22; six passing hosted workflows do not complete the local full-partition union.
Prior maintainability PASS remains scoped. No further tests or edits by reviewer.

Raw archive/provenance/manifest accompany this record. Any subsequent process-only
evidence commit does not claim tests executed at that SHA; source/test/spec/docs
object identities establish bounded reuse. Final-head CI may rerun after evidence
publication; this record makes no final-head acceptance/merge-readiness claim.
PR stays draft, #1250/#1251 open; no merge, E or R29. Next: restore the required
local test environment, diagnose all22 failures, then resume outstanding full gates
without weakening tests or erasing failed evidence.
