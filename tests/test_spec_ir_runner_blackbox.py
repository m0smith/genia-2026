from pathlib import Path

import pytest

from tools.spec_runner.comparator import compare_spec
from tools.spec_runner.executor import execute_spec
from tools.spec_runner.loader import discover_specs, load_spec


IR_DIR = Path(__file__).resolve().parents[1] / "spec" / "ir"
EVAL_DIR = Path(__file__).resolve().parents[1] / "spec" / "eval"
FLOW_DIR = Path(__file__).resolve().parents[1] / "spec" / "flow"
CLI_DIR = Path(__file__).resolve().parents[1] / "spec" / "cli"


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
        "pipeline-call-shape-basic",
        "output-print",
        "output-log",
        "output-print-and-log",
        "pattern-duplicate-binding-false",
    }.issubset(eval_names)


def test_discover_specs_includes_cli_matrix_cases() -> None:
    specs, invalid_specs = discover_specs()

    assert not invalid_specs
    cli_names = {spec.name for spec in specs if spec.category == "cli"}
    assert {
        "file_mode_main_argv",
        "command_mode_collect_sum",
        "pipe_mode_map_parse_int",
        "pipe_mode_bare_parse_int_error",
        "pipe_mode_sum_error",
        "pipe_mode_collect_error",
    }.issubset(cli_names)


def test_discover_specs_includes_flow_cases() -> None:
    specs, invalid_specs = discover_specs()

    assert not invalid_specs
    flow_names = {spec.name for spec in specs if spec.category == "flow"}
    assert {
        "stdin-lines-collect-basic",
        "stdin-lines-take-early-stop",
        "flow-single-use-error",
        "flow-error-propagation-sum-on-flow",
        "refine-step-emit-deterministic",
        "rules-rule-emit-deterministic",
        "step-rule-helper-equivalence",
        "rules-identity-stage",
    }.issubset(flow_names)


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
        "pipeline-call-shape-basic.yaml",
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


@pytest.mark.parametrize(
    "fname",
    [
        "file_mode_main_argv.yaml",
        "command_mode_collect_sum.yaml",
        "pipe_mode_map_parse_int.yaml",
        "pipe_mode_bare_parse_int_error.yaml",
        "pipe_mode_sum_error.yaml",
        "pipe_mode_collect_error.yaml",
    ],
)
def test_cli_spec_fixture(fname: str) -> None:
    spec = load_spec(CLI_DIR / fname)
    actual = execute_spec(spec)
    failures = compare_spec(spec, actual)

    assert actual.ir is None
    assert not failures, f"Failures: {failures}"


@pytest.mark.parametrize(
    "fname",
    [
        "stdin-lines-collect-basic.yaml",
        "stdin-lines-take-early-stop.yaml",
        "flow-single-use-error.yaml",
        "flow-error-propagation-sum-on-flow.yaml",
        "refine-step-emit-deterministic.yaml",
        "rules-rule-emit-deterministic.yaml",
        "step-rule-helper-equivalence.yaml",
        "rules-identity-stage.yaml",
    ],
)
def test_flow_spec_fixture(fname: str) -> None:
    spec = load_spec(FLOW_DIR / fname)
    actual = execute_spec(spec)
    failures = compare_spec(spec, actual)

    assert actual.ir is None
    assert not failures, f"Failures: {failures}"
