from __future__ import annotations

import re
from pathlib import Path

import pytest


REPO = Path(__file__).resolve().parents[2]
LIFECYCLE_DOC = REPO / "docs" / "architecture" / "lifecycle.md"


def normalize(text: str) -> str:
    return " ".join(text.casefold().split())


def line_context_allows_non_goal_or_proposal(line: str) -> bool:
    normalized = normalize(line)
    allowed_markers = [
        "not implemented",
        "not current",
        "no ",
        "non-goal",
        "future",
        "proposed",
        "proposal",
        "avoid",
        "unless genia_state.md",
        "does not",
        "must not",
    ]
    return any(marker in normalized for marker in allowed_markers)


def read_lifecycle_doc() -> str:
    if not LIFECYCLE_DOC.exists():
        pytest.fail(
            "docs/architecture/lifecycle.md must exist as the permanent R4 lifecycle "
            "vocabulary and non-goals document"
        )
    return LIFECYCLE_DOC.read_text(encoding="utf-8")


def assert_contains_all(text: str, excerpts: list[str]) -> None:
    normalized = normalize(text)
    for excerpt in excerpts:
        assert normalize(excerpt) in normalized, f"lifecycle doc missing required contract text: {excerpt}"


def assert_mentions_words(text: str, label: str, words: list[str]) -> None:
    normalized = normalize(text)
    missing = [word for word in words if normalize(word) not in normalized]
    assert missing == [], f"lifecycle doc must define {label}; missing words: {missing}"


def test_lifecycle_architecture_doc_exists() -> None:
    lifecycle_doc_text = read_lifecycle_doc()
    assert lifecycle_doc_text.strip(), "lifecycle architecture doc must not be empty"


def test_lifecycle_doc_marks_status_and_truth_boundary() -> None:
    lifecycle_doc_text = read_lifecycle_doc()
    assert_contains_all(
        lifecycle_doc_text,
        [
            "R4",
            "lifecycle vocabulary",
            "non-goals",
            "not implemented runtime behavior",
            "GENIA_STATE.md",
            "final authority",
        ],
    )

    forbidden_claims = [
        "Genia supports lifecycle plans",
        "Genia runs lifecycle phases",
        "execution modes use lifecycle plans",
        "phase plans are executable",
    ]
    for line in lifecycle_doc_text.splitlines():
        for claim in forbidden_claims:
            if normalize(claim) in normalize(line):
                assert line_context_allows_non_goal_or_proposal(line), (
                    "lifecycle doc must not imply current lifecycle execution implementation: "
                    f"{line.strip()!r}"
                )


def test_lifecycle_doc_defines_required_vocabulary() -> None:
    lifecycle_doc_text = read_lifecycle_doc()
    required_terms = [
        "lifecycle",
        "lifecycle plan",
        "lifecycle phase",
        "lifecycle scope",
        "lifecycle binding",
        "lifecycle annotation binding",
        "lifecycle resource",
        "lifecycle cleanup",
        "lifecycle failure",
        "execution mode lifecycle",
        "test lifecycle",
        "module lifecycle",
    ]
    assert_contains_all(lifecycle_doc_text, required_terms)

    required_concept_words = {
        "lifecycle plan": ["phase", "scope", "ordering", "cleanup", "failure"],
        "lifecycle binding": ["phase", "candidate"],
        "lifecycle annotation binding": ["annotation", "candidate", "phase"],
        "lifecycle resource": ["resource", "ownership", "cleanup"],
        "lifecycle cleanup": ["entered scope", "cleanup", "chance"],
        "lifecycle failure": ["failure", "phase", "scope", "report"],
    }
    for label, words in required_concept_words.items():
        assert_mentions_words(lifecycle_doc_text, label, words)


def test_lifecycle_doc_locks_annotation_inertness() -> None:
    lifecycle_doc_text = read_lifecycle_doc()
    assert_contains_all(
        lifecycle_doc_text,
        [
            "annotations mark candidates",
            "lifecycle phases decide execution",
            "annotations do not execute merely because they exist",
            "imports",
            "loading",
            "must not auto-run lifecycle work",
        ],
    )


def test_lifecycle_doc_lists_explicit_r4_non_goals() -> None:
    lifecycle_doc_text = read_lifecycle_doc()
    non_goals = {
        "lifecycle runner implementation": ["no", "lifecycle runner", "implementation"],
        "runtime execution-mode refactor": ["no", "runtime", "execution-mode", "refactor"],
        "setup/teardown execution": ["no", "setup", "teardown", "execution"],
        "parser syntax changes": ["no", "parser", "syntax", "changes"],
        "Core IR changes": ["no", "Core IR", "changes"],
        "YAML lifecycle runner": ["no", "YAML", "lifecycle runner"],
        "server lifecycle implementation": ["no", "server lifecycle", "implementation"],
        "actor lifecycle implementation": ["no", "actor lifecycle", "implementation"],
        "plugin lifecycle implementation": ["no", "plugin lifecycle", "implementation"],
        "module instance lifecycle implementation": ["no", "module instance lifecycle", "implementation"],
        "hidden import/start behavior": ["no", "hidden", "import", "start", "behavior"],
    }
    for label, words in non_goals.items():
        assert_mentions_words(lifecycle_doc_text, label, words)


def test_lifecycle_doc_is_host_independent() -> None:
    lifecycle_doc_text = read_lifecycle_doc()
    assert_contains_all(
        lifecycle_doc_text,
        [
            "host-independent",
            "must not be defined as Python-only behavior",
        ],
    )


def test_docs_do_not_imply_implemented_lifecycle_behavior_without_state_authority() -> None:
    state_text = (REPO / "GENIA_STATE.md").read_text(encoding="utf-8")
    state_claims_lifecycle_plans_implemented = bool(
        re.search(r"implemented[^.\n]{0,80}lifecycle plan", state_text, re.IGNORECASE)
    )

    checked_docs = [
        "README.md",
        "GENIA_REPL_README.md",
        "docs/ai/LLM_CONTRACT.md",
        "docs/host-interop/HOST_INTEROP.md",
        "docs/host-interop/HOST_CAPABILITY_MATRIX.md",
    ]
    overclaim_patterns = [
        re.compile(r"\bGenia supports lifecycle plans\b", re.IGNORECASE),
        re.compile(r"\bGenia runs lifecycle phases\b", re.IGNORECASE),
        re.compile(r"\bexecution modes use lifecycle plans\b", re.IGNORECASE),
        re.compile(r"\b@setup runs\b", re.IGNORECASE),
        re.compile(r"\b@teardown runs\b", re.IGNORECASE),
        re.compile(r"\bserver lifecycle is supported\b", re.IGNORECASE),
        re.compile(r"\bactor lifecycle is supported\b", re.IGNORECASE),
        re.compile(r"\bphase plans are executable\b", re.IGNORECASE),
    ]

    unexpected_claims: list[str] = []
    for relpath in checked_docs:
        text = (REPO / relpath).read_text(encoding="utf-8")
        for line_number, line in enumerate(text.splitlines(), start=1):
            if line_context_allows_non_goal_or_proposal(line):
                continue
            for pattern in overclaim_patterns:
                if pattern.search(line):
                    unexpected_claims.append(f"{relpath}:{line_number}: {line.strip()}")

    assert state_claims_lifecycle_plans_implemented or unexpected_claims == [], (
        "Docs outside docs/architecture/lifecycle.md must not imply implemented lifecycle "
        "behavior unless GENIA_STATE.md reflects it:\n" + "\n".join(unexpected_claims)
    )
