"""E20-2/E20-4 shared cross-host spec coverage for R20 open functions and
extensible pattern dispatch (docs/design/r20-open-functions-contract.md,
docs/design/r20-open-functions-syntax-ir-design.md).

These cases are the portable evidence a future host consumes to reproduce
the approved R20 syntax, Core IR, local dispatch, and explicit cross-module
contribution/linking behavior without reading Python source.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tools.spec_runner.comparator import compare_spec
from tools.spec_runner.executor import execute_spec
from tools.spec_runner.loader import discover_specs, load_spec


REPO = Path(__file__).resolve().parents[2]
PARSE_DIR = REPO / "spec" / "parse"
IR_DIR = REPO / "spec" / "ir"
EVAL_DIR = REPO / "spec" / "eval"
ERROR_DIR = REPO / "spec" / "error"

R20_PARSE_SPECS = [
    "parse-r20-open-repeated-clauses.yaml",
    "parse-r20-open-grouped-clause.yaml",
    "parse-r20-extend-contribution-clause.yaml",
    "parse-r20-use-selection-statement.yaml",
    "parse-r20-ordinary-funcdef-unaffected.yaml",
    "parse-error-r20-open-redeclaration.yaml",
    "parse-error-r20-extend-requires-qualified-target.yaml",
    "parse-error-r20-nested-open-declaration.yaml",
    "parse-error-r20-use-missing-with.yaml",
]

R20_IR_SPECS = [
    "r20-open-repeated-clauses.yaml",
    "r20-open-grouped-equivalence.yaml",
    "r20-extend-contribution.yaml",
    "r20-use-selection.yaml",
    "r20-open-varargs-shape.yaml",
]

R20_EVAL_SPECS = [
    "r20-gcd-repeated-clauses.yaml",
    "r20-gcd-grouped-clause-equivalent.yaml",
    "r20-varargs-over-fixed-precedence.yaml",
    "r20-help-provenance.yaml",
]

R20_ERROR_SPECS = [
    "error-r20-no-matching-case.yaml",
    "error-r20-varargs-ambiguity.yaml",
    "error-r20-local-duplicate-clause.yaml",
]

# Cross-module contribution/linking behavior (disjoint contributions,
# import-order independence, ordinary-import non-selection, duplicate
# selection, ambiguous overlap, alias identity) requires a real second
# `.genia` module file on disk. The shared eval/error YAML runner
# (tools/spec_runner) only accepts one inline `source` string per case
# today — it has no multi-file fixture mechanism — so R20 cross-module
# behavior is proven as Python-host unit evidence instead, in
# tests/unit/test_r20_open_functions_cross_module.py. This is a disclosed
# infrastructure gap (see docs/releases/R20.md), not a semantic gap: the
# contract's cross-module obligations are exercised and passing, just not
# through the generic multi-host YAML runner yet.


def test_discover_specs_includes_r20_cases() -> None:
    specs, invalid_specs = discover_specs()

    assert not invalid_specs
    discovered = {spec.name for spec in specs}
    expected = {
        Path(name).stem
        for name in [*R20_PARSE_SPECS, *R20_IR_SPECS, *R20_EVAL_SPECS, *R20_ERROR_SPECS]
    }
    assert expected.issubset(discovered)


@pytest.mark.parametrize("fname", R20_PARSE_SPECS)
def test_r20_parse_shared_specs(fname: str) -> None:
    spec = load_spec(PARSE_DIR / fname)
    actual = execute_spec(spec)
    failures = compare_spec(spec, actual)
    assert not failures, f"Failures: {failures}"


@pytest.mark.parametrize("fname", R20_IR_SPECS)
def test_r20_ir_shared_specs(fname: str) -> None:
    spec = load_spec(IR_DIR / fname)
    actual = execute_spec(spec)
    failures = compare_spec(spec, actual)
    assert not failures, f"Failures: {failures}"


@pytest.mark.parametrize("fname", R20_EVAL_SPECS)
def test_r20_eval_shared_specs(fname: str) -> None:
    spec = load_spec(EVAL_DIR / fname)
    actual = execute_spec(spec)
    failures = compare_spec(spec, actual)

    assert actual.ir is None
    assert not failures, f"Failures: {failures}"


@pytest.mark.parametrize("fname", R20_ERROR_SPECS)
def test_r20_error_shared_specs(fname: str) -> None:
    spec = load_spec(ERROR_DIR / fname)
    actual = execute_spec(spec)
    failures = compare_spec(spec, actual)

    assert actual.ir is None
    assert not failures, f"Failures: {failures}"
