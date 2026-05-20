from __future__ import annotations

from pathlib import Path

import pytest

from tools.spec_runner.comparator import compare_spec
from tools.spec_runner.executor import execute_spec
from tools.spec_runner.loader import discover_specs, load_spec


REPO = Path(__file__).resolve().parents[2]
EVAL_DIR = REPO / "spec" / "eval"
ERROR_DIR = REPO / "spec" / "error"

SHEET_EVAL_SPECS = [
    "sheet-shape-columns-rows.yaml",
    "sheet-empty-core.yaml",
    "sheet-select-immutable.yaml",
    "sheet-where-core.yaml",
    "sheet-derive-core.yaml",
]

SHEET_ERROR_SPECS = [
    "error-sheet-unequal-column-lengths.yaml",
    "error-sheet-select-missing-column.yaml",
    "error-sheet-derive-duplicate-column.yaml",
]


def test_discover_specs_includes_sheet_cases() -> None:
    specs, invalid_specs = discover_specs()

    assert not invalid_specs
    discovered = {spec.name for spec in specs}
    expected = {Path(name).stem for name in [*SHEET_EVAL_SPECS, *SHEET_ERROR_SPECS]}
    assert expected.issubset(discovered)


@pytest.mark.parametrize("fname", SHEET_EVAL_SPECS)
def test_sheet_eval_shared_specs(fname: str) -> None:
    spec = load_spec(EVAL_DIR / fname)
    actual = execute_spec(spec)
    failures = compare_spec(spec, actual)

    assert actual.ir is None
    assert not failures, f"Failures: {failures}"


@pytest.mark.parametrize("fname", SHEET_ERROR_SPECS)
def test_sheet_error_shared_specs(fname: str) -> None:
    spec = load_spec(ERROR_DIR / fname)
    actual = execute_spec(spec)
    failures = compare_spec(spec, actual)

    assert actual.ir is None
    assert not failures, f"Failures: {failures}"
