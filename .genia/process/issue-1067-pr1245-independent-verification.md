# PR #1245 independent verification

Reviewed 2026-10-15 by Codex, independently of the correction implementer.
**Verdict: FAIL / NO-GO for integration at `8475969`.** The four requested runtime
corrections work in the exercised cases. Integration still requires the maintained-code
documentation ratchet to pass and governed executable evidence for Option A's
observable Genia behavior. No production code was changed by this verification.

## Identity, authority and scope

- Correction PR: [#1245](https://github.com/m0smith/genia-2026/pull/1245), head
  `847596977fdd3cb41616bf2a57c4a39109d7243e`, branch `claude/amazing-ritchie-8mqq4k`.
- Base: [#1244](https://github.com/m0smith/genia-2026/pull/1244),
  `dcb749dd6551fe1d993f1b9643e707ca69d57a4c`; ancestry check exited 0.
- Review uses the original consolidated register at dcb749d and the correction
  appendix in #1245. That appendix is implementer testimony, not this verdict.
- [Option A approval](https://github.com/m0smith/genia-2026/pull/1244#issuecomment-6197128489)
  was fetched directly: maintainer @m0smith approved meta-frame binding of raw
  `doc`/`meta`/`help`, explicit `define`/`extend`, retention of transferred bound
  callables, R-rooted empty_env, no implicit E access, and no fallback in eval.
- Read AGENTS first; fetched latest main and confirmed its AGENTS hash matches
  the review checkout (`a0f821f829e35834edd88e649652566bad1366da`). Reviewed STATE,
  RULES, REPL README and README's applicable scope/reflection/eval/runtime statements,
  F2 contract §§11/16 and A1–A3, code-documentation contract, run-change and
  LLM_CONTRACT. The newer maintainability process file is on origin/main, absent
  from this stack; it was read through `git show origin/main:...`.

Inspected the entire production diff (environment, evaluator, builtins,
module_fallback), tests and documentation diff, plus ordinary/open declaration,
annotation, assignment, discovery, reflection/cache, runtime factory, fallback,
and Process worker call sites. No conclusion below depends solely on Claude's
PASS summaries. Classification: existing infrastructure/follow-up correction;
no release expansion. This report changes no MCP language-profile fact.

## Correction results

| Register item | Independent result | Evidence and limits |
|---|---|---|
| R01 failed-declaration attribution | FIXED for failed binding operations | `_entry_route` no longer records; set/assign/define_function record after R operation returns. Open declaration checks routed owner first, then successful Env.set records. Existing failures first/1, open log, fixed assignment and function-on-scalar leave no new record; successful operations remain visible. No global rollback erases earlier successes. |
| R15 warning deduplication | FIXED | `claim_fallback_event` protects membership+add with a per-R lock; `_warn` is called after return/release. Real Process workers with forced membership scheduling warn once; distinct-pair and independent-runtime controls pass. This proves deduplication, not warning order across pairs or immunity to a host sink that cannot write. |
| R16 registered runtime recording | FIXED | Registration initializes absent events/lock and captures strict mode before publishing E. Factory state, lock identity and captured strict value survive registration. Manual R/E/M records and warns, strict denial records none, independent runtimes stay independent. Unregistered legacy root remains ordinary lexical lookup. |
| R10/R34 Option A | FIXED in implementation; conformance evidence gate remains | `GeniaMetaEnv.lookup` retries autoload, binds only value-marked FunctionType callables through per-frame scope_bound, returns other/already-bound values unchanged. No call to fallback. Discriminating docstring, present metadata, help, transfer, rebinding and E exclusion cases pass; historical tests fail before the correction. |

R01's exception compatibility was separately compared at acf1a97 and final head:
`first(x) = x` still raises `TypeError: Duplicate function definition: first/1`;
`open log(x) = x` still raises `OpenFunctionRedeclarationError` with
`open-function-redeclaration: 'log' is already bound to a non-function value in module '<entry>'`.
The PR's test comparing two executions on the same head does not itself prove
old/new diagnostic compatibility; this cross-revision comparison does.

The test called “nested successful declaration” actually runs two sequential
top-level declarations. It proves an earlier success survives a later failure,
not arbitrary nested transactional behavior. The implementation has no whole-set
rollback, so no speculative transactional mechanism is needed.

## Required integration corrections

### V01 — blocking maintained-code documentation failure

The [Code documentation job](https://github.com/m0smith/genia-2026/actions/runs/38774070667/job/116557039816)
failed at this head, and the same checker failed locally against the actual PR base:
**9571 records; 2821 legacy gaps; 1 classified exclusion; 13 errors**.

Twelve new/changed required bindings lack documentation:

```text
src/genia/evaluator.py::GeniaMetaEnv (line 547)
tests/unit/test_f2_p2_corrections.py::_PausingEvents.__contains__ (149)
tests/unit/test_f2_p2_corrections.py::_PausingEvents.__init__ (144)
tests/unit/test_f2_p2_corrections.py::_manual_runtime (235)
tests/unit/test_f2_p2_corrections.py::_program_with_list_prelude (29)
tests/unit/test_f2_p2_corrections.py::_worker_module (124)
tests/unit/test_f2_p2_corrections.py::test_r01_failed_assignment_and_failed_function_clause_are_not_recorded.prepare (58)
tests/unit/test_f2_p2_corrections.py::test_r15_claim_is_atomic_for_many_threads_on_one_pair.contend (179)
tests/unit/test_f2_p2_corrections.py::test_r15_warning_io_is_outside_the_claim_critical_section.ReenteringSink (218)
tests/unit/test_f2_p2_corrections.py::test_r15_warning_io_is_outside_the_claim_critical_section.ReenteringSink.write_text (219)
tests/unit/test_f2_p2_meta_reflection.py::_entry (25)
tests/unit/test_f2_p2_meta_reflection.py::_show (31)
```

The thirteenth error is a resolved/stale baseline entry:
`src/genia/evaluator.py::binding::GeniaMetaEnv.lookup`.
Add useful caller-contract documentation or narrowly justified checker-supported
exemptions where appropriate; remove that resolved baseline entry. Do not add new
baseline debt to hide gaps. AGENTS and `docs/contract/code-documentation.md` require
this in the same change. Ruff, function-reference checks and Markdown builds are
different gates and do not cure this failure. Owner: #1245 implementer / @m0smith;
phase: focused documentation correction and recheck before integration.

### V02 — blocking executable conformance placement for Option A

The new meta tests are all in Python and call run_source on Genia source. Their
docstrings label them host-internal because they drive GeniaMetaEnv.lookup, but
their observations (doc/meta/help of a defined name, transferred bound callable,
absence of ambient E access) are user-visible language behavior. A host implementation
detail does not make the observation host-internal.

No spec or native case was added by #1245. AGENTS' portable-behavior placement rule
requires a shared or native twin when reasonably expressible; F2 §16.2 also places
evaluation-scope observations in shared evidence. Existing shared cases already
use eval/empty_env (`r18-surface-agreement-across-equality-like-paths`,
`lambda-pattern-quoted-param`), and F2 reflection cases use `doc_help`. There is no
demonstrated obstacle to a bounded source case. Independently executed source:

```genia
f(x) = "frame docs" x
m = define(empty_env(), quote(f), f)
[eval(quote(doc("f")), m), eval(quote(meta("f")), m)]
```

Observed debug rendering: `["frame docs", {}]`. This is a proposed regression
input, not a newly published user example or a committed conformance test.
Add governed evidence for raw-vs-bound behavior and the relevant isolation
boundary, using existing runner/capability vocabulary where applicable; retain
Python tests for locks, event state, host security and identity internals. If
shared evidence is impossible, document the concrete reason and add an eligible
native twin rather than merely labeling source tests Python-only. No new capability
or second runner is called for. Owner: #1245 implementer / @m0smith; phase:
test/evidence completion, before integration.

Passing parity over the unchanged 825 cases does not prove these new observations.
Adding shared cases must rerun the existing host gate, with unsupported results
reported honestly for the bounded C++ host.

## Documentation truth and remaining non-blocking findings

Two new wording limitations should be corrected during V01 without changing
existing partial-effect semantics:

1. `docs/architecture/python-host-injection.md:62` says “a declaration that raised
   is never recorded.” Binding may succeed before annotation processing raises.
   Both `@doc 1` followed by `first(a,b,c,d,e) = 1` and `@doc 1` followed by
   `log = 123` raise TypeError **after** binding and recording. This is distinct
   from R01's rejected binding: a new binding/clause really exists. Say “a failed
   binding operation is not recorded”; do not promise transactional annotations.
   STATE's successful-declaration wording should be read/qualified consistently.
2. `module_fallback.py:39–41` and `claim_fallback_event`'s docstring overstate the
   inconsistent-state guard. If events exist but `_fallback_lock=None`, a read
   raises TypeError, not ordinary Undefined name. No silent grant occurs, and
   supported construction installs both, so this is not an uncorrected R16 bypass.
   Either narrow the documentation to the checked missing-event condition or
   deliberately harden it with focused evidence. Do not call it a security leak.

| Previous register items | Current independent disposition |
|---|---|
| R02/R03/R04 repeated ownership checks, autoload scans, cold parsing | Accepted #1238 debt unchanged. No new performance measurement or demonstrated regression; do not introduce speculative caches. |
| R05–R09 consumer migration/defaults/fixture/docs/binding_owner | Previous corrections remain in code and focused suite; R01 now restores record accuracy. |
| R11 marker hot path; R12 cache cycles | Remain #1238 debt. New meta binding uses same bounded per-frame cache and cycle GC. No global frame cache, new measured leak, or benchmark claim. |
| R13/R14 shared marker, marking safety, seam limitations | Preserved. Broad Exception assertion for open log is weak in isolation; direct old/new exception probe above supplies the concrete cause. |
| R17 failing stream; R18 stderr write-through; R19 exclusions; R20 marker/CI | Existing guarded IO and positive/negative fallback cases pass. Write-through remains approved A1 compatibility, retirement stays #1230. |
| R21–R23 old interim failures, debt trace/sinks, debugger redaction | Historical interim failures remain accurately attributed; final boundary tests pass. This is not a universal security proof. |
| R24 historical audit execution limits | Still historical; local/CI executions in this report are separately attributed. |
| R25/R26 remote head and durable review records | Prior fixes preserved. Older ignored-path PR links remain metadata cleanup; durable replacements still present. |
| R27/R28 independent label, probe/mutation recipes | Available but previous mutation counts not rerun here. Current regression sensitivity is separately reproduced below. |
| R29 STATE size; R30 MCP ordering; R31 docs checks | Current documentation tests pass; size margin remains one word by the ratified split measure. Constructor ordering proof remains distinct from MCP end-state denial. |
| R32 #1233 chronology | New appendix reports two independent reviews but does not preserve complete dated review transcripts/ranges for each. Commit order proves red-before-fix; cannot reconstruct exact historical review-before-doc handoff timing. This current code/evidence review does not manufacture past ordering. |
| R33 fallback retirement | Unchanged #1230, accountable @m0smith: actual landing date/checkpoint, A1 measurement and R29 gate remain required. No removal or issue closure authorized. |
| R34 nondiscriminatory old pin | New docstring and present-map controls discriminate, demonstrated red-before-fix. Governed source twin still V02. |
| R35 contradictory historical contract preamble | Still low-severity inherited wording; explicit implementation-status paragraph/STATE distinguish current behavior. Reconcile when editing status prose. |
| R36 F no-phantom rationale | Historical rationale remains superseded by consolidated report and successful-binding correction. |

Additional #1238 debt fetched directly from the issue update: duplicate binder
snippet in lookup/_resolve_identifier is small and currently identical; no refactor
needed for this gate. Missing-lock guard has the bounded limitation above. Meta
help sink ownership was unpinned in committed tests: an independent probe now
confirms output goes to captured runtime output even with a meta-local stdout
binding, but that probe is not a permanent regression. Record any desired hardening
under existing #1238, not a duplicate speculative ticket.

STATE/REPL/architecture and the approved contract now describe Option A and
success-only binding attribution rather than treating comments as fixes. RULES
and README retain compatible lexical/eval/module statements. Current MCP profile
has no detailed meta-reflection fact; generated profile check passes. No new
profile fact is required merely to add this host correction, and no authority is
inferred from the profile. Matrix/cheatsheet sync tests pass; no Template-family
primitive was added. The book paths named in older guide prose are absent in
this checkout, so no nonexistent book update is claimed.

## Commands and results

All local Python commands used the following exact prefix, with WORKTREE replaced
by the directory explicitly named below (both source and subprocess imports):

```sh
PYTHONPATH=WORKTREE/src:WORKTREE UV_CACHE_DIR=/tmp/uv-cache UV_PROJECT_ENVIRONMENT=/Users/m0smith/projects/genia-2026/.venv uv run --no-sync
```

WORKTREE for final-head checks: `/tmp/genia-pr1245-review`. Shell globs below
expanded in that checkout. Counts are for complete selections, not unique tests
across overlapping selections.

**Scope selection, run twice**, prefix above followed by:

```sh
pytest -q tests/unit/test_f2_p2_corrections.py tests/unit/test_f2_p2_meta_reflection.py tests/unit/test_f2_p2_b_behavior.py tests/unit/test_f2_p2_b_boundaries.py tests/unit/test_f2_p2_b_hosts.py tests/unit/test_f2_p2_c_topology.py tests/unit/test_f2_p2_d_consumers.py tests/unit/test_f2_p2_e_fallback.py tests/unit/test_f2_p2_f_integration.py tests/unit/test_f2_p2_f_repository_programs.py tests/unit/test_f2_p2_g_closeout.py
```

Default: **212 passed in 7.87s**. Same command prefixed additionally with
`GENIA_STRICT_MODULE_SCOPE=1`: **212 passed in 11.12s**. Deliberate default-mode
fallback tests clear strict through fixtures; explicit strict tests verify denial.
This is not a claim every case in that selection runs strict internally.

**Documentation selection:**

```sh
pytest -q tests/doc tests/unit/test_doc_style_sync.py tests/unit/test_cheatsheet_*.py
```

**517 passed, 35 skipped in 36.03s.** Also executed:

```sh
python tools/gen_function_docs.py --check
python tools/gen_mcp_language_profile.py --check
ruff check src/genia/environment.py src/genia/evaluator.py src/genia/builtins.py src/genia/module_fallback.py tests/unit/test_f2_p2_corrections.py tests/unit/test_f2_p2_meta_reflection.py
python tools/stage_docs_for_mkdocs.py
mkdocs build --strict --site-dir /tmp/pr1245-review-site
python -m tools.code_documentation --base-ref dcb749dd6551fe1d993f1b9643e707ca69d57a4c --inventory /tmp/pr1245-doc-inventory.json
```

First five commands exited 0 (MkDocs 14.57s). Code-documentation command exited 1
with the 13 errors in V01. The PR did not change the baseline file.

**Expanded reflection/security selection:**

```sh
pytest -q tests/unit/test_metacircular_eval.py tests/unit/test_metacircular_syntax.py tests/unit/test_annotation_metadata.py tests/unit/test_f2_p1_reflection_scope.py tests/unit/test_r28_mcp_conformance_security.py tests/unit/test_r28_mcp_compat_conformance.py tests/unit/test_r28_mcp_conformance_lifecycle.py tests/unit/test_r28_mcp_conformance_run.py tests/unit/test_r28_mcp_conformance_surface.py tests/unit/test_r28_mcp_language_profile.py tests/unit/test_protected_configuration.py tests/unit/test_declassification.py
```

Initial sandboxed run was interrupted after **32 failed, 392 passed in 388.31s**,
exit 2: lifecycle/cleanup checks could not execute `ps` (PermissionError), not a
valid all-green security result. An isolated `pytest -q
tests/unit/test_r28_mcp_conformance_lifecycle.py -x --tb=short` reproduced the same
permission error (1 failed in 1.15s). The original run was stopped with SIGINT and
the exact expanded command rerun with process-inspection permission.

Permitted rerun: **663 passed in 635.37s (10:35)**, exit 0. This includes
protected-carrier/sentinel, pruning, compatibility, cancellation, timeout,
worker-cleanup and reflection regressions. No deadline was weakened or test
skipped to obtain this result.

**Regression sensitivity (no production mutations):**

```sh
git worktree add --detach /tmp/genia-pr1245-red-corrections acf1a97
git worktree add --detach /tmp/genia-pr1245-red-meta 77034c3
```

At the historical commits, run each respective new test file using that
worktree's prefix and `pytest -q tests/unit/test_f2_p2_corrections.py --tb=short`
or `pytest -q tests/unit/test_f2_p2_meta_reflection.py --tb=short`:

- acf1a97 original correction tests: **14 failed, 6 passed, 1 warning in 0.64s**.
  One failure was a faulty partial-pruning fixture later replaced with real MCP
  pruning; do not count that fixture failure as a runtime defect.
- 77034c3 original meta tests: **5 failed, 6 passed in 0.75s**.

Then copy **only the final test files**, leaving historical production unchanged:

```sh
cp /tmp/genia-pr1245-review/tests/unit/test_f2_p2_corrections.py /tmp/genia-pr1245-red-corrections/tests/unit/test_f2_p2_corrections.py
cp /tmp/genia-pr1245-review/tests/unit/test_f2_p2_meta_reflection.py /tmp/genia-pr1245-red-meta/tests/unit/test_f2_p2_meta_reflection.py
```

Rerun the same respective pytest commands: **13 failed, 9 passed, 1 warning in
0.63s** for corrections; **5 failed, 6 passed in 0.58s** for meta. Classify the
correction failures accurately: four R01 record assertions, R15's actual **two
warnings** reproduction, missing new helper APIs/lock in the additional controls,
R16 None events/uncaptured strict/isolation failures, and fail-closed failure.
The reentrant-sink case also emits an expected unhandled-thread warning because
the old claim API does not exist; that is not an extra runtime race proof.
All five meta failures are behavioral: two doc, two present-meta and one help.
MCP-denied-name tests pass on the old tree too: they are preservation controls,
not newly failing correction requirements. Final tests pass on final head above.

For the exact exception comparison, ran `python -` with each worktree prefix
(`/tmp/genia-pr1245-red-corrections` and `/tmp/genia-pr1245-review`) and this input:

```python
import genia
for source in ['first(x) = x', 'open log(x) = x']:
    p = genia.make_program_env([])
    genia.run_source('length([1])', p)
    try:
        genia.run_source(source, p)
    except Exception as exc:
        print(source, type(exc).__name__, str(exc))
```

The outputs match exactly as recorded in R01 above.

**Additional host probes:** `/tmp/pr1245-extra-probes.py`, run with final prefix
and `python /tmp/pr1245-extra-probes.py`, checked meta same-frame identity,
different child-frame identity, explicit positive binding metadata, captured
runtime help output despite local stdout, and already-bound transfer. All pass;
the two annotation-error probes and missing-lock result are described above.
Its initial host call `meta.extend([], [])` used Python list parameters where
tagged lambda data is required; that probe failed before behavioral assertions.
Corrected child construction used `GeniaMetaEnv(Env(meta.env))`. No production
change was made to make a probe pass. Exact corrected probe is appended below.

**Shared specifications:** final-head prefix followed by
`python -m tools.spec_runner > /tmp/pr1245-specs.log 2>&1` exited 0;
`Summary: total=825 passed=825 failed=0 invalid=0`. This independently reproduces
the existing suite result, with the new-coverage limitation in V02 unchanged.

## Integration jobs: relevant and actually executed by CI

Read with `gh pr view 1245 --json comments,statusCheckRollup`, `gh run view
38774070667 --log-failed`, `gh run view ... --json headSha,conclusion,event`, and
`gh api repos/m0smith/genia-2026/actions/jobs/ID/logs` for IDs 116557042296,
116557042075 and 116557042018. Network-denied attempts were retried with permission;
empty `gh run --log` redirects were not counted as evidence. API job logs and
check results supplied the actual evidence.

- [Python/C++ parity](https://github.com/m0smith/genia-2026/actions/runs/38774070529/job/116557042296):
  SUCCESS, run attached to head 8475969, executing PR synthetic merge
  `d4b52cf0508acf74008a5224f5355fd77f63fef8`. Python protocol 825 total / 807
  passed / 18 unsupported; C++ 825 / 263 passed / 562 unsupported; every
  failure-class count zero; existing parity checks passed. Python evidence is
  pinned to that checkout; C++ declares older revision
  `6402e668ae85a1e7efe94b3ac3d51f233b730ca4`, so its log explicitly says
  **current-main compatibility only**, not pinned conformance. Cached build
  products were reused; evidence execution was fresh. Bounded unsupported
  reflection/module behavior is not C++ parity with Python.
- [Official MCP SDK acceptance](https://github.com/m0smith/genia-2026/actions/runs/38774070961/job/116557042075):
  SUCCESS, **42 passed in 107.47s**, including negotiation, cancel/disconnect and
  relaunch. This is relevant end-to-end defense against shared evaluator/runtime
  changes breaking worker setup or stdio lifecycle. It does not replace the
  protected-value/pruning checks or prove Option A's new observations.
- Same CI run: VS Code unit job succeeds. Fast-test job succeeds; strict job
  log includes 6879 passed / 63 skipped (not-slow non-loopback), 31 loopback,
  and 825 shared specs. These selectors are not the full local slow+fast union;
  implementer's full-run claims remain separately attributed.

Thus the implementer's “not executed” wording describes their session, not
current CI. These two jobs are relevant integration gates and **are not missing
at the reviewed head**. They need not be rerun locally just to duplicate successful
CI on identical source. They must run on the final integration candidate after
new shared evidence or base retargeting. Their success does not override V01/V02.

## Final recommendation

**NO-GO at 8475969.** Runtime R01/R15/R16 and the approved R10/R34 correction are
independently verified in the stated bounds. Complete V01 and V02, correct the
narrow documentation overclaims, and rerun applicable checks/review before
integration. Keep #1067/#1229/#1238/#1230 open. No code fix, merge, issue closure,
or semantic amendment was performed. This evidence report does not convert old
review summaries or unsupported C++ cases into passing conformance.

## Corrected additional host probe (reproduction artifact)

Save as `/tmp/pr1245-extra-probes.py` and execute with the final-head prefix above.
This is Python-host inspection evidence; it is not a new product example.

```python
"""Read-only Python-host verification probes for PR 1245; no production edits."""
import os
import tempfile
from pathlib import Path
import genia
from genia.evaluator import GeniaMetaEnv, Evaluator
from genia.environment import Env
from genia.utf8 import format_debug
from genia.values import GeniaMap

os.environ.pop('GENIA_STRICT_MODULE_SCOPE', None)
out = []
e = genia.make_program_env([], output_handler=out.append)
genia.run_source('docfn(x) = "probe docs" x\nbound = doc', e)
r = e.runtime_scope()
meta = genia.run_source('define(empty_env(), quote(f), docfn)', e)
raw = r.get('doc')
assert meta.lookup('doc') is meta.lookup('doc')
assert meta.lookup('doc') is not raw
child = GeniaMetaEnv(Env(meta.env))
assert child.lookup('doc') is not meta.lookup('doc')
meta.env.set('meta_marker', 1, metadata=GeniaMap().put('doc', 'positive metadata'))
assert meta.lookup('doc')('meta_marker') == 'positive metadata'
assert meta.lookup('meta')('meta_marker').get('doc') == 'positive metadata'
shadow_out = []
meta.env.set('stdout', shadow_out.append)
meta.lookup('help')('f')
assert 'probe docs' in ''.join(out) and shadow_out == []
bound = genia.run_source('bound', e)
meta.define('d', bound)
assert meta.lookup('d') is bound
assert r.get('doc') is raw
print('meta identity, child binding, explicit metadata, runtime sink, bound transfer: PASS')

for source, name in [('@doc 1\nfirst(a,b,c,d,e) = 1', 'first'), ('@doc 1\nlog = 123', 'log')]:
    p = genia.make_program_env([])
    genia.run_source('length([1])', p)
    try:
        genia.run_source(source, p)
    except Exception as exc:
        print('annotation post-bind failure:', name, type(exc).__name__,
              'recorded', name in p.entry_declared_runtime_owned,
              'bound', name in p.runtime_scope().values)
    else:
        raise AssertionError('invalid annotation unexpectedly accepted')

with tempfile.TemporaryDirectory() as d:
    path = Path(d)
    (path / 'race.genia').write_text('worker(msg) = shared\n')
    p = genia.make_program_env([])
    genia.run_source('shared = 42\nimport race', p, filename=str(path / 'entry.genia'))
    frame = p.get('race').exports['worker'].get(1).closure
    p.runtime_scope()._fallback_lock = None
    try:
        genia.run_source('shared', frame)
    except TypeError:
        print('corrupt lock: TypeError, no silent fallback grant')
    else:
        raise AssertionError('fallback with absent lock unexpectedly succeeded')

```
