from pathlib import Path

import pytest

from tools.spec_runner.comparator import compare_spec
from tools.spec_runner.executor import execute_spec
from tools.spec_runner.loader import discover_specs, load_spec


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
        "option-constructors.yaml",
        "import-pipeline-stage.yaml",
        "call-spread.yaml",
        "case-patterns.yaml",
        "quasiquote-unquote-var.yaml",
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
        "pipeline-call-shape-basic.yaml",
        "output-print.yaml",
        "output-log.yaml",
        "output-print-and-log.yaml",
        "pattern-duplicate-binding-false.yaml",
        "pattern-first-match-wins.yaml",
        "pattern-literal-int.yaml",
        "pattern-literal-string.yaml",
        "pattern-wildcard.yaml",
        "pattern-variable-binding.yaml",
        "pattern-list-exact.yaml",
        "pattern-list-exact-miss.yaml",
        "pattern-list-empty.yaml",
        "pattern-tuple-multiarg.yaml",
        "pattern-map-partial.yaml",
        "pattern-map-key-binding.yaml",
        "pattern-map-shorthand.yaml",
        "pattern-option-some.yaml",
        "pattern-option-none.yaml",
        "pattern-option-none-context.yaml",
        "pattern-option-none-reason.yaml",
        "pattern-guard-pass.yaml",
        "pattern-guard-skip.yaml",
        "pattern-glob-star.yaml",
        "pattern-glob-non-string.yaml",
        "option-some-render-basic.yaml",
        "option-none-render-basic.yaml",
        "pipeline-option-some-lift.yaml",
        "pipeline-option-none-short-circuit.yaml",
        "stdlib-map-list-basic.yaml",
        "stdlib-map-list-empty.yaml",
        "stdlib-filter-list-basic.yaml",
        "stdlib-filter-list-no-match.yaml",
        "stdlib-first-list-some.yaml",
        "stdlib-first-list-empty.yaml",
        "stdlib-last-list-some.yaml",
        "stdlib-last-list-empty.yaml",
        "stdlib-nth-list-some.yaml",
        "stdlib-nth-list-out-of-bounds.yaml",
        "stdlib-map-option-elements.yaml",
        "stdlib-filter-option-elements.yaml",
        "map-items-map-item-key-pipeline.yaml",
        "map-items-map-item-value-pipeline.yaml",
        "each-on-list-seq-compatible.yaml",
        "seq-compatible-list-collect.yaml",
        "seq-compatible-list-run-no-output.yaml",
        "seq-compatible-list-each-run.yaml",
        "seq-compatible-list-each-lazy-unconsumed.yaml",
        "seq-compatible-list-transform-chain.yaml",
        "seq-compatible-range-transform-chain.yaml",
        "seq-compatible-range-each-run-regression.yaml",
        "seq-compatible-collect-nonseq-error.yaml",
        "pairs-basic.yaml",
        "pairs-shorter-first.yaml",
        "pairs-shorter-second.yaml",
        "pairs-empty-first.yaml",
        "pairs-empty-both.yaml",
        "pairs-strings.yaml",
        "pairs-pattern-match.yaml",
        "format-first-class-format-value-named.yaml",
        "format-first-class-format-value-inline.yaml",
        "format-first-class-format-value-backward-compat.yaml",
        "format-first-class-format-display.yaml",
        "format-first-class-format-debug-repr.yaml",
        "format-first-class-format-empty-template.yaml",
        "format-first-class-format-no-placeholders.yaml",
        "format-first-class-format-positional.yaml",
        "format-compose-basic.yaml",
        "format-compose-empty.yaml",
        "format-compose-mixed-pieces.yaml",
        "format-compose-nested.yaml",
        "format-compose-repeated-placeholder.yaml",
        "format-compose-preserves-existing-format.yaml",
        "format-field-align-left.yaml",
        "format-field-align-right.yaml",
        "format-field-align-center-even.yaml",
        "format-field-align-center-odd.yaml",
        "format-field-align-noop.yaml",
        "format-field-string-precision-truncate.yaml",
        "format-field-string-precision-zero.yaml",
        "format-field-string-precision-noop.yaml",
        "format-field-numeric-precision-basic.yaml",
        "format-field-numeric-precision-integer.yaml",
        "format-field-numeric-precision-zero.yaml",
        "format-field-zero-pad-basic.yaml",
        "format-field-zero-pad-negative.yaml",
        "format-field-zero-pad-already-wide.yaml",
        "format-field-grouping-integer.yaml",
        "format-field-grouping-large.yaml",
        "format-field-grouping-negative.yaml",
        "format-field-grouping-decimal.yaml",
        "format-field-positional-with-spec.yaml",
        "format-field-format-value-parity-align.yaml",
        "format-field-format-value-parity-numeric.yaml",
        "format-field-escaped-braces-spec-text.yaml",
        "format-pipeline-map-named.yaml",
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
        "file_mode_main_argv.yaml",
        "command_mode_collect_sum.yaml",
        "pipe_mode_map_parse_int.yaml",
        "pipe_mode_bare_parse_int_error.yaml",
        "pipe_mode_sum_error.yaml",
        "pipe_mode_collect_error.yaml",
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
        "stdin-lines-take-early-stop.yaml",
        "flow-single-use-error.yaml",
        "flow-error-propagation-sum-on-flow.yaml",
        "refine-step-emit-deterministic.yaml",
        "rules-rule-emit-deterministic.yaml",
        "step-rule-helper-equivalence.yaml",
        "rules-identity-stage.yaml",
        "flow-keep-some-parse-int.yaml",
        "flow-tee-zip-list-pairs.yaml",
        "flow-zip-list-pairs.yaml",
        "flow-map-basic.yaml",
        "flow-filter-basic.yaml",
        "flow-map-filter-chain.yaml",
        "evolve-init-f-integer-progression.yaml",
        "evolve-init-f-doubles-from-seed.yaml",
        "seq-compatible-evolve-each-run.yaml",
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
        "error-pattern-guard-all-fail.yaml",
        "error-pattern-glob-malformed.yaml",
        "error-format-non-string-template.yaml",
        "error-format-first-class-constructor-non-string.yaml",
        "error-format-first-class-non-string-non-format.yaml",
        "error-format-field-empty-spec.yaml",
        "error-format-field-bare-width.yaml",
        "error-format-field-incomplete-align.yaml",
        "error-format-field-combined-spec.yaml",
        "error-format-field-zero-pad-non-numeric.yaml",
        "error-format-field-grouping-non-numeric.yaml",
        "error-format-field-precision-non-string-non-numeric.yaml",
        "error-format-field-bool-zero-pad.yaml",
        "error-format-compose-invalid-piece.yaml",
        "error-format-compose-missing-placeholder.yaml",
        "error-format-compose-non-list.yaml",
        "error-format-compose-string-argument.yaml",
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
