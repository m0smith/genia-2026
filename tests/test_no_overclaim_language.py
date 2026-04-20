from __future__ import annotations

from pathlib import Path
import sys

import pytest

TESTS_DIR = Path(__file__).resolve().parent
if str(TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(TESTS_DIR))

from docs_truth_utils import REPO, display_path, strip_fenced_code


DOC_PATHS = [
    REPO / "GENIA_REPL_README.md",
    REPO / "GENIA_RULES.md",
    REPO / "GENIA_STATE.md",
    REPO / "README.md",
    *sorted((REPO / "docs").rglob("*.md")),
]
FORBIDDEN_PHRASES = [
    "no drift",
    "fully aligned",
    "all examples are valid",
    "complete coverage",
]
QUALIFYING_PHRASES = [
    "in reviewed sections",
    "in examined areas",
]


def assert_no_unqualified_overclaim_language(path: Path) -> None:
    stripped = strip_fenced_code(path.read_text(encoding="utf-8"))
    lines = stripped.splitlines()
    violations: list[str] = []

    for index, raw_line in enumerate(lines):
        lowered = raw_line.lower()
        for phrase in FORBIDDEN_PHRASES:
            if phrase not in lowered:
                continue
            window = "\n".join(lines[max(0, index - 1) : min(len(lines), index + 2)]).lower()
            if any(q in window for q in QUALIFYING_PHRASES):
                continue
            violations.append(
                f"{display_path(path)}:{index + 1}: unqualified overclaim phrase '{phrase}'"
            )

    assert not violations, "\n".join(violations)


@pytest.mark.parametrize("path", DOC_PATHS, ids=lambda p: str(p.relative_to(REPO)))
def test_docs_avoid_unqualified_overclaim_language(path: Path) -> None:
    if path.name == "AGENTS.md":
        pytest.skip("AGENTS.md intentionally lists banned phrases as policy examples")
    assert_no_unqualified_overclaim_language(path)


def test_overclaim_helper_allows_qualified_phrase(tmp_path: Path) -> None:
    doc = tmp_path / "doc.md"
    doc.write_text(
        "Coverage note: no drift in reviewed sections.\n",
        encoding="utf-8",
    )
    assert_no_unqualified_overclaim_language(doc)


def test_overclaim_helper_rejects_unqualified_phrase(tmp_path: Path) -> None:
    doc = tmp_path / "doc.md"
    doc.write_text(
        "Coverage note: fully aligned.\n",
        encoding="utf-8",
    )
    with pytest.raises(AssertionError, match="unqualified overclaim phrase"):
        assert_no_unqualified_overclaim_language(doc)
