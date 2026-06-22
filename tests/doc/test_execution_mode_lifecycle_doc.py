from __future__ import annotations

import re
from pathlib import Path

import pytest


REPO = Path(__file__).resolve().parents[2]
PROPOSAL_DOC = REPO / "docs" / "architecture" / "execution-mode-lifecycle.md"


def normalize(text: str) -> str:
    return " ".join(text.casefold().split())


def read_proposal_doc() -> str:
    if not PROPOSAL_DOC.exists():
        pytest.fail(
            "docs/architecture/execution-mode-lifecycle.md must exist as the R4 "
            "execution-mode lifecycle proposal document for issue #455"
        )
    return PROPOSAL_DOC.read_text(encoding="utf-8")


def assert_contains_all(text: str, excerpts: list[str]) -> None:
    normalized = normalize(text)
    for excerpt in excerpts:
        assert normalize(excerpt) in normalized, (
            "execution-mode lifecycle proposal doc is missing required text: "
            f"{excerpt}"
        )


def test_execution_mode_lifecycle_proposal_doc_exists_and_is_proposal_only() -> None:
    text = read_proposal_doc()

    assert_contains_all(
        text,
        [
            "R4",
            "execution-mode lifecycle",
            "proposal",
            "not implemented",
            "GENIA_STATE.md",
            "final authority",
        ],
    )


def test_execution_mode_lifecycle_doc_covers_current_execution_modes() -> None:
    text = read_proposal_doc()

    assert_contains_all(
        text,
        [
            "command mode",
            "file mode",
            "pipe mode",
            "REPL mode",
            "spec/test execution mode",
        ],
    )

    required_phase_shapes = [
        "command_mode_lifecycle",
        "file_mode_lifecycle",
        "pipe_mode_lifecycle",
        "repl_mode_lifecycle",
        "spec_mode_lifecycle",
    ]
    assert_contains_all(text, required_phase_shapes)


def test_execution_mode_lifecycle_doc_defines_required_concepts() -> None:
    text = read_proposal_doc()

    assert_contains_all(
        text,
        [
            "ExecutionMode",
            "LifecyclePlan",
            "LifecycleBinding",
            "source/input acquisition",
            "context binding",
            "evaluation",
            "output/normalization",
            "cleanup/finalization",
        ],
    )


def test_execution_mode_lifecycle_doc_preserves_annotation_inertness() -> None:
    text = read_proposal_doc()

    assert_contains_all(
        text,
        [
            "annotations are inert",
            "annotations mark candidates",
            "lifecycle phases decide what runs",
            "annotations never execute themselves",
            "Only lifecycle phases with explicit bindings consume annotations",
        ],
    )


def test_execution_mode_lifecycle_doc_does_not_claim_implemented_runtime_behavior() -> None:
    text = read_proposal_doc()

    required_non_behaviors = [
        "no lifecycle runner",
        "no current CLI behavior changes",
        "no setup/teardown hook support is claimed as implemented",
        "@setup runs automatically",
        "@teardown runs automatically",
        "@route does not start a server",
    ]
    assert_contains_all(text, required_non_behaviors)

    forbidden_implemented_claims = [
        r"\bGenia runs execution-mode lifecycle phases\b",
        r"\bexecution modes use lifecycle plans\b",
        r"\b@setup runs\b",
        r"\b@teardown runs\b",
        r"\bgeneralized lifecycle runner is implemented\b",
        r"\bcurrent CLI behavior changes\b",
    ]
    for line_number, line in enumerate(text.splitlines(), start=1):
        normalized_line = normalize(line)
        allowed_context = any(
            marker in normalized_line
            for marker in [
                "not implemented",
                "not current",
                "no ",
                "does not",
                "must not",
                "proposal",
                "proposed",
                "future",
            ]
        )
        for pattern in forbidden_implemented_claims:
            if re.search(pattern, line, flags=re.IGNORECASE):
                assert allowed_context, (
                    "execution-mode lifecycle proposal must not imply implemented "
                    f"runtime behavior at line {line_number}: {line.strip()!r}"
                )


def test_execution_mode_lifecycle_doc_uses_current_symbol_form_when_showing_symbols() -> None:
    text = read_proposal_doc()

    assert ":command_mode" not in text
    assert ":file_mode" not in text
    assert ":pipe_mode" not in text
    assert_contains_all(
        text,
        [
            "quote(command_mode)",
            "quote(file_mode)",
            "quote(pipe_mode)",
        ],
    )
