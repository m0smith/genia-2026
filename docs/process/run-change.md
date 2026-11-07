# Running a Genia Change

Starting with R26, complete the
[GENIA Change Pre-Flight issue template](../../.github/ISSUE_TEMPLATE/genia-change-preflight.md)
before implementation for new release work, semantic or language changes,
runtime or host behavior changes, conformance/spec changes, and multi-file
changes. Small typo or documentation-only fixes may skip it only when they have
no semantic, host, conformance, or process impact. If the pre-flight cannot be
completed, the work is not ready to implement. This is a project process
control, not Genia runtime behavior, and does not apply retroactively to closed
releases through R25.

For work requiring pre-flight:

**Phase handoffs:** For issue-tracked work, follow the [GitHub issue comment handoff contract](llm-prompts.md) for each phase below. Read preceding phase comments and linked evidence before proceeding. Post and verify the structured issue comment before declaring each phase complete; retain failing and intermediate evidence. A local temporary handoff file is optional scratch, never the authoritative record. If GitHub publication fails, mark the phase handoff BLOCKED and do not advance. Commit gates, independent review, explicit authorization, and semantic source-of-truth precedence remain unchanged.

1. Create branch: `issue-<number>-<short-name>`
2. Run preflight prompt
   - Pre-flight must include a completed PORTABILITY ANALYSIS block (section 3a).
   - All seven portability fields must be answered before the contract phase begins.
   - Incomplete portability analysis is grounds for blocking the contract step.
   - If the change adds or changes portable observable behavior, complete the
     executable semantic conformance obligation from
     `docs/architecture/executable-semantic-conformance.md` before the contract
     phase:
     1. identify the portable authority and representation/boundary;
     2. identify the shared executable spec evidence (or explicitly justify why
        shared evidence is impossible without claiming unproved cross-host
        conformance);
     3. identify applicability using the existing `spec/manifest.json`
        capability vocabulary, adding a capability only for a genuinely new,
        independently claimable host surface;
     4. identify the host capability claim/evidence impact;
     5. identify implemented-truth documentation that must be synchronized
        after implementation and verification.
   - If an implementing host must inspect another host's implementation source
     to determine observable Genia semantics, stop. Clarify the authoritative
     contract and add or repair shared evidence before host implementation
     resumes.
   - This obligation reuses R16. Do not create a parallel runner, protocol,
     evidence format, capability registry/profile system, semantic manifest, or
     Core IR mechanism merely to satisfy this process gate.
   - Answer the **MCP language-knowledge impact** question: does this change
     affect knowledge an MCP client should know about Genia
     (`genia_language_profile`)? If yes, the same change updates STATE, the
     `mcp_language_profile` registry in `docs/contract/semantic_facts.json`, and the
     generated block in `apps/mcp/mcp.genia`
     (`tools/gen_mcp_language_profile.py`); if no, record why.
   - Identify whether Python, C++, or both are affected. A semantic change must
     land first as shared contract/conformance work; then both hosts must
     implement it, or a temporary host gap must be documented before merge.
     Add or update shared spec/conformance tests wherever applicable.
   - Every temporary host gap recorded in `spec/known_host_gaps.json` must have
     a GitHub issue reference, short reason, affected host, affected tests or
     spec area, and removal condition. Do not add unowned skip-list entries.
3. Commit preflight
4. Run contract prompt
5. Commit contract
6. Run design prompt
7. Commit design
8. Run failing-test prompt
9. Commit failing tests
10. Run implementation prompt
11. Commit implementation
12. Run the **Code Quality & Maintainability Review** phase using
    [`code-maintainability-review.md`](code-maintainability-review.md), inspecting
    the implementation diff and affected call sites, not only the implementer's
    summary. Record the reviewer, evidence, findings, verdict, and follow-ups.
13. Resolve blocking maintainability findings and obtain a fresh review verdict;
    commit any necessary focused fixes. Do not proceed with a FAIL verdict.
14. Publish the maintainability-review handoff as a GitHub issue comment; commit any version-controlled review artifacts when applicable.
15. Run docs prompt
16. Commit docs
17. Run audit prompt (independent behavioral/documentation truth audit;
    maintainability review does not replace it)
18. Commit audit or audit fixes
19. Run the Doc Distillation prompt
20. Commit the updated docs

Do not merge until audit passes.

## Full regression in socket-restricted environments

Run both partitions on the first attempt:

```
uv run pytest -n auto -q -m "not loopback"
uv run pytest -n auto -q -m loopback
```

The second command requires local loopback socket permission. The two commands
together are equivalent to ordinary full-suite selection; neither partition
alone is full regression. Do not automatically skip loopback tests when socket
permission is unavailable.

## Resource envelope for external-host verification

Record CPU quota, available memory and competing work when investigating a
request timeout. Schedule compilation, documentation builds and semantic host
verification sequentially in a resource-limited workspace. Choose and record
`--host-jobs` for that envelope (for example, `--host-jobs 2` under a two-CPU
quota); concurrency does not change case discovery, expected results, the
default 10-second request deadline or outcome classification. A finite green
run does not prove determinism or explain an earlier timeout. Retain failures,
label diagnostic versus acceptance runs and do not repeat failures to replace
their outcomes with PASS.

## Temporary #1250 bounded acceptance workflow

`.github/workflows/issue-1250-acceptance.yml` is manual `workflow_dispatch`
only, on `issue-1250-acceptance-infrastructure`. An independent Claude review
and explicit maintainer authorization of the workflow commit must precede a
dispatch; the `authorized` input records the operator's acknowledgement, not
an approval substitute. Implementing or opening its draft PR does not authorize
a run. GitHub requires workflow registration on the default branch before manual
dispatch is available; registration/merge is a separate maintainer action, not
authorization to dispatch. Record the workflow SHA and authorization in #1250's
append-only ledger.
The test subjects are fixed at baseline `0b25d2b45722f4397fd712f2f4b8eb3ea294f6e5`
and candidate `e3562f620020023ea39c44273068872d6bc73fe6`; the infrastructure
checkout is the separately recorded dispatch SHA. No user-supplied subject ref,
secret binding, write permission or persisted checkout credential is used.

Two sequential, independently provisioned GitHub-hosted Ubuntu 24.04 jobs each
run G0 on unchanged main, both approved scratch negative controls, then G1
(focused 15, original 22, teardown 2, signals ×3). Both jobs must succeed before
G2 starts on another hosted runner; that runner repeats G0/negative controls
before the exact 24-node `-n 2` replay. No retries or best-of selection are made.
G1 boot IDs must differ; missing provenance blocks G2. Each gate uses a fresh
HOME/cache and a non-reaping PID 1 namespace with a 2-CPU/8-GiB cgroup limit.
Python 3.12.14 and uv 0.13.5 are fixed; each subject/scratch clone generates its
own lock and syncs with `--locked`. Lock digest and normalized installed freeze
must match the published repair evidence, or the job stops.

The R4 negative control reverses the exact reviewed fixture patch
`38eb980ee5fc95bdad45f197543861c2c2eb6046` in a disposable baseline clone; the
existing probe→session node must fail with `a launch left processes behind`.
The other clone neutralizes only the launcher's `child.send_signal(signum)`;
each of the three existing signal nodes must fail at its command-exit check.
These are deliberate, separately labeled detection checks, never acceptance
failures relabeled as passes. Original subject trees and test assertions are
unchanged. Unrelated failures, collection errors, skipped nodes, missing JUnit,
wrong membership/counts, undetected mutants or prerequisite failures block all
subsequent work in that job and dependent jobs. Namespace exit removes the
negative controls' intentionally unreaped descendants.

Artifacts (30-day retention) contain exact commands/exits, raw pytest logs,
JUnit, registered IDs, mutant diffs, lock files/digests, installed versions,
runner/image/workflow identity, boot ID, PID 1, cgroup limits and passive process
signal-mask/group/session snapshots, plus a SHA256 manifest. Do not upload the
whole environment or credentials. Archive durable evidence links and outcomes
in #1250 before artifacts expire. Failures before evidence capture remain
visible in the Actions job log and cannot qualify a gate. Tests retain their
existing child-stderr capture behavior; process snapshots do not intercept it.

G3–G5 and full GREEN are absent. Workflow success establishes only the bounded
executed gates; independent evidence review and any later authorization remain
required. It cannot explain historical executor signal behavior or change
`GENIA_STATE.md`, language semantics, capability claims or release acceptance.
