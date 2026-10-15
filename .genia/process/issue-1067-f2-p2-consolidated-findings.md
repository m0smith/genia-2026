# F2/P2 consolidated maintainability and truth review

Date: 2026-10-15. Parent #1067; execution #1229; debt #1238; retirement #1230.
Phase: audit/evidence only. **Recommendation: NO-GO for integration.** No production
code, tests, semantics, or approved contract were changed by this review.

Three corrections block integration (R01, R15, R16). R10 requires an explicit
maintainer interpretation before merge; a conservative result is not proof of
contract compliance. Existing green tests do not settle these findings.

**Correction status:** see the final section, "Correction status" (appended after this NO-GO review; the sections above are the historical review and are not rewritten).

## Baseline and authority

Reviewed GitHub heads fetched on the review date:

| PR / slice | Head | Base |
|---|---|---|
| #1235 / B | `24cbe008d2c5cdde644f0e719fb048341a7e85e2` | main |
| #1239 / C | `cb593207a635fe46ffa26cc10387aee6b2cac442` | B |
| #1240 / D | `b674674de946b632b18cc12145f6310e33a83256` | C |
| #1241 / E | `7d696abf80125278e7c764c5be20537731e30d31` | D |
| #1242 / F | `91d454cd8f4bbf35847f7b38c1f61c1d55b39e9a` | E |
| #1243 / G | `99787634e6eef6f8b6346f96ade93bec0dc2fb33` | F |

All five adjacent `git merge-base --is-ancestor` checks exited 0. Review branch
starts at G, in an isolated worktree. The C branch is actually named
`claude/tender-dijkstra-vk788s`. No stack branch was rewritten or merged.

Authority consulted: AGENTS, STATE (especially reflection, metacircular evaluation,
and section 9), RULES, REPL README, README, run-change, LLM_CONTRACT, F2 contract
§§7, 11, 16 and A1–A3, decisions/approval records. Approval is
[D1–D6 with A1–A3](https://github.com/m0smith/genia-2026/issues/1067#issuecomment-6171848719).
The maintainability gate file is absent from G; its current `origin/main` version
was read with `git show origin/main:docs/process/code-maintainability-review.md`
(introduced by `e44f7e0`). This is a divergent-base fact, not permission to omit review.

Sources collected: committed C/D/E/F/G maintainability records and evidence records
in this directory; all six PR bodies, commit lists, comments/reviews (PR comments
and submitted reviews were empty when read); #1238 body and both comments;
#1067/#1229/#1230 bodies/comments and #1220/#1221 bodies (no comments returned).
Truth-audit findings below are those preserved in evidence/PR bodies. Original
independent reviewer transcripts are not committed there; do not mistake an
author's audit summary for an independently replayable transcript.

Scope classification: infrastructure/follow-up supporting reliable validated data
pipelines; no new release feature. MCP language-knowledge impact: none for this
evidence-only report. Any eventual reflection correction needs its own impact review.

## Disposition register

`C.N1` means finding N1 in the committed P2-C maintainability review; similarly
D/E numbers. `TA` identifies the truth-audit summaries in the corresponding evidence
record. Original severity is shown first; the disposition is this review's verdict.
Owner entries name accountable or recommended owners, **not GitHub assignments**:
#1238 and the related issues currently have no assignees. M = @m0smith, accountable
maintainer pending an explicit implementer assignment. Gates are proposed next phases.

| Finding | Severity | Disposition | Evidence | Owner | Required action | Gate |
|---|---|---|---|---|---|---|
| R01 C.N1; F §6; G N1: failed declarations enter inspection | originally non-blocking; blocking | BLOCKING | `environment.py:307–333` `_entry_route`/`binding_scope`, `binding_owner:211`, `inspection_bindings:229`; G failed-declaration test passes by asserting the defect | M; #1238 N1 | Record successful declarations only; correct pin and implemented-truth wording | P2 correction, before integration |
| R02 C.N2: repeated ownership checks | non-blocking | ACCEPTED DEBT | `is_runtime_owned` and `_runtime_name_available` repeat bound/internal/autoload checks | M; #1238 N2 | Consolidate only if clarity or measurement justifies it; retain pruning semantics | P3 preparation or measured performance follow-up |
| R03 C.N2: repeated autoload scans/set construction | non-blocking | ACCEPTED DEBT | Same helpers; `any(...)` and `set(runtime.autoloads.values())` remain | M; #1238 N2 | Measure relevant entry operations before adding invalidation/cache complexity | Performance follow-up; no demonstrated P2 regression |
| R04 C.N2: cold manifest parsing | non-blocking | ACCEPTED DEBT | `_declared_prelude_names` caches parsed names by path; first manifest request parses targets; manifest unions are rebuilt | M; #1238 N2 | Measure startup separately; fib timing does not measure cold parsing | Performance follow-up; bounded packaged input, no correctness defect shown |
| R05 C.N3: early inspection accessor change | non-blocking | FIXED | D consumer migrations; B boundary/host and D consumer tests pass on G | M; #1238 N3, #1221 | Mark delivered subitem during issue reconciliation; R01 remains separate | Integration evidence review |
| R06 C.N4 immutable defaults | informational | FIXED (verified invariant) | Defaults are None/False/frozenset; topology tests exercise distinct frames | M; #1229 | None | None |
| R07 C.N5 MCP fixture call style | non-blocking | FIXED | `tests/fixtures/r28_mcp_conformance.py` comment pins `genia.make_program_env` instrumentation seam | M; #1229 | None | None |
| R08 C.N6 helper Raises docs | non-blocking | FIXED | `builtins.py` `make_program_env` documents preparation failures and entry-only rejection | M; #1229 | None | None |
| R09 D.1 + D earlier module-main regression | non-blocking | FIXED | Non-re-resolving `Env.binding_owner`; native discovery and `_resolve_program_result` use selected owner; wrong-accessor cases pass | M; #1221 | None beyond R01's record accuracy | Integration evidence review |
| R10 D.TA; F §6/Meta pin: metacircular reflection raw R-bound | non-blocking originally | NEEDS DECISION | `GeniaMetaEnv.lookup:555` returns raw Env.get; §16.2 evaluating-frame rule has no explicit meta exception; §16.4 specifies R-based base, not reflection | M; #1238 comment 6175183418 | Explicitly rule on meta-frame reflection; preserve no-fallback and capability boundaries; see below | Decision before merge; correction phases if required |
| R11 D.2 marker check hot path | non-blocking | ACCEPTED DEBT | `_resolve_identifier:1199` type/attribute checks remain; reported fib ranges overlap (C 349–380 ms, D 349–368 ms), not independently benchmarked here | M; #1238 | No frozenset rewrite without measured benefit | Performance follow-up; no measured regression established |
| R12 D.3 cache/closure cycles | non-blocking | ACCEPTED DEBT (documented, not removed) | `Env.scope_bound:149` caches per target; closure captures Env; cycle-GC dependency documented | M; #1238 comment | Preserve stable same-scope identity; measure retention if a real workload warrants changes | Runtime-memory follow-up; no global frame cache or unbounded per-frame target growth shown |
| R13 D.4 magic attribute | non-blocking | FIXED | `Env.SCOPE_BINDER_ATTR` used by builtins and evaluator | M; #1229 | None | None |
| R14 D.5/6/7 and D.t1/t2 | informational / non-blocking | FIXED / verified limitation | Value marking uses actual FunctionType; no E/P3 code smuggled into D; baseline reductions accompany docs; serve negative asserts Undefined name; eval lambda/list replacement limitation predates P2 | M; #1229 | Preserve existing tests; do not call the reduced eval case higher-order coverage | None |
| R15 E.3: unlocked warning check/add | non-blocking originally; blocking | BLOCKING | `module_fallback.py:49–53`; real Process workers produce 2 warnings / 1 pair under forced legal schedule | M; recommend #1230 correction checklist linked from #1238/#1229 | Serialize first-pair claim, keep IO outside critical section; concurrency regression | P2 correction before merge |
| R16 E.4: uninitialized event set | non-blocking originally; blocking | BLOCKING | Env default None; public `create_entry_scope` does not initialize it; eligible registered-root read returns value without event/warning | M; recommend #1230 correction checklist linked from #1229 | Initialize consistent execution state or explicitly reject unsupported registration; no silent evidence bypass | P2 correction before merge |
| R17 E.1 warning-stream errors | non-blocking | FIXED | `_warn` guards both process stderr and runtime sink with BrokenPipeError/OSError; failing-stream test passes | M; #1230 | None; arbitrary host exceptions are outside the verified error classes | None |
| R18 E.2 replaceable runtime stderr | non-blocking | ACCEPTED DEBT / intentional P2 compatibility | `_warn` reads R stderr; successful entry declaration of runtime-owned stderr writes through under A1 | M; #1230 and A1 | Keep sink ownership explicit; revisit only with approved write-through retirement | P3; does not add protected-value authority or a new bypass |
| R19 E.5 allegedly vacuous exclusion tests | non-blocking | FIXED (evidence concern resolved) | Positive fallback cases plus B4 seven exclusions; real registered R/E/M fixtures and wrong-owner checks pass | M; #1221 | None | None |
| R20 E.6 marker/tracking literals; E.CI | non-blocking / informational | FIXED | G AST guard confirms one caller and one STATE marker; #1230 intentional literal; ci.yml strict env is step-local | M; #1230 | Retire together through §11.4/A2 | P3/R29 planning gate |
| R21 C.TA F-1 interim claims / F-4 three specs + parity reds | audit findings | FIXED at combined G | Interim C/D failures honestly retained; reflection implementation and shared specs now present; focused checks green | M; #1229 | Do not merge red B/C/D snapshots as a releasable stopping point | Whole-stack integration |
| R22 C.TA F-2 debt trace / F-3 early sink migration | audit findings | FIXED / recorded deviation | #1238 exists; runtime sink migration visible in C; boundary sink tests pass | M; #1238/#1221 | No further correction for early migration | None |
| R23 D.TA debugger redaction | audit caveat | FIXED (bounded proof) | Protected entry globals/diagnostics B10 case passes; debugger uses protected repr, no new declassification | M; #1221 | Preserve sentinel tests; not a universal security proof | Integration review |
| R24 E.TA suite-wide claims not independently run | evidence limitation | INSUFFICIENT EVIDENCE for original audit execution; focused recheck green | E records implementer default/strict full runs, auditor limitations; present review did not rerun full suite | M; #1229 | Required CI/full regression remains merge gate; never relabel inspected logs as reviewer-run | Merge checks |
| R25 F stale remote E head | record defect | FIXED | GitHub #1241 now 7d696abf, ancestry verified; contains hardening commits | M; #1229 | None | None |
| R26 F ignored review artifacts | record defect | FIXED for availability | C/D/E/F/G records committed at durable paths; original tmp references in D/E PR bodies remain stale | M; #1229 | Prefer durable links; report gives authoritative replacements | Non-blocking metadata cleanup |
| R27 F.TA §9(1) independent-verification label | audit finding | FIXED with limits | F §4 cites D/F independent summaries; this review separately inspects code/tests | M; #1220 | Closure contingent on remaining findings; not blanket proof | Integration review |
| R28 F.TA §9(2) measurement/mutation reproducibility | audit finding | FIXED for recipe availability | Probe committed; F §3b lists exact eight mutations; not rerun here | M; #1230/#1221 | Rerun measurement on merged tree before retirement | P3 retirement; author-run mutation counts remain attributed |
| R29 F.TA §9(3) STATE headroom | audit finding | FIXED | G condenses STATE; documentation size guard in tests/doc passes | M; #1229 | None | None |
| R30 F.TA §9(4) MCP end-state vs ordering proof | audit finding | FIXED (proper separate proof) | Integration assertion checks denial; B7 constructor instrumentation checks prune before entry; focused B hosts pass | M; #1221 | Preserve both proof roles | Integration review |
| R31 G final README/REPL edits | audit/doc concern | FIXED (validation passes) | tests/doc, style/cheatsheets, staged strict MkDocs build pass on exact G; final commit 9978763 included | M; #1229 | R01 wording must change with correction; build success does not approve semantics | Correction docs + merge CI |
| R32 #1233 lifecycle evidence | process concern | INSUFFICIENT EVIDENCE for historical ordering | C/D/E review summaries describe pre-doc ranges and follow-up fixes; records first committed in F, after C/D/E docs; no original timestamped transcripts | M; #1229 | Record limitation; current independent review covers actual G code; do not claim historical durable handoff order proven | Current review before integration; no invented retroactive PASS |
| R33 fallback retirement | continuing obligation | ACCEPTED DEBT | #1230 owner M, A2 hard R29 gate, 60-day review checkpoint; no first-main date yet; F limits executed-body coverage honestly | M; #1230 | Record actual first-main UTC date/checkpoint on landing; rerun measurement and A1 counts, preserve third-party uncertainty | P3 removal / R29 start |
| R34 NEW: Meta pin is nondiscriminatory | test-quality defect | INSUFFICIENT EVIDENCE | F integration last assertion doc(added) where added=1 returns missing-doc even with correct scope | M; #1238, R10 | Use metadata or documented callable positive control, then match approved interpretation | R10 resolution before merge |
| R35 NEW: contradictory contract status preamble | low doc defect | ACCEPTED DEBT | F2 header says no behavior implemented and P2-0 says nothing in §16 implemented, immediately beside G implemented-status note | M; #1229 | Label historical text explicitly or reconcile during correction docs | P2 docs follow-up; explicit G note and STATE disambiguate actual implementation |
| R36 NEW: F no-phantom rationale overstates resolution | low evidence defect | FIXED by superseding analysis here; old record retained | F §6 filters name in R.values, which prevents nonexistent names but exposes pre-existing R bindings after failed declaration; G correctly admits this | M; #1238 | Cite R01 rather than F's 'no correction needed' conclusion | R01 correction audit |

Documentation is not a correction: R01, R12, R15 and R16 all have explanatory
comments, but their runtime behaviors persist. R12 is acceptable debt because no
retention regression is demonstrated and identity caching is required. R15/R16
violate an explicit observation guarantee and cannot be accepted on that basis.
No performance measurement in this review establishes a slowdown. The reported
fib measurement speaks only to its workload and does not settle startup/entry routing.

## Priority investigation and reproduction

### R01 — failed declaration visibility

The existing G test
`tests/unit/test_f2_p2_g_closeout.py::test_failed_declaration_of_existing_runtime_name_is_recorded_as_an_attempt`
runs both `first(x) = x` after list autoload and `open log(x) = x`. The declarations
raise, yet `entry.inspection_bindings()` includes the existing runtime value.
`binding_owner` trusts the same record for host consumers. No newly granted
declassification authority is demonstrated; the defect is false attribution and
potential consumer selection, not a proved secret leak.

Approved §16.1.4 says consumers observe runtime-owned names the entry declared
and **no other R binding**. STATE now truthfully admits the attempt behavior, but
the admission is not an approved amendment to the visibility requirement. F's
filter prevents a nonexistent binding; it does not prevent exposing an old one.

Recording after success preserves successful write-through and existing collision
errors. It changes inspection after a failed declaration (and the pinned G test),
so it is a bounded compatibility correction, not strictly behavior-neutral.
Do not simply move the line within the router: ordinary definitions, assignment,
and open declarations have different success points; nested RHS declarations must
not be erased by a naive whole-set rollback. Audit all callers listed below.

### R10 / R34 — metacircular reflection

Observed on G using `import genia` (not importing run_source into __main__):

```text
eval(quote(local), define(empty_env(), quote(local), 42)) => 42
eval(quote(meta("local")), define(empty_env(), quote(local), 42))
  => none("missing-meta", {name: "local"})
```

`GeniaMetaEnv.lookup` returns raw runtime reflective values via host Env.get.
The ordinary evaluator scope-binds them, but the meta evaluator does not. The
R-based base and no-fallback rule are correct; the test also proves entry docs
are absent. Neither fact settles whether explicit meta-frame bindings should be
reflected. No prohibited binding access was found. Already-bound reflective values
explicitly supplied through define should retain their captured scope under the
ordinary callable rule; distinguish those from raw runtime values.

§16.2's broad evaluation-bound rule and STATE's reflection statement conflict with
the claimed general R-only exception; §16.4 establishes only the environment base.
Request an explicit ruling: either scope-bind raw reflection to the meta frame
without enabling fallback, or approve and document the separate meta lookup model.
Do not silently expand eval or declare the limitation accepted merely because it
does not leak E. A `meta` positive control distinguishes missing name from an
existing binding with an empty metadata map; `doc` of integer 1 cannot do so.

### R15 — supported concurrency, not hypothetical parallel imports

`GeniaProcess._run` invokes handlers on host threads; module functions retain M
closures sharing R. Two preloaded module workers can race without concurrent
imports or autoloads. Independent reviewer ran this exact probe (production and
event-set type unchanged; strict mode off). Invoke the snippet with
`env -u GENIA_STRICT_MODULE_SCOPE` and the verification environment below:

```python
import threading, tempfile, genia
from pathlib import Path
from genia.module_fallback import temporary_compatibility_fallback_read

barrier = threading.Barrier(2)
filename = temporary_compatibility_fallback_read.__code__.co_filename
hits = []
def trace(frame, event, arg):
    if event == "line" and frame.f_code.co_filename == filename and frame.f_lineno == 51:
        hits.append(threading.get_ident())
        barrier.wait(timeout=5)
    return trace

threading.settrace(trace)
with tempfile.TemporaryDirectory() as directory:
    (Path(directory) / "race.genia").write_text("worker(msg) = entry_secret\n")
    entry = genia.make_program_env([])
    genia.run_source("entry_secret = 42\nimport race\np = spawn(race.worker)\nq = spawn(race.worker)",
                     entry, filename=str(Path(directory) / "entry.genia"))
    genia.run_source("send(p, 1)\nsend(q, 2)", entry)
    entry.get("p")._r25_wait_idle()
    entry.get("q")._r25_wait_idle()
    print("barrier_hits", len(hits), "events", len(entry.runtime_scope().fallback_events),
          "failed", entry.get("p").failed(), entry.get("q").failed())
threading.settrace(None)
```

Result: two identical warnings, `barrier_hits 2 events 1 failed False False`.
The trace barrier only forces scheduling after both membership checks; it proves
an allowed interleaving, not a natural frequency or set corruption. Distinct-pair
accounting remains correct in this probe; warning accounting does not. Contract
§11.3 and STATE section 9 require one warning per pair. A per-runtime protected
check/add is proportionate; perform warning IO after releasing the guard.

### R16 — registered caller-created runtime

Executed unchanged production evaluator:

```python
import genia
from genia.environment import Env
r = Env()
e = r.create_entry_scope()
e.set("shared", 42)
m = Env(r)
m._unit_scope = m
m.module_id = "manual"
print(genia.run_source("shared", m), r.fallback_events)
```

Result: `42 None`, no warning. M's ownership initialization mirrors the module
loader; no replacement fallback implementation is used. `Env` is an internal host
class, but its constructor and registration are the expressly described host API
in §16.6.1; no factory-only precondition is specified. This is distinct from the
supported legacy **unregistered** single-root case (which has no fallback).

All 13 program factories initialize events and capture strict mode through
make_global_env, so their evidence does not cover this registration path. Either
registration must establish coherent event/strict state or reject an unsupported
runtime explicitly under an approved boundary. Silently granting a fallback read
without evidence conflicts with §16.3.2. Do not accept None as an empty event set.

## Verification actually executed

Shared environment used: existing locked repository venv, with
`UV_PROJECT_ENVIRONMENT=/Users/m0smith/projects/genia-2026/.venv`,
`UV_CACHE_DIR=/tmp/uv-cache`, `uv run --no-sync`, and explicit
`PYTHONPATH=/tmp/genia-p2-consolidated/src:/tmp/genia-p2-consolidated`.

| Run | Observed result |
|---|---|
| B boundaries/hosts, C topology, D consumers, E fallback, F integration/repository programs, G closeout, tests/doc, doc style, core/unix cheatsheets | 583 passed, 35 skipped |
| B behavior + all `tests/unit/test_cheatsheet_*.py` | 149 passed |
| Strict B boundaries/hosts, E, F integration/repository programs, G | 116 passed |
| Generated function reference `--check`; MCP language profile `--check` | exit 0 |
| `tools/stage_docs_for_mkdocs.py`, then `mkdocs build --strict --site-dir /tmp/genia-p2-review-site` | exit 0, build completed |
| Parent's manual-root and meta lookup probes above | results reproduced |
| Independent reviewer: G + Meta pin | 4 passed |
| Independent reviewer: supported-worker concurrency probe | duplicate warnings reproduced |

First test attempt lacked explicit PYTHONPATH: 523 passed, 35 skipped, **5 failed**.
Subprocesses loaded main-checkout Genia through the shared editable environment
(tracebacks named `/Users/m0smith/projects/genia-2026/src`). The corrected run
selected G for parent and subprocesses and passed. This was a review harness error,
not a production fix. One exploratory script also imported format_debug from the
wrong module; another imported run_source into __main__, tripping the existing
runtime-discovery heuristic. Corrected probes use `import genia`; neither failed
probe is behavioral evidence for P2.

Not rerun here: whole regression, loopback partition, full shared-spec runner,
C++ parity, official MCP client, VS Code tests, prior mutation experiments or
suite-wide fallback measurement. G records 6945 default/strict non-loopback passes,
31 loopback, 825 specs and successful bounded host parity; those remain attributed
historical evidence. Focused green tests include pins of known limitations and do
not prove contract compliance. No tests were added or weakened for this review.

## Review completeness and process

All enumerated C/D/E maintainability rows, F/G determinations and preserved
truth-audit findings are mapped above. F/G N/A determinations are reasonable for
production-code review because their production diff is empty, but their test and
claim quality still require scrutiny (R34/R36). C/D/E fixes were inspected in code;
explanatory comments were not counted as removing runtime behavior.

#1233 was closed before C implementation. Commit chronology supports code then
fix then docs, but C/D/E reviewer records were published only in F, and G's
maintainability determination followed its first docs/test commit. Exact historical
review/handoff timing therefore is not independently proven. The current separate
review supplies substantive pre-integration inspection, not proof of past ordering.
No new process policy or fabricated transcript is proposed.

The old D/E PR bodies still link ignored tmp paths; durable replacements are their
same-slice `*-maintainability-review.md` files here. Fallback retirement remains
tracked and owned in #1230. Its initial body still says pending/not implemented,
but subsequent comments explicitly record approval and implementation. Recommend
reconciling issue bodies/checklists rather than opening duplicate debt tickets.

## Separate skeptical reviewer

Read-only agent `/root/skeptical_review` independently inspected contract,
maintainability/evidence records, actual Env/evaluator/fallback/concurrency code,
and focused tests. It did not receive a drafted disposition matrix to endorse.
Its final verdict: **blocking findings remain** (R01, R15, R16), R10 needs an
explicit interpretation, and the Meta assertion is nondiscriminatory (R34).
It executed the concurrency probe and four existing tests and edited no tracked
files. Parent independently reproduced manual-root and Meta behavior and ran the
broader focused/documentation selection.

The reviewer also read this completed report and found no material correction;
its requested strict-mode invocation clarification is included in R15.
No final disagreement between the two current reviewers. Both disagree with the
earlier non-blocking classifications of R01/R15/R16 and the claim that absence of
an E leak alone justifies the Meta exception. These disagreements are explicit;
the earlier records remain historical, not silently rewritten.

## Narrow Claude handoffs (prepare only; do not execute in this review)

### R01 — successful-declaration record (#1238 N1)

Scope: `Env._entry_route`, `set`, `assign`, `define_function`, and evaluator
`IrOpenFuncDef` success points; inspection consumers only as necessary. Preserve
collision diagnostics, write-through, autoload and pruning behavior. Commit a
focused failing regression first: after each failed first/log declaration the
name is absent from E's declared record/view/owner, with successful declaration
and existing-record controls. Include assignment failure and annotated/open paths.
Then implement success-only recording, referencing the red SHA. Avoid naive global
rollback that erases nested successful operations. Flip G's known-defect pin and
update STATE/REPL wording and affected documentation. Run B/C/D/G and discovery/
debugger/REPL regressions; obtain independent re-review. No P3 shadowing.

### R15 — atomic warning claim (#1230 correction, cross-link #1238/#1229)

Scope: per-runtime fallback synchronization and helper only. First commit a
deterministic supported-Process regression with two same-pair reads; also verify
distinct pairs, execution isolation and failing warning stream behavior. Add the
smallest coherent guard around membership/add; warning IO stays outside the lock.
Preserve value-free warnings and exact strict behavior. No scheduler/import-lock
redesign. Update the now-false concurrency limitation docstring and affected STATE
truth only after verification. Run B4/E fallback and concurrency suites; review
deadlock/reentrancy and warn-once evidence before merge.

### R16 — registration measurement invariant (#1230 correction)

Scope: host runtime construction/registration and fallback precondition. Explicitly
settle factory-independent registration support under §16.6.1; do not silently
declare a documented host operation unsupported. First commit failing host tests
for a caller-created root registered as E, eligible module read, event/warning,
strict capture policy, and two-runtime isolation. Initialize consistent state at
the chosen execution boundary or explicitly reject unsupported construction under
an approved contract clarification. Preserve legacy unregistered roots and
pre-registration host preparation/MCP pruning. Reference red SHA, update truthful
docs, run B/C/E plus construction guards and MCP tests, independent re-review.

### R10/R34 — decision handoff (#1238)

Seek an explicit interpretation of §16.2 versus §16.4 for raw reflection obtained
inside meta evaluation. Supply the `meta(local)` repro and a documented-callable
positive control; distinguish host direct lookup and explicitly transferred bound
callables. If reflection must bind to the meta frame, return to failing-test then
minimal implementation phases and add shared evidence where expressible. If an
exception is approved, document its precise boundary and pin it discriminately.
No fallback inside eval, no ambient E access, no new eval syntax. This review
authorizes neither choice.

## Optional #1226 post-task review

Meaningful support work was Python-host inspection/reproduction, pytest execution,
GitHub metadata retrieval and a host-thread trace/barrier. **D** for the trace and
host-internal probes: their purpose is to inspect Python Env/thread implementation;
implemented Genia source has no equivalent Python tracing API. No A/B/C candidate
was established. The Markdown register was authored directly, not generated by a
substantive data transformation; **None** for a replacement reporting script.
No Genia productivity comparison or executable-equivalence claim, no new feature
ticket, and no release gate was manufactured. No messages posted to #1226.

## Final gate

**NO-GO.** Correct R01/R15/R16, resolve R10/R34 explicitly, and independently
re-review the focused corrections before integration. Keep #1067/#1229 open;
#1220/#1221 are substantially evidenced but closure should follow corrected-stack
review/landing. #1238 remains the existing debt record; add precise correction
checklists/cross-links for the fallback findings to #1230 rather than duplicating
tickets. Deferred performance/cache work has no demonstrated correctness or
performance regression requiring P2 expansion. This review stops at evidence and
handoffs; no fixes or merges were performed.

## Correction status (stacked correction PR on #1244)

Appended after the corrections; the verdict above is historical. Branch `claude/amazing-ritchie-8mqq4k`
(stacked on #1244 head `dcb749d`). Red commits precede fixes; nothing here is a maintainer sign-off.

| Item | Red tests (failing first) | Fix | Corrected-behavior tests |
|---|---|---|---|
| R01 | `acf1a97` (R01 cases failed) | `faca7ad`: record after success in `Env.set`/`assign`/`define_function`; `_entry_route` is pure routing | `tests/unit/test_f2_p2_corrections.py::test_r01_*`; flipped G pin `test_f2_p2_g_closeout.py::test_failed_declaration_of_existing_runtime_name_is_not_recorded` |
| R15 | `acf1a97` (barrier-forced two-warning reproduction with real Process workers failed) | `faca7ad`: `Env.claim_fallback_event` (per-runtime lock, IO after release) | `test_r15_*` |
| R16 | `acf1a97` (manual R/E/M repro returned `42` with `None` events) | `faca7ad`: `create_entry_scope()` calls `init_fallback_state`; fail-closed when state missing | `test_r16_*` |
| R10 / R34 | `77034c3` (5 failed on unmodified lookup) | `62a9916`: `GeniaMetaEnv.lookup` scope-binds raw reflection (Option A, maintainer ruling PR #1244 comment 6197128489) | `tests/unit/test_f2_p2_meta_reflection.py` (documented/docstring callable, `meta` present-vs-missing, `help`, already-bound `d`, no leak, E invisible, module no-fallback, user rebinding) |

R34 note: the first red set asserted `@doc` binding metadata through `define`, which `define` has never carried; the
corrected set uses a docstring function and the present-empty-map vs `missing-meta` control (commit `77034c3`). No
semantics changed to make that pass. Maintainability review (independent, #1233): PASS WITH NON-BLOCKING FINDINGS
(shared strict reader and `init_fallback_state` re-entry guard adopted; historical records intentionally unrewritten).
