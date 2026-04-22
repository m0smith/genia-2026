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


def test_existing_eval_category_still_executes_through_shared_runner() -> None:
    spec = load_spec(EVAL_DIR / "arithmetic-basic.yaml")
    actual = execute_spec(spec)
    failures = compare_spec(spec, actual)

    assert actual.ir is None
    assert not failures, f"Failures: {failures}"
