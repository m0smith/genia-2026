"""E18-1 (#791) shared cross-host spec coverage for portable value equality.

These cases are the portable evidence a future host consumes to reproduce the
approved R18 structural and numeric equality behavior without reading Python
source.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tools.spec_runner.comparator import compare_spec
from tools.spec_runner.executor import execute_spec
from tools.spec_runner.loader import discover_specs, load_spec


REPO = Path(__file__).resolve().parents[2]
EVAL_DIR = REPO / "spec" / "eval"

R18_EQUALITY_EVAL_SPECS = [
    "r18-equality-boolean-number-separation.yaml",
    "r18-equality-exact-int-float-bridge.yaml",
    "r18-equality-signed-zero-and-infinities.yaml",
    "r18-equality-nan-non-reflexive.yaml",
    "r18-equality-kind-separation.yaml",
    "r18-equality-structural-contents.yaml",
    "r18-equality-inequality-is-negation.yaml",
]


def test_discover_specs_includes_r18_equality_cases() -> None:
    specs, invalid_specs = discover_specs()

    assert not invalid_specs
    discovered = {spec.name for spec in specs}
    expected = {Path(name).stem for name in R18_EQUALITY_EVAL_SPECS}
    assert expected.issubset(discovered)


@pytest.mark.parametrize("fname", R18_EQUALITY_EVAL_SPECS)
def test_r18_equality_eval_shared_specs(fname: str) -> None:
    spec = load_spec(EVAL_DIR / fname)
    actual = execute_spec(spec)
    failures = compare_spec(spec, actual)

    assert actual.ir is None
    assert not failures, f"Failures: {failures}"
