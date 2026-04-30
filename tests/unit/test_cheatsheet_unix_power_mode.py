from __future__ import annotations

from pathlib import Path

import pytest

from cheatsheet_validation import assert_case_result, assert_doc_and_cases_synced

DOC_PATH = Path("docs/cheatsheet/unix-power-mode.md")
CASES_PATH = Path("tests/data/cheatsheet_unix_power_mode_cases.json")
CASES = assert_doc_and_cases_synced(DOC_PATH, CASES_PATH)


def test_unix_power_mode_cheatsheet_doc_and_case_file_stay_in_sync():
    assert_doc_and_cases_synced(DOC_PATH, CASES_PATH)


@pytest.mark.parametrize("case", CASES, ids=lambda case: case["id"])
def test_unix_power_mode_cheatsheet_examples_execute(case: dict):
    assert_case_result(case)
