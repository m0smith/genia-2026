"""Execute approved R29 shared oracles with the existing semantic spec harness.

T1 is expected RED until sheet_records exists; T2 is existing-behavior PASS.
These are Python reference-host runs, not evidence of C++ implementation.
"""

from pathlib import Path

import pytest

from tools.spec_runner.comparator import compare_spec
from tools.spec_runner.executor import execute_spec
from tools.spec_runner.loader import load_spec

ROOT = Path(__file__).resolve().parents[2]
T1 = sorted((ROOT / "spec").glob("*/r29-records-*.yaml"))
T2 = sorted((ROOT / "spec").glob("*/r29-existing-*.yaml"))


@pytest.mark.parametrize("path", T1, ids=lambda p: p.stem)
def test_t1_new_record_boundary(path):
    spec = load_spec(path)
    required = ("flow_phase_1", "sheet_values") if spec.category == "flow" else ("sheet_values",)
    assert spec.requires == required
    actual = execute_spec(spec)
    assert not compare_spec(spec, actual), (spec.name, actual, compare_spec(spec, actual))


@pytest.mark.parametrize("path", T2, ids=lambda p: p.stem)
def test_t2_existing_composition(path):
    spec = load_spec(path)
    actual = execute_spec(spec)
    assert not compare_spec(spec, actual), (spec.name, actual, compare_spec(spec, actual))
