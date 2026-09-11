"""E18-4 (#794) shared cross-host spec coverage for equality-like surface agreement."""

from __future__ import annotations

from pathlib import Path

import pytest

from tools.spec_runner.comparator import compare_spec
from tools.spec_runner.executor import execute_spec
from tools.spec_runner.loader import discover_specs, load_spec


REPO = Path(__file__).resolve().parents[2]
EVAL_DIR = REPO / "spec" / "eval"
ERROR_DIR = REPO / "spec" / "error"

R18_SURFACE_EVAL_SPECS = [
    "r18-surface-agreement-across-equality-like-paths.yaml",
    "r18-surface-assert-eq-uses-one-relation.yaml",
    "r18-surface-sheet-column-identity.yaml",
]

R18_SURFACE_ERROR_SPECS = [
    "r18-surface-assert-eq-rejects-cross-kind.yaml",
]


def test_discover_specs_includes_r18_surface_cases() -> None:
    specs, invalid_specs = discover_specs()

    assert not invalid_specs
    discovered = {spec.name for spec in specs}
    expected = {
        Path(name).stem
        for name in [*R18_SURFACE_EVAL_SPECS, *R18_SURFACE_ERROR_SPECS]
    }
    assert expected.issubset(discovered)


@pytest.mark.parametrize("fname", R18_SURFACE_EVAL_SPECS)
def test_r18_surface_eval_shared_specs(fname: str) -> None:
    spec = load_spec(EVAL_DIR / fname)
    actual = execute_spec(spec)
    failures = compare_spec(spec, actual)

    assert actual.ir is None
    assert not failures, f"Failures: {failures}"


@pytest.mark.parametrize("fname", R18_SURFACE_ERROR_SPECS)
def test_r18_surface_error_shared_specs(fname: str) -> None:
    spec = load_spec(ERROR_DIR / fname)
    actual = execute_spec(spec)
    failures = compare_spec(spec, actual)

    assert actual.ir is None
    assert not failures, f"Failures: {failures}"
