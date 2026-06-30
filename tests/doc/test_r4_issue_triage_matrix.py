from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

import pytest


REPO = Path(__file__).resolve().parents[2]
# The R4 issue triage matrix is a committed audit/triage artifact. It used to
# live only in the gitignored process scratch tree, which made this guardrail
# depend on non-committed scratch input. The matrix is now committed under
# docs/ so the guardrail runs against an authoritative source of truth.
TRIAGE_MATRIX_DOC = (
    REPO
    / "docs"
    / "architecture"
    / "r4-issue-triage-matrix.md"
)
TABLE_HEADER = (
    "| Issue | State | Title | Classification | Recommended action | "
    "Rationale | Action taken? |"
)
EXPECTED_COLUMN_COUNT = 7


def normalize(text: str) -> str:
    without_emphasis = text.replace("*", "").replace("`", "")
    return " ".join(without_emphasis.casefold().split())


RECOGNIZED_CLASSIFICATIONS = frozenset(
    normalize(label)
    for label in [
        "R4 blocker",
        "R4 follow-up",
        "post-R4 deferred",
        "parking lot",
        "duplicate/superseded",
        "obsolete/close candidate",
        "completed/no action",
        "needs operator decision",
    ]
)
RECOGNIZED_ACTIONS = frozenset(
    normalize(label)
    for label in [
        "keep open",
        "close as completed",
        "close as not planned",
        "close as duplicate/superseded",
        "relabel",
        "defer/post-R4",
        "create small follow-up issue",
        "no action",
    ]
)


@dataclass(frozen=True)
class TriageRow:
    line_number: int
    issue: str
    state: str
    title: str
    classification: str
    recommended_action: str
    rationale: str
    action_taken: str


def read_audit_handoff() -> str:
    if not TRIAGE_MATRIX_DOC.exists():
        pytest.fail(
            "issue #456 R4 triage matrix must exist at "
            "docs/architecture/r4-issue-triage-matrix.md"
        )
    return TRIAGE_MATRIX_DOC.read_text(encoding="utf-8")


def split_table_row(line: str) -> list[str]:
    cells = line.strip().strip("|").split("|")
    return [cell.strip() for cell in cells]


def is_separator_row(cells: list[str]) -> bool:
    return all(re.fullmatch(r":?-{3,}:?", cell.strip()) for cell in cells)


def parse_triage_rows(text: str) -> list[TriageRow]:
    lines = text.splitlines()
    header_index = next(
        (
            index
            for index, line in enumerate(lines)
            if normalize(line) == normalize(TABLE_HEADER)
        ),
        None,
    )
    if header_index is None:
        pytest.fail(f"issue #456 triage table header is missing: {TABLE_HEADER}")

    rows: list[TriageRow] = []
    for line_index in range(header_index + 1, len(lines)):
        line = lines[line_index]
        if not line.startswith("|"):
            break

        cells = split_table_row(line)
        if is_separator_row(cells):
            continue
        if len(cells) != EXPECTED_COLUMN_COUNT:
            pytest.fail(
                "issue #456 triage table row must have "
                f"{EXPECTED_COLUMN_COUNT} cells at line {line_index + 1}: {line!r}"
            )

        rows.append(TriageRow(line_index + 1, *cells))

    return rows


def assert_rows_present(rows: list[TriageRow]) -> None:
    assert rows, "issue #456 triage table must include at least one data row"


def test_issue_456_triage_matrix_uses_pinned_header() -> None:
    text = read_audit_handoff()

    assert normalize(TABLE_HEADER) in {normalize(line) for line in text.splitlines()}, (
        "issue #456 triage table must use the pinned seven-column header: "
        f"{TABLE_HEADER}"
    )


def test_issue_456_triage_matrix_parses_data_rows() -> None:
    rows = parse_triage_rows(read_audit_handoff())

    assert_rows_present(rows)


def test_issue_456_triage_rows_use_recognized_classifications() -> None:
    rows = parse_triage_rows(read_audit_handoff())
    assert_rows_present(rows)

    for row in rows:
        normalized = normalize(row.classification)
        assert normalized in RECOGNIZED_CLASSIFICATIONS, (
            "issue #456 triage row has unrecognized classification "
            f"at line {row.line_number} for {row.issue}: {row.classification!r}"
        )


def test_issue_456_triage_rows_use_recognized_recommended_actions() -> None:
    rows = parse_triage_rows(read_audit_handoff())
    assert_rows_present(rows)

    for row in rows:
        normalized = normalize(row.recommended_action)
        assert normalized in RECOGNIZED_ACTIONS, (
            "issue #456 triage row has unrecognized recommended action "
            f"at line {row.line_number} for {row.issue}: "
            f"{row.recommended_action!r}"
        )


def test_issue_456_triage_rows_record_no_action_taken() -> None:
    rows = parse_triage_rows(read_audit_handoff())
    assert_rows_present(rows)

    for row in rows:
        assert normalize(row.action_taken) == "no", (
            "issue #456 triage row must record Action taken? as NO "
            f"at line {row.line_number} for {row.issue}: {row.action_taken!r}"
        )


def test_issue_456_triage_matrix_has_no_process_scratch_dependency() -> None:
    # Regression guard: this module must not reintroduce a dependency on the
    # gitignored process scratch directory as required test input. The needles
    # are assembled at runtime so this assertion does not match itself.
    source = Path(__file__).read_text(encoding="utf-8")
    scratch_dir = ".genia/process/" + "tmp"
    handoff_word = "hand" + "offs"
    assert scratch_dir not in source, (
        "tests must never require gitignored process scratch files as input "
        f"(found reference to {scratch_dir!r})"
    )
    assert handoff_word not in source, (
        "tests must never require process handoff scratch files as input"
    )
