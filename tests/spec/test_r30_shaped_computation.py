"""Run the R30 shared Sheet and standalone List semantic specifications on Python."""

from pathlib import Path

import pytest

from tools.spec_runner.comparator import compare_spec
from tools.spec_runner.executor import execute_spec
from tools.spec_runner.loader import load_spec

CASES = sorted((Path(__file__).resolve().parents[2] / "spec").glob("*/r30-*.yaml"))


@pytest.mark.parametrize("path", CASES, ids=lambda path: path.stem)
def test_r30_shared_case(path):
    spec = load_spec(path)
    assert ("sheet_values" in spec.requires) == path.stem.startswith("r30-sheet-")
    actual = execute_spec(spec)
    assert not compare_spec(spec, actual), (actual, compare_spec(spec, actual))
