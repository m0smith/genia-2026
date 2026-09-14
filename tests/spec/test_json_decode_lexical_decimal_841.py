"""Shared cross-host spec coverage for issue #841 (lexical JSON Decimal
decode).

Contract: docs/design/exact-numeric-model-contract.md section 13.5.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tools.spec_runner.comparator import compare_spec
from tools.spec_runner.executor import execute_spec
from tools.spec_runner.loader import discover_specs, load_spec

REPO = Path(__file__).resolve().parents[2]
EVAL_DIR = REPO / "spec" / "eval"

JSON_DECODE_LEXICAL_DECIMAL_EVAL_SPECS = [
    "json-decode-lexical-decimal.yaml",
]


def test_discover_specs_includes_json_decode_lexical_decimal_case() -> None:
    specs, invalid_specs = discover_specs()

    assert not invalid_specs
    discovered = {spec.name for spec in specs}
    expected = {Path(name).stem for name in JSON_DECODE_LEXICAL_DECIMAL_EVAL_SPECS}
    assert expected.issubset(discovered)


@pytest.mark.parametrize("fname", JSON_DECODE_LEXICAL_DECIMAL_EVAL_SPECS)
def test_json_decode_lexical_decimal_eval_shared_specs(fname: str) -> None:
    spec = load_spec(EVAL_DIR / fname)
    actual = execute_spec(spec)
    failures = compare_spec(spec, actual)

    assert actual.ir is None
    assert not failures, f"Failures: {failures}"
