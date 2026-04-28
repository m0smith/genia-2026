from __future__ import annotations

from pathlib import Path

import pytest


REPO = Path(__file__).resolve().parent.parent.parent
AGENTS_PATH = REPO / "AGENTS.md"
REQUIRED_HEADINGS = [
    "## Documentation Truth Model",
    "## Drift-Prevention Rules",
    "## Required Workflow for Any Change",
]
REQUIRED_EXCERPTS = [
    "Truth hierarchy:",
    "* no doc may claim more than `GENIA_STATE.md`",
    "* examples must include classification",
    "* host-only behavior must be labeled",
    "1. update `GENIA_STATE.md`",
    "5. run the relevant audit/validation",
]


def assert_truth_model_sections(text: str) -> None:
    for heading in REQUIRED_HEADINGS:
        assert heading in text, f"AGENTS.md is missing required heading: {heading}"
    for excerpt in REQUIRED_EXCERPTS:
        assert excerpt in text, f"AGENTS.md is missing required truth-model excerpt: {excerpt}"


def test_agents_contains_truth_model_and_workflow_guardrails() -> None:
    assert_truth_model_sections(AGENTS_PATH.read_text(encoding="utf-8"))


def test_truth_model_guardrail_helper_rejects_missing_sections() -> None:
    bad_text = """# AGENTS\n\n## Purpose\n\nNo workflow here.\n"""
    with pytest.raises(AssertionError, match="missing required heading"):
        assert_truth_model_sections(bad_text)
