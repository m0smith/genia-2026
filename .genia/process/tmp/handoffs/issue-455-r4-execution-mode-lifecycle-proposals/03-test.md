# === GENIA TEST HANDOFF ===

CHANGE NAME: issue #455 r4-execution-mode-lifecycle-proposals
CHANGE SLUG: issue-455-r4-execution-mode-lifecycle-proposals
ISSUE: #455
TYPE: docs
BRANCH: docs/issue-455-r4-execution-mode-lifecycle-proposals
HANDOFF DIR: .genia/process/tmp/handoffs/issue-455-r4-execution-mode-lifecycle-proposals

GENIA_STATE.md is final authority.

---

## Branch

- Starting branch: `docs/issue-455-r4-execution-mode-lifecycle-proposals`
- Working branch: `docs/issue-455-r4-execution-mode-lifecycle-proposals`
- Branch status: already existed before this TEST phase; no branch was created in this phase
- Current branch was confirmed before edits.
- Work was not performed on `main`.

Note: the prompt listed `docs/process/03-test.md` as a required read, but that file is absent in this checkout. The TEST phase followed the attached prompt, AGENTS.md, source-of-truth docs, prior handoffs, and existing `tests/doc/` patterns.

---

## Files Changed

- `tests/doc/test_execution_mode_lifecycle_doc.py`
- `.genia/process/tmp/handoffs/issue-455-r4-execution-mode-lifecycle-proposals/03-test.md`

No implementation, runtime, production docs, semantic-facts JSON, CLI, parser, Core IR, prelude, host adapter, or native-test behavior files were changed.

---

## Tests Added

Added focused doc-contract tests for the missing issue #455 execution-mode lifecycle proposal document:

- `test_execution_mode_lifecycle_proposal_doc_exists_and_is_proposal_only`
- `test_execution_mode_lifecycle_doc_covers_current_execution_modes`
- `test_execution_mode_lifecycle_doc_defines_required_concepts`
- `test_execution_mode_lifecycle_doc_preserves_annotation_inertness`
- `test_execution_mode_lifecycle_doc_does_not_claim_implemented_runtime_behavior`
- `test_execution_mode_lifecycle_doc_uses_current_symbol_form_when_showing_symbols`

The tests require `docs/architecture/execution-mode-lifecycle.md` to exist and, once added in a later phase, to remain clearly proposal-only, cover command/file/pipe/REPL/spec-test execution modes, distinguish `ExecutionMode`, `LifecyclePlan`, and `LifecycleBinding`, preserve annotation inertness, avoid implemented-runtime claims, and use current symbol form such as `quote(command_mode)` instead of fake `:command_mode` syntax.

---

## Why The Tests Fail Before Docs Sync

The approved contract/design for issue #455 says the execution-mode lifecycle proposal should live at:

```text
docs/architecture/execution-mode-lifecycle.md
```

That file has not been added yet. The TEST phase intentionally stops at the missing-doc boundary and does not add the proposal document.

---

## Validation

Command run:

```bash
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run pytest -q tests/doc/test_execution_mode_lifecycle_doc.py
```

Result:

```text
6 failed in 0.12s
```

Concise failing excerpt:

```text
Failed: docs/architecture/execution-mode-lifecycle.md must exist as the R4 execution-mode lifecycle proposal document for issue #455
```

This is the intended failure for the TEST phase.

---

## Phase Boundary Confirmation

- No implementation work was done.
- No production/runtime behavior was changed.
- No docs sync was done beyond this required TEST handoff.
- No generalized lifecycle runner was added.
- No annotation execution was added.
- No `@setup` or `@teardown` behavior was added or claimed.
- No current CLI behavior was changed.

---

## Commit

Failing-test commit SHA: reported in the final TEST-phase response after the commit exists.

Commit message:

```text
test(lifecycle): add failing execution mode lifecycle proposal checks issue #455
```
