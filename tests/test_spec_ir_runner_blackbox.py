from pathlib import Path

import pytest

from tools.spec_runner.comparator import compare_spec
from tools.spec_runner.executor import execute_spec
from tools.spec_runner.loader import discover_specs, load_spec


IR_DIR = Path(__file__).resolve().parents[1] / "spec" / "ir"
EVAL_DIR = Path(__file__).resolve().parents[1] / "spec" / "eval"


def test_discover_specs_includes_ir_cases() -> None:
    specs, invalid_specs = discover_specs()

    assert not invalid_specs
    ir_names = {spec.name for spec in specs if spec.category == "ir"}
    assert {
        "pipeline-explicit",
        "option-constructors",
        "import-pipeline-stage",
        "call-spread",
        "case-patterns",
    }.issubset(ir_names)


def test_discover_specs_includes_eval_cases() -> None:
    specs, invalid_specs = discover_specs()

    assert not invalid_specs
    eval_names = {spec.name for spec in specs if spec.category == "eval"}
    assert {
        "arithmetic-basic",
        "output-print",
        "output-log",
        "output-print-and-log",
        "pattern-duplicate-binding-false",
    }.issubset(eval_names)


@pytest.mark.parametrize(
    "fname",
    [
        "pipeline-explicit.yaml",
        "option-constructors.yaml",
        "import-pipeline-stage.yaml",
        "call-spread.yaml",
        "case-patterns.yaml",
    ],
)
def test_ir_spec_fixture(fname: str) -> None:
    spec = load_spec(IR_DIR / fname)
    actual = execute_spec(spec)
    failures = compare_spec(spec, actual)
    assert not failures, f"Failures: {failures}"


@pytest.mark.parametrize(
    "fname",
    [
        "arithmetic-basic.yaml",
        "output-print.yaml",
        "output-log.yaml",
        "output-print-and-log.yaml",
        "pattern-duplicate-binding-false.yaml",
    ],
)
def test_eval_spec_fixture(fname: str) -> None:
    spec = load_spec(EVAL_DIR / fname)
    actual = execute_spec(spec)
    failures = compare_spec(spec, actual)

    assert actual.ir is None
    assert not failures, f"Failures: {failures}"
