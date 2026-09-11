"""E18-3 (#793) shared cross-host spec coverage for identity and protected equality.

Opaque semantic tokens have no shared cases by design: R18 exposes no way to
mint or observe a token from Genia source, so that family is covered by focused
tests against the internal adapter instead.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tools.spec_runner.comparator import compare_spec
from tools.spec_runner.executor import execute_spec
from tools.spec_runner.loader import discover_specs, load_spec


REPO = Path(__file__).resolve().parents[2]
EVAL_DIR = REPO / "spec" / "eval"

R18_IDENTITY_PROTECTED_SPECS = [
    "r18-protected-equality-is-carrier-identity.yaml",
    "r18-protected-non-interference-through-containers.yaml",
    "r18-identity-bearing-equality.yaml",
]


def test_discover_specs_includes_r18_identity_protected_cases() -> None:
    specs, invalid_specs = discover_specs()

    assert not invalid_specs
    discovered = {spec.name for spec in specs}
    expected = {Path(name).stem for name in R18_IDENTITY_PROTECTED_SPECS}
    assert expected.issubset(discovered)


@pytest.mark.parametrize("fname", R18_IDENTITY_PROTECTED_SPECS)
def test_r18_identity_protected_shared_specs(fname: str) -> None:
    spec = load_spec(EVAL_DIR / fname)
    actual = execute_spec(spec)
    failures = compare_spec(spec, actual)

    assert actual.ir is None
    assert not failures, f"Failures: {failures}"
