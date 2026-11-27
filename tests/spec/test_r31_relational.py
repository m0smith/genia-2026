"""Run R31 shared relational specifications and pin their capability accounting."""

import json
from pathlib import Path

import pytest

from tools.spec_runner.comparator import compare_spec
from tools.spec_runner.executor import execute_spec
from tools.spec_runner.loader import load_spec

SPEC_ROOT = Path(__file__).resolve().parents[2] / "spec"
CASES = sorted(SPEC_ROOT.glob("*/r31-*.yaml"))


@pytest.mark.parametrize("path", CASES, ids=lambda path: path.stem)
def test_r31_shared_case(path):
    spec = load_spec(path)
    assert spec.requires == ("sheet_values", "sheet_relational")
    actual = execute_spec(spec)
    mismatches = compare_spec(spec, actual)
    assert not mismatches, (actual, mismatches)


def test_relational_gap_accounts_for_every_spec():
    gaps = json.loads((SPEC_ROOT / "known_host_gaps.json").read_text())["gaps"]
    gap, = [item for item in gaps if item["capability"] == "sheet_relational"]
    assert gap["affected_host"] == "cpp"
    assert sorted(gap["affected_tests"]) == sorted(path.stem for path in CASES)
