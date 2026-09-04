"""Focused coverage for issue #697: publish docs/strategy/release-roadmap.md
on the MkDocs site from its single repository source, with a top-level
Roadmap navigation entry.

These tests fail if the roadmap stops being staged or disappears from
navigation, without hand-duplicating its content anywhere in the test.
"""

from __future__ import annotations

from pathlib import Path

import tools.stage_docs_for_mkdocs as stage_docs_for_mkdocs

ROOT = Path(__file__).resolve().parents[2]
ROADMAP_SOURCE = ROOT / "docs" / "strategy" / "release-roadmap.md"
STAGED_RELATIVE_PATH = "strategy/release-roadmap.md"


def read_text(relpath: str) -> str:
    return (ROOT / relpath).read_text(encoding="utf-8")


def normalize(text: str) -> str:
    return " ".join(text.split()).lower()


def assert_contains(relpath: str, excerpts: list[str]) -> None:
    text = normalize(read_text(relpath))
    for excerpt in excerpts:
        assert normalize(excerpt) in text, f"{relpath} is missing required excerpt: {excerpt}"


def test_mkdocs_nav_includes_top_level_roadmap_entry() -> None:
    assert_contains(
        "mkdocs.yml",
        [f"Roadmap: {STAGED_RELATIVE_PATH}"],
    )


def test_roadmap_source_still_carries_planning_disclaimer() -> None:
    assert ROADMAP_SOURCE.exists(), "docs/strategy/release-roadmap.md must exist to be staged"
    assert_contains(
        "docs/strategy/release-roadmap.md",
        [
            "Planning guide",
            "non-authoritative",
            "does not define implemented language behavior",
        ],
    )


def test_staging_publishes_roadmap_from_single_source_without_duplication() -> None:
    stage_docs_for_mkdocs.main()

    staged_path = stage_docs_for_mkdocs.STAGING_ROOT / STAGED_RELATIVE_PATH
    assert staged_path.exists(), (
        f"{STAGED_RELATIVE_PATH} was not staged by tools/stage_docs_for_mkdocs.py; "
        "docs/strategy/release-roadmap.md must be published through the existing "
        "staging workflow"
    )

    staged_text = staged_path.read_text(encoding="utf-8")
    source_text = ROADMAP_SOURCE.read_text(encoding="utf-8")
    assert staged_text == source_text, (
        "the staged roadmap page must be generated verbatim from "
        "docs/strategy/release-roadmap.md, not a hand-maintained copy"
    )


def test_staging_does_not_publish_other_strategy_documents() -> None:
    stage_docs_for_mkdocs.main()

    staged_strategy_dir = stage_docs_for_mkdocs.STAGING_ROOT / "strategy"
    staged_names = sorted(p.name for p in staged_strategy_dir.glob("*.md"))
    assert staged_names == ["release-roadmap.md"], (
        "only docs/strategy/release-roadmap.md is approved for publishing; found "
        f"{staged_names} staged under strategy/ instead"
    )
