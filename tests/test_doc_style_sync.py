"""Tests enforcing synchronization between the @doc style guide, book, cheatsheets, and linter.

Run all doc-style validation tests:
    pytest tests/test_doc_style_sync.py -v
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

import pytest

# Make the tools directory importable for lint_doc
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

from lint_doc import (
    ALLOWED_SECTION_HEADERS,
    ALLOWED_FENCE_LANGS,
    BEHAVIOR_TOKENS,
    DISCOURAGED_PREFIXES,
    lint_doc,
    Severity,
)

REPO = Path(__file__).resolve().parent.parent
STYLE_GUIDE = REPO / "docs" / "style" / "doc-style.md"
BOOK_FUNCTIONS = REPO / "docs" / "book" / "03-functions.md"
CHEATSHEET_CORE = REPO / "docs" / "cheatsheet" / "core.md"
CHEATSHEET_QUICK = REPO / "docs" / "cheatsheet" / "quick-reference.md"
PRELUDE_DIR = REPO / "src" / "genia" / "std" / "prelude"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


FENCE_RE = re.compile(r"^```(\w*)\s*$", re.MULTILINE)


def extract_genia_fences(md_text: str) -> list[str]:
    """Extract code blocks marked as ```genia from Markdown text."""
    blocks: list[str] = []
    lines = md_text.split("\n")
    in_fence = False
    fence_lang = ""
    current: list[str] = []

    for line in lines:
        if not in_fence:
            m = re.match(r"^```(\w*)\s*$", line)
            if m:
                in_fence = True
                fence_lang = m.group(1)
                current = []
        else:
            if re.match(r"^```\s*$", line):
                if fence_lang == "genia":
                    blocks.append("\n".join(current))
                in_fence = False
                current = []
            else:
                current.append(line)
    return blocks


# ===========================================================================
# 1) Style guide structure test
# ===========================================================================

class TestStyleGuideStructure:
    """Validate that docs/style/doc-style.md has the required canonical sections."""

    @pytest.fixture(autouse=True)
    def _load(self):
        self.text = read_text(STYLE_GUIDE)

    def test_required_sections_exist(self):
        required = [
            "## 1. Purpose",
            "## 2. Supported Format",
            "## 3. Markdown Support (Strict Subset)",
            "## 4. Required Structure Rules",
            "## 5. Standard Sections",
            "## 6. Examples (Good vs Bad)",
            "## 7. When To Use `@doc`",
            "## 8. Style Principles",
        ]
        for section in required:
            assert section in self.text, f"Missing required section: {section}"

    def test_good_examples_exist(self):
        assert "Good: short doc" in self.text
        assert "Good: structured doc" in self.text
        assert "Good: pipeline / Option-aware doc" in self.text

    def test_bad_examples_exist(self):
        assert "Bad: long rambling prose" in self.text
        assert "Bad: leading filler" in self.text
        assert "Bad: implementation detail" in self.text
        assert "Bad: missing failure behavior" in self.text

    def test_allowed_section_headers_listed(self):
        """The style guide must list every allowed section header from the linter."""
        for header in ALLOWED_SECTION_HEADERS:
            # The style guide lists them as `## Arguments` etc in bullet items
            section_name = header.replace("## ", "")
            assert f"`## {section_name}`" in self.text, (
                f"Style guide missing allowed section header: {header}"
            )

    def test_genia_fences_are_well_formed(self):
        """Every ```genia block in the style guide should contain @doc or function-like syntax."""
        blocks = extract_genia_fences(self.text)
        assert len(blocks) > 0, "Style guide should have at least one genia code block"
        for i, block in enumerate(blocks):
            stripped = block.strip()
            assert len(stripped) > 0, f"Genia block {i} in style guide is empty"
            # Each block should contain at least something that looks like Genia:
            # @doc, a function def (->), assignment (=), or a call
            has_content = (
                "@doc" in stripped
                or "->" in stripped
                or "=" in stripped
                or "(" in stripped
            )
            assert has_content, (
                f"Genia block {i} in style guide doesn't look like valid Genia content:\n{stripped[:120]}"
            )


# ===========================================================================
# 2) Cheatsheet sync test
# ===========================================================================

class TestCheatsheetDocSync:
    """Validate @doc quick-reference sections in cheatsheets match the style guide."""

    def test_core_cheatsheet_has_doc_section(self):
        text = read_text(CHEATSHEET_CORE)
        assert "### `@doc` Quick Reference" in text or "### @doc Quick Reference" in text, (
            "docs/cheatsheet/core.md should have a @doc Quick Reference section"
        )

    def test_quick_reference_cheatsheet_has_doc_section(self):
        text = read_text(CHEATSHEET_QUICK)
        assert "## `@doc` Quick Reference" in text or "## @doc Quick Reference" in text, (
            "docs/cheatsheet/quick-reference.md should have a @doc Quick Reference section"
        )

    def test_core_cheatsheet_links_to_style_guide(self):
        text = read_text(CHEATSHEET_CORE)
        assert "doc-style.md" in text, (
            "docs/cheatsheet/core.md should reference docs/style/doc-style.md"
        )

    def test_quick_reference_cheatsheet_links_to_style_guide(self):
        text = read_text(CHEATSHEET_QUICK)
        assert "doc-style.md" in text, (
            "docs/cheatsheet/quick-reference.md should reference docs/style/doc-style.md"
        )

    def test_core_cheatsheet_doc_syntax_matches(self):
        """The @doc syntax shown in cheatsheets must match the implemented syntax."""
        text = read_text(CHEATSHEET_CORE)
        # Must show single-line @doc "..." syntax
        assert '@doc "' in text, "core cheatsheet must show single-line @doc syntax"

    def test_quick_reference_doc_syntax_matches(self):
        text = read_text(CHEATSHEET_QUICK)
        assert '@doc "' in text, "quick-reference cheatsheet must show single-line @doc syntax"

    def test_core_cheatsheet_case_markers_present(self):
        """Cheatsheet runnable examples must have [case: ...] markers per AGENTS.md rules."""
        text = read_text(CHEATSHEET_CORE)
        # Find @doc section and check for case markers nearby
        if "@doc Quick Reference" in text:
            # The section should have at least one case marker
            marker_re = re.compile(r"\[case:\s*[a-z0-9-]+\]")
            markers = marker_re.findall(text)
            assert len(markers) > 0, (
                "Core cheatsheet @doc examples should have [case: ...] markers"
            )

    def test_quick_reference_cheatsheet_case_markers_present(self):
        text = read_text(CHEATSHEET_QUICK)
        if "@doc Quick Reference" in text:
            marker_re = re.compile(r"\[case:\s*[a-z0-9-]+\]")
            markers = marker_re.findall(text)
            assert len(markers) > 0, (
                "Quick-reference cheatsheet @doc examples should have [case: ...] markers"
            )


# ===========================================================================
# 3) Book sync test
# ===========================================================================

class TestBookDocSync:
    """Validate that docs/book/03-functions.md @doc content matches the style guide."""

    @pytest.fixture(autouse=True)
    def _load(self):
        self.book_text = read_text(BOOK_FUNCTIONS)
        self.style_text = read_text(STYLE_GUIDE)

    def test_book_has_documenting_functions_section(self):
        assert "## Documenting Functions" in self.book_text

    def test_book_links_to_style_guide(self):
        assert "doc-style.md" in self.book_text, (
            "Book chapter 03 should link to docs/style/doc-style.md"
        )

    def test_book_markdown_subset_matches_style_guide(self):
        """The Markdown subset described in the book must match the style guide."""
        style = self.style_text
        book = self.book_text

        # The style guide's allowed list in section 3
        style_allowed = [
            "paragraphs",
            "blank lines",
            "bullet lists",
            "inline code",
            "fenced code blocks",
        ]
        for item in style_allowed:
            assert item in book, (
                f"Book's Markdown subset section should mention '{item}'"
            )

        # The style guide's disallowed list
        style_disallowed = ["HTML", "tables", "images"]
        for item in style_disallowed:
            assert item in book, (
                f"Book's Markdown subset section should mention disallowed '{item}'"
            )

    def test_book_allowed_section_headers_consistent(self):
        """Book prose mentioning allowed @doc section headers must be a subset of the style guide."""
        book = self.book_text
        # The book mentions headings like `## Arguments` and `## Returns`
        # Extract all `## SomeName` references from the book's Markdown subset section
        heading_refs = re.findall(r'`(## \w+)`', book)
        style_names = {h.replace("## ", "") for h in ALLOWED_SECTION_HEADERS}
        for ref in heading_refs:
            name = ref.replace("## ", "")
            assert name in style_names, (
                f"Book references section header '{ref}' but it's not in the "
                f"style guide's allowed set: {ALLOWED_SECTION_HEADERS}"
            )

    def test_book_doc_style_guide_section_exists(self):
        """Book should have a redirect section pointing to the canonical style guide."""
        assert "## `@doc` Style Guide" in self.book_text or "## @doc Style Guide" in self.book_text


# ===========================================================================
# 4) Source doc lint sweep
# ===========================================================================

class TestPreludeDocLintSweep:
    """Run the linter over any @doc strings found in prelude .genia files.

    This is a best-effort sweep. Since prelude files currently have zero @doc
    annotations, this test validates the infrastructure works and will catch
    future regressions when @doc strings are added.
    """

    DOC_RE = re.compile(r'@doc\s+"""(.*?)"""', re.DOTALL)
    SINGLE_DOC_RE = re.compile(r'@doc\s+"([^"]*)"(?!")')

    @staticmethod
    def _extract_docs(path: Path) -> list[tuple[int, str]]:
        content = path.read_text(encoding="utf-8")
        docs = []
        for m in TestPreludeDocLintSweep.DOC_RE.finditer(content):
            line = content[:m.start()].count("\n") + 1
            docs.append((line, m.group(1)))
        for m in TestPreludeDocLintSweep.SINGLE_DOC_RE.finditer(content):
            line = content[:m.start()].count("\n") + 1
            docs.append((line, m.group(1)))
        return docs

    def test_prelude_files_exist(self):
        assert PRELUDE_DIR.is_dir(), f"Prelude directory not found: {PRELUDE_DIR}"
        genia_files = list(PRELUDE_DIR.glob("*.genia"))
        assert len(genia_files) > 0, "No .genia files in prelude directory"

    def test_prelude_docs_pass_linter(self):
        """Every @doc in prelude files must pass the linter with no errors."""
        genia_files = sorted(PRELUDE_DIR.glob("*.genia"))
        all_findings: list[str] = []

        for path in genia_files:
            docs = self._extract_docs(path)
            for file_line, text in docs:
                findings = lint_doc(text)
                errors = [f for f in findings if f.severity == Severity.ERROR]
                for f in errors:
                    loc = f":{f.line}" if f.line else ""
                    all_findings.append(f"{path.name}:{file_line}{loc}: {f}")

        if all_findings:
            msg = "Prelude @doc lint errors:\n" + "\n".join(all_findings)
            pytest.fail(msg)


# ===========================================================================
# 5) Linter constants match style guide
# ===========================================================================

class TestLinterStyleGuideAlignment:
    """Ensure the linter's hardcoded constants match what the style guide documents."""

    @pytest.fixture(autouse=True)
    def _load(self):
        self.text = read_text(STYLE_GUIDE)

    def test_allowed_sections_match(self):
        """Every section header in the linter's ALLOWED_SECTION_HEADERS must appear in the style guide."""
        for header in ALLOWED_SECTION_HEADERS:
            name = header.replace("## ", "")
            assert f"`## {name}`" in self.text, (
                f"Linter allows section '{header}' but style guide doesn't list it"
            )

    def test_discouraged_prefixes_documented(self):
        """The style guide's Bad examples should cover the linter's discouraged prefixes."""
        lower_text = self.text.lower()
        # The "This function" prefix should appear in a bad example
        assert "this function" in lower_text, (
            "Style guide should show 'This function' as a bad example"
        )

    def test_disallowed_markdown_documented(self):
        """Style guide must list HTML and tables as disallowed."""
        assert "HTML" in self.text
        assert "tables" in self.text.lower()

    def test_linter_section_exists(self):
        """Style guide should document the automated linter."""
        assert "## 9. Automated Linter" in self.text
