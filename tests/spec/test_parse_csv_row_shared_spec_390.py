from pathlib import Path

import pytest

from tools.spec_runner.comparator import compare_spec
from tools.spec_runner.executor import execute_spec
from tools.spec_runner.loader import discover_specs, load_spec


ISSUE_390_EVAL_SPECS = [
    "parse-csv-row-basic.yaml",
    "parse-csv-row-quoted-fields.yaml",
    "parse-csv-row-blank-line.yaml",
    "parse-csv-row-malformed.yaml",
    "parse-csv-row-header-map.yaml",
    "parse-csv-row-header-mismatch.yaml",
    "parse-csv-row-pipeline-shape.yaml",
    "parse-csv-row-quote-in-unquoted-field.yaml",
    "parse-csv-row-data-after-closing-quote.yaml",
    "parse-csv-row-embedded-line-break.yaml",
]

ISSUE_390_ERROR_SPECS = [
    "parse-csv-row-non-string-line-error.yaml",
    "parse-csv-row-non-list-headers-error.yaml",
    "parse-csv-row-invalid-header-error.yaml",
]


def _assert_spec_passes(path: str) -> None:
    spec = load_spec(Path(path))
    actual = execute_spec(spec)
    failures = compare_spec(spec, actual)
    assert failures == []


def test_issue_390_shared_spec_inventory_is_present() -> None:
    specs, invalid_specs = discover_specs()
    names = {spec.path.name for spec in specs}

    assert invalid_specs == []
    for fname in ISSUE_390_EVAL_SPECS + ISSUE_390_ERROR_SPECS:
        assert fname in names


@pytest.mark.parametrize("fname", ISSUE_390_EVAL_SPECS)
def test_issue_390_parse_csv_row_eval_shared_specs_execute_as_contract(fname: str) -> None:
    _assert_spec_passes(f"spec/eval/{fname}")


@pytest.mark.parametrize("fname", ISSUE_390_ERROR_SPECS)
def test_issue_390_parse_csv_row_error_shared_specs_execute_as_contract(fname: str) -> None:
    _assert_spec_passes(f"spec/error/{fname}")
