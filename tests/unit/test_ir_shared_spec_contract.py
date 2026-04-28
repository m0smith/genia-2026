from __future__ import annotations

from pathlib import Path

import pytest

from genia.interpreter import Parser, lex, lower_program
from hosts.python.ir_normalize import normalize_portable_ir
from tools.spec_runner.comparator import compare_spec
from tools.spec_runner.executor import ActualResult, execute_spec
from tools.spec_runner.loader import load_spec


REPO = Path(__file__).resolve().parents[2]
IR_DIR = REPO / "spec" / "ir"


def _lower_and_normalize(source: str) -> list[dict]:
    ast_nodes = Parser(lex(source)).parse_program()
    return normalize_portable_ir(lower_program(ast_nodes))


def test_normalized_ir_is_deterministic_across_repeated_runs() -> None:
    source = 'import python.json as pyjson\n"null" |> pyjson/loads'

    first = _lower_and_normalize(source)
    second = _lower_and_normalize(source)

    assert first == second


@pytest.mark.parametrize(
    "source, expected",
    [
        ("42", [{"node": "IrExprStmt", "expr": {"node": "IrLiteral", "value": 42}}]),
        ("value", [{"node": "IrExprStmt", "expr": {"node": "IrVar", "name": "value"}}]),
        (
            "f(1, 2)",
            [
                {
                    "node": "IrExprStmt",
                    "expr": {
                        "node": "IrCall",
                        "fn": {"node": "IrVar", "name": "f"},
                        "args": [
                            {"node": "IrLiteral", "value": 1},
                            {"node": "IrLiteral", "value": 2},
                        ],
                    },
                }
            ],
        ),
    ],
)
def test_representative_ir_nodes_normalize_to_portable_shape(source: str, expected: list[dict]) -> None:
    assert _lower_and_normalize(source) == expected


def test_pipeline_normalization_keeps_explicit_pipeline_shape() -> None:
    normalized = _lower_and_normalize("3 |> inc |> double")
    expr = normalized[0]["expr"]

    assert expr["node"] == "IrPipeline"
    assert expr["source"] == {"node": "IrLiteral", "value": 3}
    assert expr["stages"] == [
        {"node": "IrVar", "name": "inc"},
        {"node": "IrVar", "name": "double"},
    ]


def test_option_constructor_normalization_keeps_documented_portable_forms() -> None:
    normalized = _lower_and_normalize('[some(1), none("parse_failed", {source: "x"}), nil]')
    items = normalized[0]["expr"]["items"]

    assert items[0] == {"node": "IrOptionSome", "value": {"node": "IrLiteral", "value": 1}}
    assert items[1]["node"] == "IrOptionNone"
    assert items[1]["reason"] == {
        "node": "IrQuote",
        "expr": {"kind": "Literal", "value": "parse_failed"},
    }
    assert items[2] == {
        "node": "IrOptionNone",
        "reason": {"node": "IrLiteral", "value": "nil"},
        "context": None,
    }


def test_pattern_lowering_normalization_uses_only_documented_irpat_families() -> None:
    normalized = _lower_and_normalize(
        'classify(xs) = ([x, ..rest]) ? x > 0 -> some(x) | (_) -> nil'
    )
    clauses = normalized[0]["body"]["clauses"]

    assert clauses[0]["pattern"] == {
        "node": "IrPatTuple",
        "items": [
            {
                "node": "IrPatList",
                "items": [
                    {"node": "IrPatBind", "name": "x"},
                    {"node": "IrPatRest", "name": "rest"},
                ],
            }
        ],
    }
    assert clauses[1]["pattern"] == {
        "node": "IrPatTuple",
        "items": [{"node": "IrPatWildcard"}],
    }


def test_normalized_ir_does_not_leak_python_specific_formatting() -> None:
    normalized = _lower_and_normalize("3 |> inc |> double")
    rendered = repr(normalized)

    assert "SourceSpan" not in rendered
    assert "<memory>" not in rendered
    assert "span" not in rendered
    assert " at 0x" not in rendered
    assert "IrPipeline(" not in rendered


def test_compare_spec_reports_ir_mismatch_on_expected_shape_difference() -> None:
    spec = load_spec(IR_DIR / "pipeline-explicit.yaml")
    actual = execute_spec(spec)
    mutated_expected = [{"node": "IrExprStmt", "expr": {"node": "IrCall"}}]
    mismatched_spec = spec.__class__(
        name=spec.name,
        category=spec.category,
        source=spec.source,
        stdin=spec.stdin,
        expected_stdout=spec.expected_stdout,
        expected_stderr=spec.expected_stderr,
        expected_exit_code=spec.expected_exit_code,
        expected_ir=mutated_expected,
        path=spec.path,
    )

    failures = compare_spec(mismatched_spec, actual)

    assert len(failures) == 1
    assert failures[0].field == "ir"
    assert failures[0].expected == mutated_expected
    assert failures[0].actual == actual.ir


def test_loader_rejects_ir_spec_missing_expected_ir(tmp_path: Path) -> None:
    spec_path = tmp_path / "broken-ir.yaml"
    spec_path.write_text(
        "\n".join(
            [
                "name: broken-ir",
                "category: ir",
                "input:",
                "  source: |",
                "    1",
                "expected: {}",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match=r"missing required field: expected\.ir"):
        load_spec(spec_path)


def test_loader_rejects_ir_spec_with_eval_only_fields(tmp_path: Path) -> None:
    spec_path = tmp_path / "broken-fields.yaml"
    spec_path.write_text(
        "\n".join(
            [
                "name: broken-fields",
                "category: ir",
                "input:",
                "  source: |",
                "    1",
                "expected:",
                "  stdout: ''",
                "  stderr: ''",
                "  exit_code: 0",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match=r"unknown expected fields"):
        load_spec(spec_path)


def test_executor_dispatches_ir_category_to_ir_result_shape() -> None:
    spec = load_spec(IR_DIR / "call-spread.yaml")

    actual = execute_spec(spec)

    assert isinstance(actual, ActualResult)
    assert actual.ir == spec.expected_ir
    assert actual.stdout is None
    assert actual.stderr is None
    assert actual.exit_code is None
