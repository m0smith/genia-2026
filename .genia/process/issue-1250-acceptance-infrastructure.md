# Temporary #1250 acceptance infrastructure procedure

Non-authoritative CI/process instructions for PR #1317 and its dependency proposal. `GENIA_STATE.md`
remains final authority. No language, runtime, capability or host parity change.

**Removal condition:** after the maintainer records #1250's acceptance decision,
delete `.github/workflows/issue-1250-acceptance.yml`, `tools/issue_1250/` and its
focused helper tests, and this temporary procedure in the same retirement change.
Retain durable evidence/authorization links in #1250's append-only ledger.

## Proposed dependency baseline — NOT APPROVED

Preparation on 2026-11-08 generated one lock in an isolated baseline archive.
See [the proposal and difference report](issue-1250-dependency-proposal-2026-11-08.md)
and `tools/issue_1250/dependencies/proposed-2026-11-08/` for immutable proposed
bytes, freeze, provenance and graph. Historical `LOCK`, registration freeze and
original22 remain unchanged. The proposal is a different environment from the
historical failures; it has no acceptance credit.

`provision()` now stops before installation while `APPROVED_DEPENDENCIES` is
`None`. There is no CLI/environment activation switch. Independent review must
approve or reject the proposal before a separate reviewed registration change
can connect the shared-lock helper. No dispatch is authorized by this change.
The build-backend correction is documented in
[the correction record](issue-1250-build-backend-correction.md). It pins seven
build distributions and their wheel hashes separately from the proposed runtime
lock. Each subject receives a fresh isolated build venv; no backend-only package
is installed into its runtime/development venv. The existing Hatchling backend
builds a real PEP 660 editable wheel, which is installed without dependencies or
index lookup. The frontend records PEP 610 editable source metadata and maintains
installed RECORD. The project-wide pyproject/build contract is unchanged.

Backend evidence is checked against literal SHA-256 constants before install;
direct-wheel installs require hashes, prohibit transitive dependency acquisition,
and use no index. Complete build inventories and static/dynamic requirements
must match before building. Missing/tampered evidence, absent/wrong backend,
failed build/install, lock mutation or any extra installed backend distribution
fails closed. Target freeze names its exact interpreter; an inherited active
VIRTUAL_ENV cannot redirect verification. Supported scope is CPython 3.12.14,
uv 0.13.5, Linux x86_64; conflicting UV_/PIP_ configuration is rejected.

The original default-isolation installation evidence remains immutable and does
not identify its backend versions. Additive corrected cold-cache baseline and
candidate packaging evidence names and hashes the actual backend inputs. It
supersedes only the earlier installation reproducibility claim. Hosted execution,
acceptance remain unperformed. Independent review approved the build-backend
correction only; baseline activation is still unapproved.

## Mandatory future dependency qualification

[Registration preparation](issue-1250-registration-preparation.md) defines the
inactive registration proposal and exact unapplied activation wiring. The
read-only approval_validation module rejects missing/stale/skipped/failed or
wrong-source/input/environment evidence. Future activation wiring must call it
with a separately approved manifest receipt before any provisioning. A normal
unit run may omit integration; explicit future qualification cannot. Local
Debian evidence never supplies hosted Ubuntu qualification. No current workflow
or sentinel was changed to activate this behavior.

The frontend now validates the existing installed RECORD before modification and
all updated hashes/sizes afterward. Both backend wheels and the built editable
wheel are installed through hash-required direct requirements. Additional
negative tests cover real uv hash rejection, backend/install failure propagation,
RECORD corruption, requirements/backend-path and subject/environment mismatches.

## Prepared hosted qualification (unexecuted)

[Hosted qualification infrastructure](issue-1250-hosted-qualification-preparation.md)
adds a separate manual-only workflow, immutable official toolchain/action pins,
API-bound run/artifact retrieval, safe read-only ZIP snapshots and an independent
receipt contract. No hosted workflow was executed or registered by this phase.
The old self-attested hosted validator is now content validation only; the public
hosted boundary additionally requires a verifier-issued API-backed snapshot.
An arbitrary artifact directory or GITHUB_* claim cannot establish hosted trust.

The receipt remains pending/absent. The old activation patch remains unapplied
and is not a usable hosted activation recipe. Final staged executable/workflow
code must be reviewed before collecting its exact commit/tree; any code change
requires requalification. The external reviewer must approve a source/run/artifact-
bound payload through an independently allowlisted API review identity. Same-account
preparation COMMENT reviews do not become activation receipts. No active
provisioning entry is wired to this new helper, and the sentinel remains None.

## Authorization and registration

Registration, diagnostic smoke dispatch, and G0–G2 dispatch are three separate
maintainer actions. This implementation authorizes none of them. Independent
Claude re-review precedes registration/smoke authorization. GitHub must register
the workflow on the default branch before dispatch is available; any minimal
stub must preserve the inputs and be reviewed separately. Verify that the
workflow appears in Actions and that dispatch at the reviewed branch actually
loads that branch's workflow (including YAML anchor support).

Dispatch must name the reviewed 40-lowercase-hex `workflow_sha`, select the
separately authorized `mode` (`smoke` or `acceptance`) and set `authorized=true`.
The first step of each selected job fails loudly unless event, repository,
branch, mode, exact executing commit (`GITHUB_SHA` and `GITHUB_WORKFLOW_SHA`),
and `GITHUB_RUN_ATTEMPT=1` match. Re-run-job attempts are rejected; new attempts
need a new run and ledger authorization, with every earlier outcome preserved.
No secret binding, write permission or persisted checkout credential is used.

## Diagnostic smoke: never G0 acceptance

One Ubuntu 24.04 hosted job, 15-minute bound, exact baseline checkout only:
`0b25d2b45722f4397fd712f2f4b8eb3ea294f6e5`. No candidate checkout, mutant or signal
node. The actual hosted wrapper creates the resource/PID/mount boundaries and
drops uid, then verifies non-root PID 1, 2-CPU/8-GiB cgroup limits, provisioning
metadata and actual Python/uv versions. Dependency provisioning currently stops
at the independent-approval gate. After separately reviewed activation, the
shared helper copies one registered immutable fixture, verifies its literal SHA
before and after locked sync, and compares the registered installed freeze
before running only the exact probe→session cleanup node. Its outcome is `DIAGNOSTIC_ONLY`,
even on success. Upload and digest reporting run on failure as well.

GitHub's CPython 3.12.14 build is recorded, not assumed identical to the original
Clang build. uv 0.13.5, immutable-lock digest and normalized installed freeze must
match independently approved registered evidence. Acceptance provisioning has
no `uv lock` invocation and cannot independently resolve baseline/candidate
project dependencies. Missing/tampered evidence, declaration drift, conflicting
existing locks, failed/stale locked sync, rewritten locks or freeze drift fail
closed. A proposed lock is never approved merely by copying it; historical
evidence is preserved separately and is not overwritten. Hosted Python availability,
systemd/cgroup behavior and namespace integration remain unverified until the
separately authorized smoke runs. A clean smoke requires review before a separate
exact-SHA G0–G2 authorization; it never supplies acceptance credit.

## Bounded acceptance after separate authorization

Two sequential hosted VM jobs A/B (45-minute bound each) run baseline G0:
24 exact lifecycle/launch/teardown/SDK IDs, then both reviewed scratch controls.
The fixture control reverses only reviewed R4 patch
`38eb980ee5fc95bdad45f197543861c2c2eb6046`; the probe→session test must reach
`a launch left processes behind`. The other clone neutralizes only
`child.send_signal(signum)`. SIGHUP must fail its command-exit assertion;
SIGTERM/SIGINT must show `session.proc.wait(timeout=GRACE_S)`,
`subprocess.TimeoutExpired` and `timed out after 60 seconds`. Both actual wall
and JUnit testcase durations must be at least 55 seconds. No oracle or timeout
changes; missing/unrelated/short failures fail detection.

Only after G0 succeeds and its namespace exits does that same VM enter a fresh
namespace for candidate G1. A verified same-job G0 manifest/provenance is required.
Candidate: `e3562f620020023ea39c44273068872d6bc73fe6`. Run focused15, exact original22,
teardown2, then each of the three signal nodes three consecutive times. Explicit
identities determine exclusions/inclusions; node positions do not. The original
registration is checked against the frozen candidate's closeout JSON.

G2 needs both successful G1 jobs. Another 45-minute hosted job qualifies its own
G0 and fresh namespace, then verifies both downloaded manifests and outcomes.
All three VM boot IDs must differ. Attempt/run/workflow/image/kernel provenance
must match; runner names are compared and reported (labels are not globally
unique VM identities). This is **per-VM independence within one Ubuntu 24.04
image class**, not environment diversity or a Codex sandbox. Run exactly
original22+teardown2 with `pytest -n 2`. Any failed prerequisite stops advancement.
G3–G5/full GREEN are absent.

## Evidence and limits

Each phase writes raw commands/exits, exact IDs/counts, JUnit/logs, mutant diffs,
lock files/digests/freezes, actual interpreter/uv build, kernel, runner/image/
workflow/authorized SHA, boot ID, uid/PID1, cgroups and passive process signal
masks/groups/sessions. No broad environment or credentials are uploaded. A
non-reaping PID1 retains orphan zombies until namespace exit; the runner user
has passwordless sudo, so dropping uid models client execution rather than
creating a security boundary. Existing tests still control child stderr capture.

Phase summaries distinguish PASS, failure, NOT RUN and expected mutant detection;
mutant rc=1 remains an observed test failure. Cleanup metadata errors cannot
replace an original test/preparation exception. Root artifact manifests cover
phase manifests and summaries. Print manifest SHA256 and outcomes in job logs
and step summaries, then print upload-artifact's independent archive digest, ID
and URL. Internal manifests remain self-attested; quote both digests and the
run/attempt/authorization URLs in the ledger after an authorized run. Archive
links before the 30-day retention expires. Cancelled or incomplete jobs supply
no qualification; missing artifacts or summaries fail closed.

No passing hosted context explains the unresolved executor-A signal behavior.
Historical failures, independent production/semantic/truth reviews and later
release authorization remain separate.
