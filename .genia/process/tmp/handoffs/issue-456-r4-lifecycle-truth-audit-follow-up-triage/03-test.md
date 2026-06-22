# 03-test — issue #456 r4-lifecycle-truth-audit-follow-up-triage

CHANGE NAME: issue #456 r4-lifecycle-truth-audit-follow-up-triage
CHANGE SLUG: issue-456-r4-lifecycle-truth-audit-follow-up-triage
ISSUE: #456
TYPE: docs / audit-triage
BRANCH: docs/issue-456-r4-lifecycle-truth-audit-follow-up-triage
HANDOFF_DIR: .genia/process/tmp/handoffs/issue-456-r4-lifecycle-truth-audit-follow-up-triage

GENIA_STATE.md is final authority.

HARD STOP:
TEST phase only. No audit artifact was implemented. No production docs, runtime, parser, evaluator, CLI, Flow, lifecycle implementation, Core IR, or GitHub issue state was changed.

---

## 0. Branch

Starting branch:
- docs/issue-456-r4-lifecycle-truth-audit-follow-up-triage

Working branch:
- docs/issue-456-r4-lifecycle-truth-audit-follow-up-triage

Branch existence:
- The required branch already existed at the start of this TEST phase and was already checked out.

---

## 1. Files Changed

- tests/doc/test_issue_456_lifecycle_truth_audit_triage.py
- .genia/process/tmp/handoffs/issue-456-r4-lifecycle-truth-audit-follow-up-triage/03-test.md

---

## 2. Tests Added

Added a focused doc test file for the issue #456 audit/triage artifact:

- requires the approved next-phase artifact path:
  - .genia/process/tmp/handoffs/issue-456-r4-lifecycle-truth-audit-follow-up-triage/03-audit.md
- requires stable audit sections from the approved design
- requires a verdict label of PASS, PASS WITH ISSUES, or FAIL
- requires issue triage to distinguish closure candidates from follow-up candidates
- requires findings to include status/category/evidence/recommended-action fields
- requires authoritative evidence markers and references
- forbids claims of newly implemented lifecycle behavior
- forbids performed or automatic GitHub issue mutations
- preserves the issue #455 execution-mode lifecycle proposal boundary
- requires recommended follow-ups to be proposed actions, not performed actions

---

## 3. Commands Run

Expected failing TEST command:

```bash
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run pytest -q tests/doc/test_issue_456_lifecycle_truth_audit_triage.py
```

Result:
- 8 failed in 0.12s

Failing output excerpt:

```text
Failed: issue #456 audit/triage handoff must exist at .genia/process/tmp/handoffs/issue-456-r4-lifecycle-truth-audit-follow-up-triage/03-audit.md
```

Nearest existing related doc tests:

```bash
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run pytest -q tests/doc/test_lifecycle_architecture_doc.py tests/doc/test_execution_mode_lifecycle_doc.py tests/doc/test_semantic_doc_sync.py
```

Result:
- 98 passed in 0.43s

---

## 4. Expected Failure Confirmation

The new test failure is expected and useful.

Reason:
- The TEST phase intentionally did not create .genia/process/tmp/handoffs/issue-456-r4-lifecycle-truth-audit-follow-up-triage/03-audit.md.
- The next phase must implement the audit/triage artifact at that path and satisfy the contract asserted by the test.

No implementation, docs-sync, audit/truth-review, or GitHub issue mutation work was performed.

---

## 5. Next Recommended Phase

Next phase:
- implementation of the audit/triage artifact only

Next output:
- .genia/process/tmp/handoffs/issue-456-r4-lifecycle-truth-audit-follow-up-triage/03-audit.md

Boundaries:
- Do not change runtime behavior.
- Do not edit production docs unless a later phase explicitly requests docs-sync/fix work.
- Do not close, relabel, comment on, or create GitHub issues.
- Record recommended issue actions as proposed actions only.
