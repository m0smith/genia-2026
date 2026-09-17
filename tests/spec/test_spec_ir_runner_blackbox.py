from pathlib import Path

import pytest

from tools.spec_runner.comparator import compare_spec
from tools.spec_runner.executor import execute_spec
from tools.spec_runner.loader import discover_specs, load_spec

# The `test_*_spec_fixture` blackbox tests below execute a *small
# representative sample* per category through the real
# load_spec -> execute_spec -> compare_spec pipeline, to prove that wiring
# works end to end for each category. They deliberately do not replay every
# fixture in `spec/`: the full shared corpus is already executed once per
# supported Python version by the canonical `python -m tools.spec_runner`
# path, so re-running every case here would only duplicate that execution
# without adding evidence. Each category's discovery is still fully checked
# for the presence of every fixture name via `test_discover_specs_includes_*`
# below, which is cheap (no interpreter execution) and does not replay cases.

IR_DIR = Path(__file__).resolve().parents[2] / "spec" / "ir"
EVAL_DIR = Path(__file__).resolve().parents[2] / "spec" / "eval"
FLOW_DIR = Path(__file__).resolve().parents[2] / "spec" / "flow"
CLI_DIR = Path(__file__).resolve().parents[2] / "spec" / "cli"
ERROR_DIR = Path(__file__).resolve().parents[2] / "spec" / "error"


@pytest.mark.spec
@pytest.mark.slow
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
        "quasiquote-unquote-var",
        "quasiquote-unquote-splicing-var",
    }.issubset(ir_names)

@pytest.mark.spec
@pytest.mark.slow
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
        "pattern-first-match-wins",
        "pattern-literal-int",
        "pattern-literal-string",
        "pattern-wildcard",
        "pattern-variable-binding",
        "pattern-list-exact",
        "pattern-list-exact-miss",
        "pattern-list-empty",
        "pattern-tuple-multiarg",
        "pattern-map-partial",
        "pattern-map-key-binding",
        "pattern-map-shorthand",
        "pattern-option-some",
        "pattern-option-none",
        "pattern-option-none-context",
        "pattern-option-none-reason",
        "pattern-guard-pass",
        "pattern-guard-skip",
        "pattern-glob-star",
        "pattern-glob-non-string",
        "option-some-render-basic",
        "option-none-render-basic",
        "pipeline-option-some-lift",
        "pipeline-option-none-short-circuit",
        "stdlib-map-list-basic",
        "stdlib-map-list-empty",
        "stdlib-filter-list-basic",
        "stdlib-filter-list-no-match",
        "stdlib-first-list-some",
        "stdlib-first-list-empty",
        "stdlib-last-list-some",
        "stdlib-last-list-empty",
        "stdlib-nth-list-some",
        "stdlib-nth-list-out-of-bounds",
        "stdlib-map-option-elements",
        "stdlib-filter-option-elements",
        "map-items-map-item-key-pipeline",
        "map-items-map-item-value-pipeline",
        "each-on-list-seq-compatible",
        "seq-compatible-list-collect",
        "seq-compatible-list-run-no-output",
        "seq-compatible-list-each-run",
        "seq-compatible-list-each-lazy-unconsumed",
        "seq-compatible-list-transform-chain",
        "seq-compatible-range-transform-chain",
        "seq-compatible-range-each-run-regression",
        "seq-compatible-collect-nonseq-error",
        "reduce-on-flow-type-error",
        "first-on-flow-type-error",
        "pairs-basic",
        "pairs-shorter-first",
        "pairs-shorter-second",
        "pairs-empty-first",
        "pairs-empty-both",
        "pairs-strings",
        "pairs-pattern-match",
    }.issubset(eval_names)

@pytest.mark.spec
@pytest.mark.slow
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


def test_discover_specs_includes_error_pattern_cases() -> None:
    specs, invalid_specs = discover_specs()

    assert not invalid_specs
    error_names = {spec.name for spec in specs if spec.category == "error"}
    assert {
        "error-pattern-miss",
        "error-pattern-guard-all-fail",
        "error-pattern-glob-malformed",
    }.issubset(error_names)

@pytest.mark.spec
@pytest.mark.slow
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
        "flow-keep-some-parse-int",
        "flow-tee-zip-list-pairs",
        "flow-zip-list-pairs",
        "count-as-pipe-stage-type-error",
        "flow-map-basic",
        "flow-filter-basic",
        "flow-map-filter-chain",
        "seq-compatible-evolve-each-run",
        "seq-compatible-flow-transform-chain",
    }.issubset(flow_names)

@pytest.mark.spec
@pytest.mark.slow
@pytest.mark.parametrize(
    "fname",
    [
        "pipeline-explicit.yaml",
        "case-patterns.yaml",
        "quasiquote-unquote-splicing-var.yaml",
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
        "pattern-first-match-wins.yaml",
        "pattern-option-some.yaml",
        "stdlib-map-list-basic.yaml",
        "seq-compatible-list-collect.yaml",
        "pairs-basic.yaml",
        "format-first-class-format-value-named.yaml",
        "format-compose-nested.yaml",
        "format-field-align-left.yaml",
    ],
)
@pytest.mark.spec
@pytest.mark.slow
def test_eval_spec_fixture(fname: str) -> None:
    spec = load_spec(EVAL_DIR / fname)
    actual = execute_spec(spec)
    failures = compare_spec(spec, actual)

    assert actual.ir is None
    assert not failures, f"Failures: {failures}"


@pytest.mark.parametrize(
    "fname",
    [
        # command_mode_collect_sum.yaml is deliberately NOT included here:
        # it is the representative expensive CLI fixture kept unique to
        # tests/spec/test_cli_shared_spec_runner.py to avoid replaying it
        # through two separate pytest paths on every supported Python.
        "file_mode_main_argv.yaml",
        "pipe_mode_map_parse_int.yaml",
    ],
)
@pytest.mark.spec
@pytest.mark.slow
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
        "flow-error-propagation-sum-on-flow.yaml",
        "flow-map-filter-chain.yaml",
        "seq-compatible-flow-transform-chain.yaml",
    ],
)
@pytest.mark.spec
@pytest.mark.slow
def test_flow_spec_fixture(fname: str) -> None:
    spec = load_spec(FLOW_DIR / fname)
    actual = execute_spec(spec)
    failures = compare_spec(spec, actual)

    assert actual.ir is None
    assert not failures, f"Failures: {failures}"


@pytest.mark.parametrize(
    "fname",
    [
        "error-pattern-miss.yaml",
        "error-format-non-string-template.yaml",
        "error-format-field-empty-spec.yaml",
        "error-format-compose-invalid-piece.yaml",
    ],
)
@pytest.mark.spec
@pytest.mark.slow
def test_error_spec_fixture(fname: str) -> None:
    spec = load_spec(ERROR_DIR / fname)
    actual = execute_spec(spec)
    failures = compare_spec(spec, actual)

    assert actual.ir is None
    assert not failures, f"Failures: {failures}"
