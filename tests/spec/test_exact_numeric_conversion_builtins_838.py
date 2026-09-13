"""Shared cross-host spec coverage for issue #838 step 5 (explicit exact
numeric conversion builtins: `rational(...)`, `float64(...)`, `exact(...)`).

Contract: docs/design/exact-numeric-model-contract.md sections 4, 5, 6.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tools.spec_runner.comparator import compare_spec
from tools.spec_runner.executor import execute_spec
from tools.spec_runner.loader import discover_specs, load_spec

REPO = Path(__file__).resolve().parents[2]
EVAL_DIR = REPO / "spec" / "eval"

EXACT_NUMERIC_CONVERSION_EVAL_SPECS = [
    "exact-numeric-conversion-builtins.yaml",
]


def test_discover_specs_includes_exact_numeric_conversion_cases() -> None:
    specs, invalid_specs = discover_specs()

    assert not invalid_specs
    discovered = {spec.name for spec in specs}
    expected = {Path(name).stem for name in EXACT_NUMERIC_CONVERSION_EVAL_SPECS}
    assert expected.issubset(discovered)


@pytest.mark.parametrize("fname", EXACT_NUMERIC_CONVERSION_EVAL_SPECS)
def test_exact_numeric_conversion_eval_shared_specs(fname: str) -> None:
    spec = load_spec(EVAL_DIR / fname)
    actual = execute_spec(spec)
    failures = compare_spec(spec, actual)

    assert actual.ir is None
    assert not failures, f"Failures: {failures}"
