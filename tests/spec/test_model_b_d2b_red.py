"""D2b proposed portable linking behavior; R16 source fixtures, no implementation stub.

Python executes every oracle without skip/xfail. C++ applicability is separately
measured through the existing R16 external host executor, never reported as PASS.
"""

from pathlib import Path
import pytest
from tools.spec_runner.loader import load_spec
from tools.spec_runner.executor import execute_spec
from tools.spec_runner.comparator import compare_spec

REPO = Path(__file__).resolve().parents[2]
CASES = sorted((REPO / "spec").glob("*/model-b-link-*.yaml")) + [
    REPO / "spec/error" / name
    for name in (
        "model-b-c-own-extend-ordinary-rejected.yaml",
        "model-b-c-own-use-ordinary-base-unchanged.yaml",
        "model-b-d1-preserve-ordinary-extension-rejection.yaml",
        "error-r20-cross-module-overlapping-unit-ambiguity.yaml",
    )
]


@pytest.mark.parametrize("path", CASES, ids=lambda p: p.stem)
def test_d2b_shared_oracle(path):
    """Compare exact public observables using the existing shared runner machinery."""
    spec = load_spec(path)
    assert compare_spec(spec, execute_spec(spec)) == []


def test_d2b_shared_requirements_and_owned_cpp_gap():
    """Every proposed D2b case is gated and attached to the existing C++ owner."""
    import json

    gap = next(
        g
        for g in json.loads((REPO / "spec/known_host_gaps.json").read_text())["gaps"]
        if g["capability"] == "default_open_functions"
    )
    assert gap["tracking_issue"] == "m0smith/genia-2026#1269"
    for path in CASES:
        if path.stem.startswith("model-b-link-"):
            spec = load_spec(path)
            assert {"multi_file_eval", "open_functions", "default_open_functions"} <= set(
                spec.requires
            )
            assert spec.name in gap["affected_tests"]
