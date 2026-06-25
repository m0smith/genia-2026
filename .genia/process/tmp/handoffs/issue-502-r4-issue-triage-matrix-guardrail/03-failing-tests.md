# 03-failing-tests - issue #502 r4-issue-triage-matrix-guardrail

CHANGE NAME: issue #502 r4-issue-triage-matrix-guardrail
CHANGE SLUG: issue-502-r4-issue-triage-matrix-guardrail
ISSUE: #502
TYPE: feature (doc-test guardrail)
BRANCH: feature/issue-502-r4-issue-triage-matrix-guardrail

GENIA_STATE.md is final authority.

## 0. Branch check

- Current branch: feature/issue-502-r4-issue-triage-matrix-guardrail
- Required branch: feature/issue-502-r4-issue-triage-matrix-guardrail
- Not on main: YES

## 1. Test plan

Files added:
- tests/doc/test_r4_issue_triage_matrix.py

Behavior groups covered:
- Pinned seven-column triage table header.
- At least one parsed table data row.
- Per-row recognized `Classification` labels.
- Per-row recognized `Recommended action` labels.
- Per-row `Action taken?` normalized to `NO`.

Explicit omissions:
- Optional live `gh issue view` check omitted in this phase.
- No GitHub issue mutation.
- No production source changes.
- No production docs changes.
- No edits to the #456 audit artifact.
- No pytest markers, plugins, or CI config.

## 2. Required coverage

Happy path:
- The committed #456 audit artifact's section 9 triage table parses and satisfies
  the contract.

Edge cases:
- Markdown emphasis/backticks around labels are tolerated during normalization.
- Table parsing stops at the first non-pipe line after the table.
- Range issue rows such as `#345-#356` are treated the same as single-issue rows
  in the structural checks.

Failure cases guarded:
- Missing audit artifact.
- Missing or renamed pinned header.
- Zero parsed rows.
- A malformed row with the wrong cell count.
- An unrecognized classification.
- An unrecognized recommended action.
- Any `Action taken?` value other than `NO`.

## 3. Execution

Command run:

```bash
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run pytest -q tests/doc/test_r4_issue_triage_matrix.py -v
```

Result:
- PASS: 5 passed in 0.06s.

Adjacent guardrail command run:

```bash
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run pytest -q tests/doc/test_issue_456_lifecycle_truth_audit_triage.py -v
```

Result:
- PASS: 8 passed in 0.06s.

## 4. Failure evidence

Expected failing tests:
- None.

Reason:
- The issue #502 contract and design state that the new structural guardrail
  should pass against the current committed #456 audit artifact. Creating a
  deliberate red state would require changing or invalidating the #456 artifact,
  which the phase explicitly forbids.

Observed evidence:
- `tests/doc/test_r4_issue_triage_matrix.py` collected 5 tests and all passed.
- Adjacent #456 guardrail collected 8 tests and all passed.

Phase note:
- The branch handoff directory uses `03-failing-tests.md`, while the operator
  prompt requested `03-test.md`. This file records the branch-local process path;
  `03-test.md` mirrors this content for the prompt-requested path.

## 5. Ambiguities / blockers

- `docs/process/03-test.md` does not exist on this branch. The matching local
  process file is `docs/process/04-test.md`, and the handoff README lists
  `03-failing-tests.md`.
- The "failing-test phase" wording conflicts with the approved #502 contract's
  "test passes against the current committed artifact" expectation. This phase
  follows the contract and preserves the no-edit/no-mutation guardrails.
