"""Guard maintained Sheet diagnostic/CSV summaries against existing executable truth.

The shared unequal-length fixture and existing R22 scalar tests remain behavioral
evidence. These focused text checks catch documented contradictions without
claiming general prose completeness or expanded host conformance.
"""
from __future__ import annotations

from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]


def _csv_section(text: str, start: str) -> str:
    """Extract an existing CSV helper section through its next Markdown heading."""
    section = text.split(start, 1)[1]
    return section.split("\n##", 1)[0]


def _assert_csv_numeric_summary(section: str, label: str) -> None:
    """Require existing numeric kinds in the scalar list, not unrelated nearby prose."""
    candidates = [
        line for line in section.splitlines()
        if "nil" in line.lower() and "boolean" in line.lower()
        and ("string" in line.lower() or "symbol" in line.lower())
    ]
    assert candidates, f"{label} needs a discoverable CSV scalar summary"
    for line in candidates:
        normalized = " ".join(line.lower().split())
        assert "decimal" in normalized and "rational" in normalized, (
            f"{label} CSV scalar summary omits existing Decimal/Rational support"
        )
        assert "integer" in normalized and "float64" in normalized, (
            f"{label} CSV scalar summary must retain Integer/Float64 support"
        )


def _assert_unequal_length_summary(text: str) -> None:
    """Pin the existing generic constructor diagnostic without promising a column name."""
    summary = next(
        line for line in text.splitlines()
        if "unequal column lengths at construction:" in line.lower()
    )
    assert "sheet expected all columns to have equal length" in summary, (
        "Sheet length summary must give the shared fixture's exact generic diagnostic"
    )
    assert "with column name" not in summary.lower(), (
        "Sheet length summary must not promise absent column-name detail"
    )


@pytest.mark.parametrize(
    ("relpath", "start"),
    (
        ("GENIA_STATE.md", "`render_csv(sheet)` (**Experimental**):"),
        ("GENIA_RULES.md", "## 22) Sheet invariants"),
        ("GENIA_REPL_README.md", "- `render_csv(sheet)` is a host-backed pure builtin"),
        ("README.md", "### render_csv Sheet output helper"),
    ),
)
def test_csv_numeric_summaries_include_existing_r22_kinds(relpath: str, start: str) -> None:
    """Protect each maintained scalar list against omitting current numeric kinds."""
    text = (ROOT / relpath).read_text(encoding="utf-8")
    # The REPL helper is one bullet, not its containing multi-helper section.
    section = text.split(start, 1)[1].split("\n", 1)[0] if "REPL" in relpath else _csv_section(text, start)
    _assert_csv_numeric_summary(section, relpath)


def test_sheet_length_summary_matches_existing_shared_error() -> None:
    """Constructor summary must agree with the unchanged shared diagnostic fixture."""
    _assert_unequal_length_summary((ROOT / "GENIA_STATE.md").read_text(encoding="utf-8"))


def test_guard_rejects_restored_omitted_numeric_kinds() -> None:
    """A correct unrelated numeric paragraph cannot offset a stale CSV scalar list."""
    text = "Decimal and Rational exist.\n- string, symbol, integer, float, boolean, and nil fields are supported"
    with pytest.raises(AssertionError, match="omits existing Decimal/Rational"):
        _assert_csv_numeric_summary(text, "restored fixture")


def test_guard_rejects_restored_column_name_promise() -> None:
    """Pin rejection of the original summary even beside the correct error elsewhere."""
    text = "sheet expected all columns to have equal length\n- unequal column lengths at construction: TypeError with column name"
    with pytest.raises(AssertionError, match="exact generic diagnostic"):
        _assert_unequal_length_summary(text)
