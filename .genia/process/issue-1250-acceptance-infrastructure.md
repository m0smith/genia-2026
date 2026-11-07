# Temporary #1250 acceptance infrastructure procedure

Non-authoritative CI/process instructions for PR #1317. `GENIA_STATE.md`
remains final authority. No language, runtime, capability or host parity change.

**Removal condition:** after the maintainer records #1250's acceptance decision,
delete `.github/workflows/issue-1250-acceptance.yml`, `tools/issue_1250/` and its
focused helper tests, and this temporary procedure in the same retirement change.
Retain durable evidence/authorization links in #1250's append-only ledger.

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
metadata and actual Python/uv versions. It generates the baseline-local lock,
syncs locked dependencies and checks the historical lock/freeze before running
only the exact probe→session cleanup node. Its outcome is `DIAGNOSTIC_ONLY`,
even on success. Upload and digest reporting run on failure as well.

GitHub's CPython 3.12.14 build is recorded, not assumed identical to the original
Clang build. uv 0.13.5, generated-lock digest and normalized installed freeze must
match published evidence. The live solve may drift; fail closed rather than pin
new versions or copy an old lock to hide drift. Hosted Python availability,
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
