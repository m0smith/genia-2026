from __future__ import annotations

import importlib
from pathlib import Path
import re
import sys

import pytest

TESTS_DIR = Path(__file__).resolve().parent
if str(TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(TESTS_DIR))

docs_truth_utils = importlib.import_module("docs_truth_utils")
REPO = docs_truth_utils.REPO
display_path = docs_truth_utils.display_path
read_text = docs_truth_utils.read_text
strip_fenced_code = docs_truth_utils.strip_fenced_code


TARGET_DOCS = [
    REPO / "README.md",
    REPO / "GENIA_REPL_README.md",
    *sorted((REPO / "docs" / "book").glob("*.md")),
    *sorted((REPO / "docs" / "cheatsheet").glob("*.md")),
    *sorted((REPO / "docs" / "sicp").glob("*.md")),
    *sorted((REPO / "docs" / "host-interop").glob("*.md")),
]
HOST_PATTERNS = [
    re.compile(r"\bstdin_keys\b", re.IGNORECASE),
    re.compile(r"\bserve_http\b", re.IGNORECASE),
    re.compile(r"http helper surface", re.IGNORECASE),
    re.compile(r"http server bridge", re.IGNORECASE),
    re.compile(r"`?rand\(\)`?", re.IGNORECASE),
    re.compile(r"`?rand_int\([^`\n]*\)`?", re.IGNORECASE),
    re.compile(r"`?sleep\([^`\n]*\)`?", re.IGNORECASE),
    re.compile(r"\bref_get\b|\bref_set\b|\bref_update\b", re.IGNORECASE),
    re.compile(r"\bspawn\([^`\n]*\)|`spawn`|\bprocess_alive\?\b", re.IGNORECASE),
]
QUALIFIER_RE = re.compile(r"python-host-only|python reference host", re.IGNORECASE)
CONTRACT_FILES = [
    REPO / "README.md",
    REPO / "GENIA_REPL_README.md",
    REPO / "docs" / "book" / "10-concurrency.md",
    REPO / "docs" / "book" / "15-reference-host-and-portability.md",
    REPO / "docs" / "cheatsheet" / "core.md",
    REPO / "docs" / "cheatsheet" / "quick-reference.md",
]


def assert_host_sensitive_terms_are_qualified(path: Path) -> None:
    stripped = strip_fenced_code(path.read_text(encoding="utf-8"))
    lines = stripped.splitlines()
    lowered = stripped.lower()
    file_has_global_qualifier = "python-host-only" in lowered or "python reference host" in lowered
    violations: list[str] = []

    for index, line in enumerate(lines):
        if not line.strip():
            continue
        for pattern in HOST_PATTERNS:
            if pattern.search(line) is None:
                continue
            start = max(0, index - 6)
            end = min(len(lines), index + 7)
            window = "\n".join(lines[start:end])
            if QUALIFIER_RE.search(window) or file_has_global_qualifier:
                continue
            violations.append(
                f"{display_path(path)}:{index + 1}: host-sensitive term lacks Python qualifier near: {line.strip()}"
            )

    assert not violations, "\n".join(violations)


@pytest.mark.parametrize("path", TARGET_DOCS, ids=lambda p: str(p.relative_to(REPO)))
def test_host_sensitive_doc_terms_are_qualified(path: Path) -> None:
    assert_host_sensitive_terms_are_qualified(path)


@pytest.mark.parametrize("path", CONTRACT_FILES, ids=lambda p: str(p.relative_to(REPO)))
def test_portability_facing_docs_use_contract_and_reference_host_labels(path: Path) -> None:
    text = read_text(path)
    assert "LANGUAGE CONTRACT:" in text, f"{display_path(path)} is missing LANGUAGE CONTRACT wording"
    assert "PYTHON REFERENCE HOST:" in text, (
        f"{display_path(path)} is missing PYTHON REFERENCE HOST wording"
    )


def test_host_boundary_helper_rejects_unqualified_host_feature(tmp_path: Path) -> None:
    doc = tmp_path / "doc.md"
    doc.write_text(
        """# Demo

This section documents `rand()` and `sleep(ms)` helpers.
""",
        encoding="utf-8",
    )

    with pytest.raises(AssertionError, match="host-sensitive term lacks Python qualifier"):
        assert_host_sensitive_terms_are_qualified(doc)
