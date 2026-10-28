# #1285 — process-reaping investigation and scoped preflight

Date: 2026-10-27. Non-authoritative public process evidence.
Tracking: [#1285](https://github.com/m0smith/genia-2026/issues/1285);
predecessor [merged #1293](https://github.com/m0smith/genia-2026/pull/1293).
Branch: `issue-1285-mcp-reaping-investigation`; owner maintainer, author Codex.

## Preflight and phase plan

The user authorizes public diagnosis and only evidence-supported narrow remediation.
Includes unchanged-test reproduction, process ownership/reaping traces, temporary
subreaper comparison, supported-shutdown controls, fixture correction if proven,
existing/new regression evidence, maintainability review and independent actual-
commit audit. Excludes language/runtime/MCP semantic changes, unrelated refactors,
root lock/CI policy changes, paid services, hidden data/oracle/candidates/trials.

Latest AGENTS blob `b072beb55d22d5856d3d356d73c60704e04d197f` and STATE/RULES/
REPL/README are unchanged from the previously read source chain. STATE is final
authority. Issue decisions, #1292/#1293, draft #1291, replay/provenance evidence,
`docs/process/run-change.md`, the preflight template and maintainability review
guide apply. R28 contract sections 4/12 and `docs/mcp/stdio-development.md` govern
supported EOF/signal shutdown and owned worker kill/reap; SIGKILL cannot execute
the killed parent's signal/finally/wait logic.

Maturity N/A for fixture/process work. Python reference host implementation and
portable language contract remain unchanged; C++ is unaffected. No new MCP tool,
protocol or authority is proposed. Minimality, explicit ownership and the
validated-pipeline priority are preserved; hidden-oracle infrastructure is not
being built. Cross-file impact is limited to the justified test helper/regression
and public process/evidence records. Authoritative language docs, generated
profile, book, cheatsheets and shared specs need no semantic synchronization.
MCP language-knowledge impact: none, because assistant-visible behavior is unchanged.

Seven portability fields: (1) STATE authority unchanged; (2) boundary is Python
test process ownership, not Core IR/Genia values; (3) existing lifecycle tests are
host-specific executable evidence; (4) Linux `/proc`/subreaper experiments are
Linux-only, not a portable capability; (5) no Python/C++ behavior/parity claim;
(6) no new known-host-gap entry; (7) maintain scoped evidence, no semantic docs.

Verification plan: preserve the existing failing test and zombie detection; add
a host-fixture regression for exceptional context exit if a correction is
justified; commit failing evidence before implementation. Then repeat targeted
checks, run related lifecycle and MCP conformance tests, both full Python-host
pytest partitions and relevant docs checks. No deadline extension, arbitrary
sleep, skip or exception for zombies is allowed. Polling in diagnostics observes
bounded process-state changes; it is not used to manufacture a passing condition.
Examples are process-only. Complexity is a small ownership correction, not a new
supervisor framework. Stop if cause remains unresolved or scope must expand.

Phase order: preflight/evidence → failing test commit → justified implementation
referencing RED → maintainability review → evidence/docs synchronization →
independent actual-commit audit. Existing contract is preserved rather than
amended. Initial gate permits investigation only; final recommendation depends
on broader verification, not a single passing target.

## Baseline and initial observations

Baseline source `9d930d07bf1ecdb1f0b59ed76abf67ef002e7e90`; original approved
lock SHA-256 `02faf4e82e2f6f2ea9af3f5d39ce67390da55fcc2d93577a9affc273308aafe8`;
CPython 3.12.15, outer uv 0.13.5. The disposable clean replay environment from
#1293 is still available; its lock and dependencies are not changed or resynced.
The remediation worktree starts at `25a9c07013d3ed1169f4b707b7756044256e0a58`;
runtime, launcher and fixture files match the older executed baseline before edits.

The configured client command is `uv run --no-project --no-python-downloads
python hosts/python/mcp_launch.py`. Its process chain includes a uv wrapper, a
Genia launcher and a Genia host; the launcher waits for its own host child. The
fixture currently calls `self.proc.kill()` on context exit, then closes stdin and
waits for that direct command. For the configured command, SIGKILL targets uv,
which cannot then wait for its launcher child.

PID 1 in this execution container is `tail`, state sleeping. An unchanged targeted
test under ordinary supervision failed in 60.519495s wall (exit 1). The captured
orphaned child became `Z`, PPID 1; an attempted wait from the tracer returned
ECHILD because the tracer was not its parent. The Genia host disappeared. A
separate process-local Linux subreaper ran the same unchanged test: PASS in
0.912644s wall (exit 0), with two adopted child exits reaped at status 0 and no
captured identity left. The subreaper affected only the diagnostic parent; no
system/PID-1 configuration was changed.

Initial EOF/SIGTERM/SIGKILL controls found that EOF and SIGTERM removed observed
descendants, while SIGKILL orphaned the Genia launcher, which became a zombie
after the host disappeared. A tool-selection detail was discovered: the nested
configured command resolved uv 0.12.23 from PATH despite the outer verifier using
0.13.5. The original A/B traces are retained (the controls were rerun and replaced); an explicit nested-uv-0.13.5
comparison is required before attributing the effect independently of uv version.
Initial diagnostic role labeling was corrected so a uv argv containing a launcher
script is not itself mislabeled as the Python launcher; raw earlier trace is
retained, and corrected comparisons identify process roles separately.

Direct execution outside this container/under BENJAMIN is BLOCKED: no direct host
access is supplied. A proper init Docker image is NOT TESTED; the supported
process-local subreaper comparison is evidence about reaping, not image validation.

## Executed evidence, remediation and final gates

The controlled comparisons and remediation results follow below.
No runtime defect is assumed. A PID-1 orphan and a process the runtime still owns
are different responsibilities; a killed parent cannot reap, while a living
subreaper/PID 1 can adopt and wait for an orphan.

Budget stays $0 incremental spending. No paid infrastructure/model/storage,
billing change, manual CI dispatch or private material is involved. This is not
authorization to ignore an unexplained failure or weaken the original assertion.
All hidden-material/oracle/candidate/comparison NO-GO boundaries remain in force.

## Controlled findings and remediation (2026-10-28)

Classification: **MULTIPLE_CAUSES** — fixture ownership error plus a non-reaping
container PID 1, not a demonstrated Genia runtime ownership defect. With both
outer and nested uv fixed at 0.13.5, the unchanged test failed under ordinary
supervision in 60.481503s and passed under a process-local subreaper in 0.912314s.
Ordinary chain: outer uv 21656 → pytest 21660 → configured uv 21662 →
launcher 21665 → host 21667.
After fixture SIGKILL of uv, launcher 21665 was adopted by PID 1 and became Z;
the host disappeared. The tracer's wait returned ECHILD, confirming no custody.
Under subreaper 21870, orphan launchers 21879 and 21886 were adopted and waited
at exit status 0; no captured identity remained. PID/start-token identities,
PPID/PGID/SID and state transitions are recorded in the
[public evidence](../experiments/issue-1285/process-reaping/evidence.json).

Supported-shutdown controls with the same nested uv: EOF exited 0 and removed
descendants in 0.031531s; SIGTERM returned raw status 241 and removed descendants
in 0.007358s. SIGKILL returned -9 and orphaned launcher 21912, which became Z
under PID 1 after host 21914 disappeared. No interpretation of raw 241 is claimed.
The diagnostic parent alone enabled Linux prctl PR_SET_CHILD_SUBREAPER (36, 1),
verified PR_GET_CHILD_SUBREAPER (37), and used waitpid(-1) to reap adopted exits
while supervising unchanged pytest. Ordinary mode did not enable adoption.
This is an init-equivalent comparison, not a tested Docker image. Direct
BENJAMIN/host execution remains unavailable; image/init verification is deferred.
Complete raw traces/logs remain in this session's diagnosis workspace; selected
ownership transitions and raw-file hashes/lengths are committed for review.

RED commit `5b35386fd5d4d2b15e1afea346cac8371c741c63` added a real exceptional-
context subprocess regression: it failed before correction (60.31s). Fix commit
`38eb980ee5fc95bdad45f197543861c2c2eb6046` changes only the shared test fixture:
request TERM, close stdin, wait up to 25 seconds, then kill and wait the direct
command for up to 5 seconds. This retains the existing total 30-second budget.
A real TERM-ignoring child regression verifies bounded fallback and pipe closure.
No existing assertion, worker deadline, zombie detection or skip was weakened.
Runtime/launcher code, authoritative semantics, CI and dependency lock are unchanged.

GREEN: original target plus both regressions, 3 passed in 25.96s. The original
target then passed five independent repetitions (0.82–0.88s wall each).
Full two-worker regression: non-loopback 7,105 passed / 60 skipped (415.55s),
loopback 31 passed (3.98s), total **7,136 passed / 60 skipped / 0 failures**.
JUnit subsets include 23 lifecycle and 507 MCP conformance tests; these are
included in the total, not additional independent executions. Documentation
inventory, instruction validation, generated MCP profile check and changed-file
Ruff all passed. Full commands, timings and log hashes are in evidence.json.
Execution reused the approved clean 44-package environment without sync/install;
uv 0.13.5, CPython 3.12.15 and original BENJAMIN lock were preserved.

Independent maintainability review of actual implementation commit 38eb980e:
PASS, no blocking or deferred findings. The reviewer checked ownership, signal/
EOF behavior, fallback boundedness, callers and both real subprocess regressions.
Final actual-commit evidence audit is recorded in the PR handoff after completion.

#1226 applicability was checked: issue closed; comment 6368569494 records the
five-observation pilot complete. No new observation was posted or policy extended.
For this task Python/Linux process tooling is class D (another tool is better);
no Genia substitution/comparison was made, and review time was not measured.

**Gate:** GO only to resume public frozen-runner preparation. This does not
verify an immutable image, package/backend/OS freeze, equal independent workers,
identity isolation or private custody. All hidden-material/oracle/candidate/trial
NO-GO boundaries remain. No paid service or manual workflow execution occurred.
**Single next action:** owner review and merge of this narrow remediation before
resuming public immutable-runner preparation and its independent replay gate.
