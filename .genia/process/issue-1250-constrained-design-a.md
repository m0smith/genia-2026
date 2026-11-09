# #1250 iteration 6 — constrained Design A staging

Non-authoritative process record. NOT APPROVED — DO NOT MERGE. This stages the
approved architecture; it does not approve dependencies or claim acceptance.
[Maintainer authorization](https://github.com/m0smith/genia-2026/issues/1250#issuecomment-6750380905),
[architecture review](https://github.com/m0smith/genia-2026/pull/1318#pullrequestreview-5831753786),
and [verified preflight](https://github.com/m0smith/genia-2026/issues/1250#issuecomment-6751682930)
anchor the scope. The original iteration-5 blocker is historical; its boundary
choice is superseded by that authorization, not its retained evidence.

## Scope and preflight

Starting PR head: `39747f64989336fa919655e0239488a21a5a7dee`; stacked base:
`9f96c6d9369bc29b87d6f63a97b3f7ce89bb7e05`. The environment's unrelated main
checkout was preserved; staging uses an isolated worktree of the exact head.
RED commit: `258ee34f` (44 failures before production edits); additional runtime-seam
RED commit: `48983f1f` (2 failures before seam hardening). Implementation follows
those failing-test commits. Local logs are retained in
`issue-1250-iteration-6-evidence/`; none represents hosted qualification.

Portability analysis:

1. Affected host: Python process infrastructure only; C++ unaffected.
2. Portable semantics: unchanged. STATE's host-status and RULES/REPL/README
   language/runtime contracts remain accurate; no root-document edit is needed.
3. Contract authority: the linked maintainer authorization and architecture
   review govern this temporary infrastructure, below language authority.
4. Shared spec/conformance: inapplicable to this process/credential change;
   existing acceptance nodes remain the oracle, with no semantic-spec edits.
5. Capability/Core IR impact: none; no new host capability or protocol.
6. Host gap: none; no parity claim or known-gap entry required.
7. MCP language knowledge: unaffected; no language-profile regeneration needed.

This is high-risk evidence/security infrastructure. The existing approved design
is reused, with one implementer; independent Claude review remains the next
separate gate. Examples below are process-only. A missing receipt blocks without
installing anything; synthetic API fixtures exercise the authorized path without
issuing a real approval. No Genia feature or release expansion is involved.

## Credential and process ownership

The acceptance job has exactly `contents: read`, `actions: read` and
`pull-requests: read`, at workflow and job level. It uses only the job-scoped
`GITHUB_TOKEN`; no PAT, new secret or signing authority is introduced. The gate
step owns the token as `CONTROLLER_TOKEN` in its environment. A shell-builtin
`printf` sends it over stdin through `sudo systemd-run --pipe`, `unshare` and
`setpriv`. Only explicit `--setenv` values reach the namespace; none contains
the credential. The controller rejects credential environment variables, reads
one bounded token, closes stdin, and constructs the read-only API client.

Every `run.py` phase invocation independently verifies authorization. It fetches
policy from `main`, checks the dispatch and complete contributor range, verifies
GitHub run/workflow/job/artifact provenance and server ZIP digest, extracts and
validates a read-only snapshot, requires a real approved review, checks clean
staged source identity and executable hashes, and rechecks policy/review before
returning. The client is closed and token references are dropped in `finally`
before the first subject clone/build/spawn. Child stdin is `/dev/null` and other
descriptors are closed. `command`, `run_nodes`, and negative-control helpers use
an explicit environment allowlist; GitHub selectors/credentials, arbitrary
secrets, Python startup hooks and pytest option/plugin overrides are excluded.

The process retains a sealed `Authorization` holding the original
`VerifiedSnapshot`. `provision` rejects absent/forged authority and rechecks
snapshot, expiry, clean source and executable hashes. It passes that exact
snapshot directly to `provision_locked`. The historical `APPROVED_DEPENDENCIES =
None` remains unchanged. `provision_locked` itself rejects a missing or forged snapshot. The internal
`prepare_locked` helper remains the **offline packaging preparation seam**, used
by the existing qualification test; it supplies no acceptance authority and
never runs acceptance nodes. Changing the historical sentinel in memory cannot
open the runtime entry. Existing test fixtures were adapted to these admission
seams without changing lock/freeze/backend/error oracles.
No seal or successful approval is deserialized or written as a JSON flag.

This is **not a secrecy boundary** against same-UID or root access. Runner
passwordless sudo, hostile subject code, compromised GitHub/maintainer accounts,
and access to the step environment or process memory remain outside the accepted
boundary. The credential is read-only and job-scoped, expiring at job end.
Early installation-token revocation is not assumed or implemented: whether it
works for `GITHUB_TOKEN` must first be established by an authorized hosted dry run.

## Policy and reviewer authority

`tools/issue_1250/reviewer-policy.json` is an empty candidate-only policy skeleton.
It enrolls neither maintainers nor reviewers and has not been installed on main.
Both empty lists fail closed. The authoritative file must be merged on **main**
by the owner under separate authorization; a staged-branch copy has no authority.
Dispatch supplies its exact SHA-256. The contents API is fixed to `ref=main`;
its base64 bytes, Git blob and SHA-256 must match. A changed policy rejects at the
next invocation and also at the final pre-execution recheck.

The schema has `schema: 1`, repository, exact stacked `base_sha`, `maintainers`
and `reviewers`. Maintainers have positive numeric `id` and audit `login`.
Reviewers additionally require `enrolled_by` (an enrolled maintainer ID),
timezone-aware `enrolled_utc`, an issue-1250 comment URL in `authorization`, and
`independence_attested: true`. Account identity uses numeric IDs, not logins;
GitHub authenticates account control, while the owner attests human independence
and co-author-trailer independence. No identity is fabricated by this staging.

The acceptance dispatch must be attempt 1, manual, from an enrolled actor and
triggering actor, for the acceptance workflow at the exact candidate. PR head
and stacked base must match. Every author and committer in the full base..S
comparison is excluded, along with dispatch actors and qualification collectors.
Pagination checks exact totals, page sizes, base/merge-base, duplicate SHAs,
final candidate and all numeric identities. Unmapped/ambiguous contributors,
divergence, truncation, more than 1000 commits or any API failure reject.

The external receipt binds all existing source/workflow/run/attempt/artifact/
manifest/dependency identities, scope, numeric reviewer and expiry. Its real
GitHub review must be `APPROVED`, on S, by that enrolled nonexcluded ID, after
qualification completion, with the exact standalone canonical marker:

```text
ISSUE1250-APPROVAL sha256:<canonical-receipt-payload-digest>
```

The canonical digest excludes only `review`. COMMENTED, dismissed, self-issued,
wrong-ID/commit/marker, expired or malformed approvals reject. Revocation is a
policy change or review dismissal; it takes effect on the next invocation.
In-flight jobs finish under the accepted design. The existing 24-hour evidence
window and attempt-1 restriction are unchanged. The historical standalone
retrieval CLI remains verification-only; receipt checks now require main-policy
SHA-256 and acceptance-run ID, not a login allowlist.

## Source and toolchain identity

S already contains the staged activation code. Future activation supplies only
external receipt/policy data, with no source-tree patch. Any executable,
workflow, test, proposal or other fingerprinted change requires new exact-source
qualification and review. Qualification fingerprints include the reviewer-policy
skeleton, both workflows, all #1250 Python tooling/tests and existing policies;
dependency inputs have their separate recorded digests.

Subject checkouts moved out of pre-verification workflow steps. The controller
clones the fixed baseline/candidate only after approval and credential disposal,
using the trusted infrastructure checkout's full object history. Smoke remains
baseline-only; negative controls remain disposable clones. Namespace behavior,
cgroup bounds, test nodes, mutant detectors and G0/G1/G2 prerequisite checks are
preserved; tests model these paths without running acceptance.

Acceptance now uses qualification's same official hash-pinned CPython archive
and direct hash-pinned uv wheel bootstrap. The controller additionally compares
actual resolved Python and uv executable SHA-256 values with the verified
qualification record before subject execution and each provisioning entry.
No mutable setup-python action or unhashed pip uv installation remains. Checkout,
download-artifact and upload-artifact actions use immutable official upstream
SHAs; the retained validation packet records the tag checks.

## Failure handling, recovery and remaining gates

Missing authorization and any verifier error retain sanitized BLOCKED evidence
and abort with no subject process. API 403/429, malformed data, bad archive or
any provisioning error fail closed; no cached approval or automatic retry grants
authority. Existing evidence/diagnostic destinations cannot be overwritten.
Once a phase starts, errors remain FAIL in its summary; failure is never turned
into acceptance credit. Temporary snapshot directories are owned by the
controller outside the source tree and are read-only, not a root-proof sandbox.

Rollback: omit authorization, dismiss the review or revoke policy on main under
separate owner authorization; stop dispatching. Revert this iteration's staged
commits if needed, retaining all evidence. Never apply the historical
`activation.proposed.patch`; it is superseded history. Never activate by changing
the sentinel. The pending receipt and historical registrations, locks, freeze,
original 22 failures, prior evidence packets and semantic oracles are preserved.

Still unverified locally: shared hosted stdin behavior through systemd/sudo,
job-token artifact/review access, storage redirects, official CPython installer,
runner shared-library behavior, API field compatibility, optional early token
revocation and the end-to-end 24-hour operational budget. These require the
**later separately authorized hosted dry run**. No actual qualification artifact,
workflow run or hosted test was used here.

The next gate is independent Claude review of the final exact staged SHA/tree,
explicitly including the changed credential assumption. Independent reviewer
identity/enrollment on main remains blocked. Registration, hosted dry run,
qualification, reviewer receipt, activation and each acceptance stage require
separate authorization. No GREEN declaration, executor-A/#1316 change, merge or
issue closure is included.
