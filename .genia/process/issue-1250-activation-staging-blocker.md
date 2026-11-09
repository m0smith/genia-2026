# #1250 final activation staging — iteration 5 blocked

> Historical phase record: current constrained Design A staging is documented in
> [iteration 6](issue-1250-constrained-design-a.md). That record supersedes the
> old unwired-caller/login-allowlist instructions and obsolete activation patch,
> not the evidence or verdict recorded here. No baseline activation is approved.

Codex, 2026-11-09. **NOT APPROVED — DO NOT MERGE.** This is a
trust-boundary assessment, not completed activation wiring or qualification.
The user explicitly requires: “If the current architecture cannot satisfy these
requirements without changing the trust model, document the conflict and stop
for review rather than weakening validation.” That stop condition applies below.

Assessed executable source: `6f491c5edf8c6e6b0747c06b856de70d58712f2e`,
tree `5badfa4c90290212c6320bb3bfc50fb19fdc7fe9`.
PR #1318 base remains `9f96c6d9369bc29b87d6f63a97b3f7ce89bb7e05`.
[Preflight](https://github.com/m0smith/genia-2026/issues/1250#issuecomment-6748307077)
proposed same-process verification plus externally authenticated reviewer policy.
This assessment supersedes its GO-to-implementation recommendation. That proposed
authority/bootstrap arrangement is not implemented or independently approved.

## Conflict requiring an independent decision

The existing `hosted_trust` contract requires the reviewed verifier to run outside
the candidate/test process. The independent operator supplies the authorization
tuple and reviewer allowlist. GitHub API provenance and the server artifact digest
establish the snapshot; a genuine independently allowlisted APPROVED review binds
the canonical receipt. `VerifiedSnapshot` is a transient Python capability with a
private object seal, inode identity and read-only content checks. It is deliberately
not a serialized assertion of approval.

The acceptance workflow starts `run.py` in a separate non-root PID1 namespace
through systemd/unshare/setpriv. Its explicit environment forwarding contains no
GitHub API credential or external approval data. `run.py` documents no network
credentials. It later executes subject build code and tests through subprocesses;
the runner's shared uid and passwordless sudo are explicitly not a security
boundary. Its only current provisioning entry rejects the None sentinel.

An outside verifier cannot pass its live snapshot capability across that process
boundary. A manifest path, JSON `api_verified` flag or successful exit status cannot
replace the seal. The old activation patch both changes the source after collection
and lacks the live capability. It remains preserved and unapplied, not a recipe.

Two concrete designs are possible, but neither is merely connecting an existing
approved caller:

| Option for independent review | Required trust-model decision |
| --- | --- |
| Retrieve and verify inside the trusted PID1 infrastructure orchestrator, then provision in that same process | Admit a GitHub read credential and external operator controls into a process that starts subject code. Decide credential lifetime, external control ownership, child inheritance and same-uid/root threat assumptions. Removing environment variables alone does not establish an adversarial isolation boundary. |
| Keep retrieval/verification in a separate control process | Define an authenticated transferable approval capability and its issuer, verification root, scope, expiry/revocation and transport. Do not deserialize the current private seal or trust a candidate-provided approval flag. |

The preflight additionally proposed authenticating reviewer enrollment and a
separate data-only activation authorization through maintainer API comments.
That introduces a new policy authority, canonical payload and enrollment protocol;
the current receipt verifier does not implement or authenticate that policy.
An external filesystem location alone does not prove who authorized its contents.
No new authority, environment secret, account or successful receipt was installed.

**Requested Claude decision:** assess whether the first option can preserve the
intended existing operator trust assumptions, explicitly approve its credential
and reviewer-policy boundary, or specify the second option's authority contract.
This is not a claim that secure activation is impossible. It is a stop before
silently choosing a security contract. Final staged executable code and its full
synthetic caller tests remain outstanding; do not qualify this documentation-only
head as though final activation wiring existed.

## Reviewer authorization remains blocked

No distinct authorized account was identified. No allowlist entry was added.
Before receipt issuance, the maintainer must identify a genuinely separate GitHub
account and explicitly authorize its enrollment outside candidate evidence under
the reviewed policy. It must not be a source author or either collection actor.
The current verifier excludes the head author and collection actors; excluding
all contributing source authors must be resolved with the caller design rather
than assuming that a docs-only head author represents every contributor.

The independent reviewer must inspect the exact staged commit/tree and all bound
workflow/run/attempt/artifact/manifest/runtime/build hashes, review the canonical
payload, and submit an actual GitHub APPROVED review on that commit. Its body must
contain the standalone `ISSUE1250-APPROVAL sha256:<canonical-payload-digest>` marker.
The receipt references PR 1318 and the authoritative review ID. API review state,
account, commit, marker and submission/expiry timestamps must all verify. COMMENT
reviews and the current same-account preparation reviews are insufficient.
This procedure does not enroll an account or authorize activation.

## Read-only operational assessment

See `issue-1250-activation-staging-evidence/readonly-api-metadata.json` for UTC
timestamps, request URLs, response bodies and selected rate/pagination headers.
Initial sandbox requests failed with URLError; the permitted network retry
succeeded. No token/header credential or artifact contents were recorded.

Official GitHub tag metadata on 2026-11-09 confirms checkout v4 at
`11d5960a326750d5838078e36cf38b85af677262` and upload-artifact v4.6.2 at
`ea165f8d65b6e75b540449e92b4886f43607fa02`. Both refs point directly to commits.
The checkout v4 tag is mutable; the workflow consumes its immutable commit pin.

Historical run `42497808332`, attempt 1, is a **failed acceptance-workflow
diagnostic smoke**, not qualification evidence. Only metadata was read. Its job
response includes head SHA, runner ID/name, runner group `GitHub Actions`, labels
`ubuntu-24.04`, step states and total_count. Skipped jobs have null runner identity;
they cannot satisfy successful qualification. The artifact response includes ID
`13623249823`, digest, size, expiry and workflow-run repository/head identifiers.
This validates field availability for that historical response, not compatibility
of a future qualification run or successful bootstrap/extraction. No real artifact
was downloaded, and no historical run was executed or retried here.

The qualification workflow REST lookup returns 404; no registration was performed.
The default branch must contain a separately authorized registration before manual
dispatch is available. Registration does not establish the code executed: the
event SHA, workflow SHA, contents hash, commit/tree, run and attempt must still
match the final reviewed staged source. The acceptance workflow currently restricts
its ref to the infrastructure branch; final branch/ref handling is also unfinished.

Jobs/artifacts were requested with per_page=100; observed counts are 3/1 and there
is no Link header. The current verifier rejects truncated or unexpected counts;
it does not silently accept the first page. Standard limits depend on credential
type (commonly 60 unauthenticated or 5,000 authenticated core requests/hour);
the observed session response reports 15,000 with 14,967 remaining at artifact
lookup. Do not assume that quota for a future token. The verifier re-fetches
metadata at receipt verification; rate-limit/shape failures must remain closed,
with no stale cached approval fallback.

Use only repository-scoped read permissions needed for contents, Actions metadata/
artifacts and PR reviews; no write permission or workflow dispatch is needed for
verification. Token isolation is the unresolved caller decision above. The current
API client restricts redirects and removes authentication on storage fetches;
the live artifact redirect domains were not tested. Bootstrap archive layout,
ensurepip/direct-wheel installation and real cold-cache integration remain
unexecuted on hosted Ubuntu. Evidence collection, review and activation must fit
the existing 24-hour freshness window, attempt 1 only. No retries extend it.

## Validation and immutable evidence

No executable, workflow, test, receipt, registration, lock or freeze was changed.
Preparation suite: **226 passed, 1 skipped**, 6.90 seconds. The skip is the opt-in
real cold-cache integration. The suite includes synthetic complete snapshot/receipt
verification, invalid receipt/API provenance, changed source rejection and default
provisioning rejection. Those existing tests do not prove a new activation caller.
Ruff passed. No new TDD RED or implementation PASS is claimed: caller implementation
stopped before test/implementation phases under the explicit trust-model gate.
Prior RED/PASS packets remain unchanged; this packet adds current guard evidence.

`unchanged-inputs.json` hashes 107 tracked inputs at the assessed source, including
all issue-1250 tooling, dependency fixtures, preparation tests, both workflows,
AGENTS, four root docs and pyproject. All are byte-identical to that source.
Historical lock digest remains
`27ca5a9328ba8641ce18078782c7edecdc8a753aa6b4fd3ca57932a66d49f291`;
proposed runtime lock remains
`2bb0f5f5a5b073539ba0df6e92820a461d3cfb5364ca8951a99717b3c684a8bf`.
The original 22 failures and every prior evidence packet remain immutable.
The checked-in sentinel is None and the receipt pending; no baseline is active.

No Genia semantics, portable contract, Core IR, capability, C++ host or MCP language
knowledge changed. The four root authority documents remain accurate and unchanged;
this infrastructure assessment belongs in process documentation.

## Sequencing, recovery and next gate

1. Resolve this architecture stop through independent Claude review and explicit
   authorization of its trust boundary; finish final activation staging and TDD.
2. Independently review the complete final staged SHA/tree. No executable changes
   may remain solely to consume an approved receipt.
3. Separately authorize any default-branch workflow registration.
4. Separately authorize one exact-SHA hosted qualification run.
5. Independently retrieve and verify hosted evidence outside untrusted subject code.
6. Enroll the distinct authorized reviewer; obtain genuine approval and receipt.
7. Separately authorize data-only activation under the approved caller design.
8. Separately authorize subsequent acceptance gates.

Missing identity, stale evidence or source changes block advancement. Preserve
failed evidence; a new staged source requires fresh exact-source qualification.
Rollback now is removal/revert of this additive documentation/evidence commit,
without touching prior packets. Future recovery must revoke external activation
authorization under the reviewed design, preserve receipts/artifacts/failures and
restore the absent-control closed gate. Do not restore the obsolete patch.

No workflow registration/dispatch, hosted qualification, smoke, G0/G1/G2, merge,
issue closure, executor A/#1316 investigation or GREEN declaration occurred.
Stop here for independent Claude review; final activation staging is incomplete.
