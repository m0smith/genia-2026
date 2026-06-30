"""Issue #456 — R4 lifecycle truth-audit guardrail.

This test verifies the *truth boundary* that issue #456 audited: that Genia's
R4 lifecycle work remains proposal/vocabulary only and is not claimed as
implemented runtime behavior, with ``GENIA_STATE.md`` as final authority.

Earlier this guardrail was wired to a local audit handoff file under the
gitignored process scratch tree (see ``.gitignore``). That tree is process
scratch space; it is not a source of truth and must never be required as
committed test input. The check below re-expresses the same guardrail against
committed, authoritative repository files only:

* ``GENIA_STATE.md`` (final authority)
* ``GENIA_RULES.md`` (annotation invariants)
* ``docs/architecture/lifecycle.md`` (proposed lifecycle vocabulary)
* ``docs/architecture/execution-mode-lifecycle.md`` (#455 proposal doc)
* the committed lifecycle/semantic guardrail test modules

A regression test at the bottom asserts this module no longer depends on the
process scratch tree.
"""

from __future__ import annotations

import re
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]

STATE_DOC = REPO / "GENIA_STATE.md"
RULES_DOC = REPO / "GENIA_RULES.md"
LIFECYCLE_DOC = REPO / "docs" / "architecture" / "lifecycle.md"
EXECUTION_MODE_DOC = REPO / "docs" / "architecture" / "execution-mode-lifecycle.md"

COMMITTED_GUARDRAIL_TESTS = [
    REPO / "tests" / "doc" / "test_lifecycle_architecture_doc.py",
    REPO / "tests" / "doc" / "test_execution_mode_lifecycle_doc.py",
    REPO / "tests" / "doc" / "test_semantic_doc_sync.py",
]


def normalize(text: str) -> str:
    return " ".join(text.casefold().split())


def read_committed(path: Path) -> str:
    assert path.exists(), f"required committed source must exist: {path.relative_to(REPO)}"
    text = path.read_text(encoding="utf-8")
    assert text.strip(), f"required committed source must not be empty: {path.relative_to(REPO)}"
    return text


def assert_contains_all(text: str, excerpts: list[str], source_label: str) -> None:
    normalized = normalize(text)
    for excerpt in excerpts:
        assert normalize(excerpt) in normalized, (
            f"{source_label} is missing required lifecycle-truth text: {excerpt!r}"
        )


def test_issue_456_state_is_final_authority_for_lifecycle_truth() -> None:
    text = read_committed(STATE_DOC)

    assert_contains_all(
        text,
        [
            "GENIA_STATE.md is the final authority for implemented behavior",
            "No lifecycle runner behavior is implemented.",
            "No setup/teardown behavior is implemented.",
        ],
        "GENIA_STATE.md",
    )


def test_issue_456_lifecycle_doc_keeps_proposal_vs_current_boundary() -> None:
    text = read_committed(LIFECYCLE_DOC)

    assert_contains_all(
        text,
        [
            "not implemented runtime behavior",
            "Generalized lifecycle plan execution is not implemented runtime behavior.",
            "Lifecycle runners are not implemented runtime behavior.",
            "Setup/teardown lifecycle hooks are not implemented runtime behavior.",
            "Generalized annotation binding execution is not implemented runtime behavior.",
            "no lifecycle runner implementation",
            "no annotation execution behavior",
        ],
        "docs/architecture/lifecycle.md",
    )


def test_issue_456_execution_mode_doc_remains_proposal_only() -> None:
    # Preserves the issue #455 dependency boundary: execution-mode lifecycle
    # is proposal documentation, not an implemented runner refactor.
    text = read_committed(EXECUTION_MODE_DOC)

    assert_contains_all(
        text,
        [
            "execution-mode lifecycle",
            "proposal",
            "not implemented",
            "no lifecycle runner",
            "GENIA_STATE.md",
            "final authority",
        ],
        "docs/architecture/execution-mode-lifecycle.md",
    )


def test_issue_456_annotations_remain_inert_metadata() -> None:
    rules = read_committed(RULES_DOC)
    lifecycle = read_committed(LIFECYCLE_DOC)

    assert_contains_all(
        rules,
        [
            "annotation metadata behavior is currently implemented only for",
            "no annotation introduces macros, compile-time transforms, or syntax rewriting",
        ],
        "GENIA_RULES.md",
    )
    assert_contains_all(
        lifecycle,
        [
            "Annotations mark candidates. Lifecycle phases decide execution.",
            "Annotations do not execute merely because they exist.",
            "Imports and loading must not auto-run lifecycle work.",
        ],
        "docs/architecture/lifecycle.md",
    )


def test_issue_456_committed_lifecycle_guardrail_tests_exist() -> None:
    # The audit's "test/doc guardrail check" section depended on these
    # committed guardrail modules. Assert they remain present and non-empty.
    for path in COMMITTED_GUARDRAIL_TESTS:
        assert path.exists(), (
            "committed lifecycle/semantic guardrail test must exist: "
            f"{path.relative_to(REPO)}"
        )
        assert path.read_text(encoding="utf-8").strip(), (
            f"committed guardrail test must not be empty: {path.relative_to(REPO)}"
        )


def test_issue_456_lifecycle_proposal_docs_do_not_claim_implemented_behavior() -> None:
    # Re-expression of the original forbidden-claims guardrail, now run over the
    # committed proposal docs whose job is to maintain the proposal/not-implemented
    # boundary (rather than over a scratch handoff file).
    forbidden_claims = [
        r"\bimplemented lifecycle system\b",
        r"\bgeneralized lifecycle runner is implemented\b",
        r"\bexecution-mode lifecycle runner exists\b",
        r"\bGenia runs lifecycle phases\b",
        r"\bannotations run setup/teardown hooks\b",
        r"\b@setup runs automatically\b",
        r"\b@teardown runs automatically\b",
    ]
    allowed_context = re.compile(
        r"not implemented|not current|no |does not|must not|proposal|proposed|future",
        re.IGNORECASE,
    )
    for path in (LIFECYCLE_DOC, EXECUTION_MODE_DOC):
        text = read_committed(path)
        for line_number, line in enumerate(text.splitlines(), start=1):
            for pattern in forbidden_claims:
                if re.search(pattern, line, flags=re.IGNORECASE):
                    assert allowed_context.search(line), (
                        f"{path.relative_to(REPO)} must not claim implemented "
                        f"lifecycle behavior at line {line_number}: {line.strip()!r}"
                    )


def test_issue_456_test_has_no_process_scratch_dependency() -> None:
    # Regression guard: this module must not reintroduce a dependency on the
    # gitignored process scratch directory as required test input. The needles
    # are assembled at runtime so this assertion does not match itself.
    source = Path(__file__).read_text(encoding="utf-8")
    scratch_dir = ".genia/process/" + "tmp"
    handoff_word = "hand" + "offs"
    assert scratch_dir not in source, (
        "tests must never require gitignored process scratch files as input "
        f"(found reference to {scratch_dir!r})"
    )
    assert handoff_word not in source, (
        "tests must never require process handoff scratch files as input"
    )
