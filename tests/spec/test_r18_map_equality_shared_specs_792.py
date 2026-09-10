"""E18-2 (#792) shared cross-host spec coverage for map equality and legal keys."""

from __future__ import annotations

from pathlib import Path

import pytest

from tools.spec_runner.comparator import compare_spec
from tools.spec_runner.executor import execute_spec
from tools.spec_runner.loader import discover_specs, load_spec


REPO = Path(__file__).resolve().parents[2]
EVAL_DIR = REPO / "spec" / "eval"
ERROR_DIR = REPO / "spec" / "error"

R18_MAP_EVAL_SPECS = [
    "r18-map-structural-equality.yaml",
    "r18-map-key-equivalence-is-equality.yaml",
    "r18-map-equal-keys-share-every-operation.yaml",
]

R18_MAP_ERROR_SPECS = [
    "r18-map-key-nan-rejected.yaml",
    "r18-map-key-nested-nan-rejected.yaml",
    "r18-map-key-nan-rejected-on-lookup.yaml",
]


def test_discover_specs_includes_r18_map_cases() -> None:
    specs, invalid_specs = discover_specs()

    assert not invalid_specs
    discovered = {spec.name for spec in specs}
    expected = {Path(name).stem for name in [*R18_MAP_EVAL_SPECS, *R18_MAP_ERROR_SPECS]}
    assert expected.issubset(discovered)


@pytest.mark.parametrize("fname", R18_MAP_EVAL_SPECS)
def test_r18_map_eval_shared_specs(fname: str) -> None:
    spec = load_spec(EVAL_DIR / fname)
    actual = execute_spec(spec)
    failures = compare_spec(spec, actual)

    assert actual.ir is None
    assert not failures, f"Failures: {failures}"


@pytest.mark.parametrize("fname", R18_MAP_ERROR_SPECS)
def test_r18_map_error_shared_specs(fname: str) -> None:
    spec = load_spec(ERROR_DIR / fname)
    actual = execute_spec(spec)
    failures = compare_spec(spec, actual)

    assert actual.ir is None
    assert not failures, f"Failures: {failures}"
