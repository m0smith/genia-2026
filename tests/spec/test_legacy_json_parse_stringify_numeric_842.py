"""Shared cross-host spec coverage for issue #842 (legacy json_parse/
json_stringify numeric reconciliation).

Contract: docs/design/exact-numeric-model-contract.md section 13.5's
lexical-decode principle, generalized to the legacy compatibility surface.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tools.spec_runner.comparator import compare_spec
from tools.spec_runner.executor import execute_spec
from tools.spec_runner.loader import discover_specs, load_spec

REPO = Path(__file__).resolve().parents[2]
EVAL_DIR = REPO / "spec" / "eval"

LEGACY_JSON_NUMERIC_EVAL_SPECS = [
    "legacy-json-parse-stringify-numeric.yaml",
]


def test_discover_specs_includes_legacy_json_numeric_case() -> None:
    specs, invalid_specs = discover_specs()

    assert not invalid_specs
    discovered = {spec.name for spec in specs}
    expected = {Path(name).stem for name in LEGACY_JSON_NUMERIC_EVAL_SPECS}
    assert expected.issubset(discovered)


@pytest.mark.parametrize("fname", LEGACY_JSON_NUMERIC_EVAL_SPECS)
def test_legacy_json_numeric_eval_shared_specs(fname: str) -> None:
    spec = load_spec(EVAL_DIR / fname)
    actual = execute_spec(spec)
    failures = compare_spec(spec, actual)

    assert actual.ir is None
    assert not failures, f"Failures: {failures}"
