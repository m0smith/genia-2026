"""Focused coverage for roadmap publishing after issue #739 split the live roadmap.

The root roadmap remains the single top-level navigation entry. Its focused
children are staged from their repository sources, while unrelated strategy
files and the frozen pre-split archive remain unpublished.
"""

from __future__ import annotations

from pathlib import Path

import tools.stage_docs_for_mkdocs as stage_docs_for_mkdocs

ROOT = Path(__file__).resolve().parents[2]
ROADMAP_SOURCE = ROOT / "docs" / "strategy" / "release-roadmap.md"
STAGED_RELATIVE_PATH = "strategy/release-roadmap.md"
FOCUSED_ROADMAP_DOCS = [
    "docs/strategy/roadmap/README.md",
    "docs/strategy/roadmap/multi-host-conformance-policy.md",
    "docs/strategy/roadmap/r15.md",
    "docs/strategy/roadmap/r16-r19.md",
    "docs/strategy/roadmap/r20-r23.md",
    "docs/strategy/roadmap/sequence.md",
    "docs/strategy/roadmap/parking-lot.md",
]


def read_text(relpath: str) -> str:
    return (ROOT / relpath).read_text(encoding="utf-8")


def normalize(text: str) -> str:
    return " ".join(text.split()).lower()


def assert_contains(relpath: str, excerpts: list[str]) -> None:
    text = normalize(read_text(relpath))
    for excerpt in excerpts:
        assert normalize(excerpt) in text, f"{relpath} is missing required excerpt: {excerpt}"


def staged_path_for(relpath: str) -> Path:
    return stage_docs_for_mkdocs.STAGING_ROOT / Path(relpath).relative_to("docs")


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


def test_staging_publishes_live_roadmap_bundle_from_repository_sources() -> None:
    stage_docs_for_mkdocs.main()

    live_docs = ["docs/strategy/release-roadmap.md", *FOCUSED_ROADMAP_DOCS]
    for relpath in live_docs:
        staged_path = staged_path_for(relpath)
        assert staged_path.exists(), f"{relpath} was not staged for MkDocs"
        assert staged_path.read_text(encoding="utf-8") == read_text(relpath), (
            f"{relpath} must be staged verbatim from its repository source"
        )


def test_staging_excludes_frozen_archive_and_unapproved_strategy_documents() -> None:
    stage_docs_for_mkdocs.main()

    staged_strategy_dir = stage_docs_for_mkdocs.STAGING_ROOT / "strategy"
    top_level_names = sorted(p.name for p in staged_strategy_dir.glob("*.md"))
    assert top_level_names == ["release-roadmap.md"]

    staged_roadmap_dir = staged_strategy_dir / "roadmap"
    staged_roadmap_names = sorted(p.name for p in staged_roadmap_dir.glob("*.md"))
    assert staged_roadmap_names == [
        "README.md",
        "multi-host-conformance-policy.md",
        "parking-lot.md",
        "r15.md",
        "r16-r19.md",
        "r20-r23.md",
        "sequence.md",
    ]

    assert not (staged_roadmap_dir / "archive").exists(), (
        "the frozen pre-split roadmap is repository history, not live published roadmap content"
    )
