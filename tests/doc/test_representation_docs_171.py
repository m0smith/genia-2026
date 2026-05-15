from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def read_text(relpath: str) -> str:
    return (ROOT / relpath).read_text(encoding="utf-8")


def normalize(text: str) -> str:
    return " ".join(text.split()).lower()


def assert_contains(relpath: str, excerpts: list[str]) -> None:
    text = normalize(read_text(relpath))
    for excerpt in excerpts:
        assert normalize(excerpt) in text, f"{relpath} is missing required excerpt: {excerpt}"


def test_representation_system_doc_page_exists_and_covers_contract() -> None:
    relpath = "docs/design/representation-system-and-format.md"
    path = ROOT / relpath

    assert path.exists(), f"{relpath} must document issue #171 representation behavior"

    assert_contains(
        relpath,
        [
            "Representation renders values as strings for output and debugging",
            "Representation does not change value identity",
            "Value templates describe or constrain values",
            "Formats describe output strings",
            "`display(value)` returns a user-facing representation string without writing output",
            "`debug_repr(value)` returns a debug representation string without writing output",
            "`format(template_or_format, values)` returns a string",
            "Named placeholders use map values",
            "Positional placeholders use list values",
            "Escaped braces use `{{` and `}}`",
            "`Format(template)`",
            "Experimental",
            "Tags are metadata only",
            "Localization",
            "Interpolation syntax",
        ],
    )


def test_representation_doc_page_includes_required_examples() -> None:
    relpath = "docs/design/representation-system-and-format.md"
    path = ROOT / relpath

    assert path.exists(), f"{relpath} must exist before required examples can be verified"

    assert_contains(
        relpath,
        [
            'format("Hello {name}!", {name: "Alice"})',
            '"Hello Alice!"',
            'format("Item {0} costs {1}", ["apple", "5"])',
            '"Item apple costs 5"',
            'format("{{key}} = {0}", ["value"])',
            '"{key} = value"',
            'format("{0} | {1} | {2}", ["X", "O", "X"])',
            '"X | O | X"',
            'format("Hello {name}!", {greeting: "Hi"})',
            "Error: format missing field: name",
        ],
    )


def test_mkdocs_nav_includes_representation_system_page() -> None:
    assert_contains(
        "mkdocs.yml",
        ["Representation System and Format: design/representation-system-and-format.md"],
    )


def test_authoritative_docs_capture_representation_boundaries() -> None:
    required = [
        "representation does not change value identity",
        "`format(template_or_format, values)` returns a string",
        "does not write output",
        "does not mutate",
        "`Format` is for output representation",
        "`Format` is separate from value templates",
    ]

    assert_contains("GENIA_STATE.md", required)
    assert_contains("GENIA_REPL_README.md", required)


def test_core_cheatsheet_covers_required_representation_examples() -> None:
    assert_contains(
        "docs/cheatsheet/core.md",
        [
            "`display`, `debug_repr`, and `format` return strings",
            "`Format(template)`",
            "Experimental",
            "does not affect value identity",
            'format("Hello {name}!", {name: "Alice"})',
            'format("Item {0} costs {1}", ["apple", "5"])',
            'format("{{key}} = {0}", ["value"])',
            'format("{0} | {1} | {2}", ["X", "O", "X"])',
            "Error: format missing field: name",
        ],
    )

