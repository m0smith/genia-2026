from pathlib import Path

import pytest

from tools.spec_runner.comparator import compare_spec
from tools.spec_runner.executor import execute_spec
from tools.spec_runner.loader import discover_specs, load_spec


ISSUE_389_EVAL_SPECS = [
    "parse-jsonl-record-valid-object.yaml",
    "parse-jsonl-record-blank-lines.yaml",
    "parse-jsonl-record-invalid-json.yaml",
    "parse-jsonl-record-non-object-json.yaml",
    "parse-jsonl-record-pipeline-shape.yaml",
    "parse-jsonl-record-json-parse-regression.yaml",
]

ISSUE_389_ERROR_SPECS = [
    "parse-jsonl-record-non-string-error.yaml",
]


def _assert_spec_passes(path: str) -> None:
    spec = load_spec(Path(path))
    actual = execute_spec(spec)
    failures = compare_spec(spec, actual)
    assert failures == []


def test_issue_389_shared_spec_inventory_is_present() -> None:
    specs, invalid_specs = discover_specs()
    names = {spec.path.name for spec in specs}

    assert invalid_specs == []
    for fname in ISSUE_389_EVAL_SPECS + ISSUE_389_ERROR_SPECS:
        assert fname in names


@pytest.mark.parametrize("fname", ISSUE_389_EVAL_SPECS)
def test_issue_389_parse_jsonl_record_eval_shared_specs_execute_as_contract(fname: str) -> None:
    _assert_spec_passes(f"spec/eval/{fname}")


@pytest.mark.parametrize("fname", ISSUE_389_ERROR_SPECS)
def test_issue_389_parse_jsonl_record_error_shared_specs_execute_as_contract(fname: str) -> None:
    _assert_spec_passes(f"spec/error/{fname}")
