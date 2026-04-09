from pathlib import Path


BOOK_CHAPTERS = sorted(
    path
    for path in Path("docs/book").glob("*.md")
    if path.name != "CHAPTER_TEMPLATE.md"
)
REQUIRED_MARKERS = ("✅", "⚠️", "❌")


def test_book_chapters_include_status_markers():
    assert BOOK_CHAPTERS, "expected docs/book chapters to validate"

    for path in BOOK_CHAPTERS:
        text = path.read_text(encoding="utf-8")
        missing = [marker for marker in REQUIRED_MARKERS if marker not in text]
        assert not missing, f"{path} is missing status markers: {', '.join(missing)}"
