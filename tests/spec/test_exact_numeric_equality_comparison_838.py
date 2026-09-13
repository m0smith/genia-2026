"""Shared cross-host spec coverage for issue #838 step 4 (exact numeric
equality/comparison reconciliation).

Contract: docs/design/exact-numeric-model-contract.md section 10.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tools.spec_runner.comparator import compare_spec
from tools.spec_runner.executor import execute_spec
from tools.spec_runner.loader import discover_specs, load_spec

REPO = Path(__file__).resolve().parents[2]
EVAL_DIR = REPO / "spec" / "eval"

EXACT_NUMERIC_EQUALITY_EVAL_SPECS = [
    "exact-numeric-equality-comparison-rational.yaml",
]


def test_discover_specs_includes_exact_numeric_equality_cases() -> None:
    specs, invalid_specs = discover_specs()

    assert not invalid_specs
    discovered = {spec.name for spec in specs}
    expected = {Path(name).stem for name in EXACT_NUMERIC_EQUALITY_EVAL_SPECS}
    assert expected.issubset(discovered)


@pytest.mark.parametrize("fname", EXACT_NUMERIC_EQUALITY_EVAL_SPECS)
def test_exact_numeric_equality_eval_shared_specs(fname: str) -> None:
    spec = load_spec(EVAL_DIR / fname)
    actual = execute_spec(spec)
    failures = compare_spec(spec, actual)

    assert actual.ir is None
    assert not failures, f"Failures: {failures}"
