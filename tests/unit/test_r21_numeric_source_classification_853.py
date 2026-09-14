"""E21-1 (issue #853): numeric source classification and lexical exactness.

Covers docs/design/r21-numeric-source-portable-representation-contract.md
sections 2 and 3: Integer vs Decimal source classification, lexical/base-10
Decimal normalization with zero host binary-float construction during
classification, malformed-exponent rejection, and rejection of leading-dot
(.5) / trailing-dot (5.) forms.

This ticket does not touch Core IR / IrLiteral payloads (E21-2) or evaluator
Decimal runtime semantics (R22); it verifies only source classification.
"""
from __future__ import annotations

import ast
import inspect

import pytest

from src.genia.ast_nodes import Number
from src.genia.lexer import lex
from src.genia.numeric_source import NumericSource, classify_numeric_literal
from src.genia.parser import Parser


# ---------------------------------------------------------------------------
# classify_numeric_literal: pure classification, no host binary float
# ---------------------------------------------------------------------------

def test_classify_integer_source() -> None:
    result = classify_numeric_literal("42")
    assert result == NumericSource(kind="integer", digits="42", coefficient=None, exponent=None)


def test_classify_integer_strips_leading_zeros_but_keeps_zero() -> None:
    assert classify_numeric_literal("0").digits == "0"
    assert classify_numeric_literal("007").digits == "7"


def test_classify_decimal_dotted() -> None:
    result = classify_numeric_literal("1.25")
    assert result.kind == "decimal"
    assert result.coefficient == "125"
    assert result.exponent == "-2"


def test_classify_decimal_exponent_only() -> None:
    result = classify_numeric_literal("1e3")
    assert result.kind == "decimal"
    assert result.coefficient == "1"
    assert result.exponent == "3"


def test_classify_decimal_dot_exponent() -> None:
    result = classify_numeric_literal("1.25e-2")
    assert result.kind == "decimal"
    # 1.25e-2 = 125 * 10^-4
    assert result.coefficient == "125"
    assert result.exponent == "-4"


def test_classify_decimal_zero_canonicalizes_to_0_0() -> None:
    result = classify_numeric_literal("0.0")
    assert result.kind == "decimal"
    assert result.coefficient == "0"
    assert result.exponent == "0"

    result2 = classify_numeric_literal("0e5")
    assert result2.coefficient == "0"
    assert result2.exponent == "0"


@pytest.mark.parametrize(
    "spelling",
    ["1.0", "1.00", "100e-2", "1.000e0"],
)
def test_classify_equivalent_decimal_spellings_normalize_identically(spelling: str) -> None:
    result = classify_numeric_literal(spelling)
    assert result.kind == "decimal"
    assert (result.coefficient, result.exponent) == ("1", "0")


def test_classify_decimal_retains_decimal_kind_when_integral() -> None:
    # 100e-2 == 1 mathematically but must remain classified Decimal, not Integer
    result = classify_numeric_literal("100e-2")
    assert result.kind == "decimal"


def test_classify_never_calls_float() -> None:
    """The classification function must not construct a host binary float."""
    source = inspect.getsource(classify_numeric_literal)
    module = __import__("src.genia.numeric_source", fromlist=["*"])
    module_source = inspect.getsource(module)
    tree = ast.parse(module_source)
    float_calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "float"
    ]
    assert float_calls == [], "numeric_source module must never call float()"


# ---------------------------------------------------------------------------
# Lexer: exponent support and malformed-exponent rejection
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "source,expected_text",
    [
        ("42", "42"),
        ("1.25", "1.25"),
        ("1e3", "1e3"),
        ("1E+3", "1E+3"),
        ("1.25e-2", "1.25e-2"),
    ],
)
def test_lexer_produces_one_number_token(source: str, expected_text: str) -> None:
    tokens = lex(source)
    assert tokens[0].kind == "NUMBER"
    assert tokens[0].text == expected_text
    assert tokens[1].kind == "EOF"


@pytest.mark.parametrize("source", ["1e", "1e+", "1E", "2.5e"])
def test_lexer_rejects_malformed_exponent(source: str) -> None:
    with pytest.raises(SyntaxError, match="[Mm]alformed exponent"):
        lex(source)


def test_lexer_trailing_dot_leaves_bare_dot_token() -> None:
    tokens = lex("5.")
    assert tokens[0].kind == "NUMBER"
    assert tokens[0].text == "5"
    # the bare "." is not a valid token on its own in this grammar
    with pytest.raises(SyntaxError):
        lex(".")


# ---------------------------------------------------------------------------
# Parser: AST Number node carries classification metadata
# ---------------------------------------------------------------------------

def _parse_expr(source: str) -> Number:
    tokens = lex(source)
    parser = Parser(tokens, source=source, filename="<test>")
    program = parser.parse_program()
    node = program[0]
    # ExprStmt wraps bare expressions
    return getattr(node, "expr", node)


def test_parser_classifies_integer_literal() -> None:
    node = _parse_expr("42")
    assert isinstance(node, Number)
    assert node.value == 42
    assert node.source_kind == "integer"
    assert node.digits == "42"


def test_parser_classifies_decimal_literal() -> None:
    node = _parse_expr("1.25")
    assert isinstance(node, Number)
    assert node.value == 1.25
    assert node.source_kind == "decimal"
    assert node.coefficient == "125"
    assert node.exponent == "-2"


def test_parser_classifies_exponent_only_decimal_literal() -> None:
    node = _parse_expr("1e3")
    assert isinstance(node, Number)
    assert node.value == 1000.0
    assert node.source_kind == "decimal"
    assert node.coefficient == "1"
    assert node.exponent == "3"


def test_parser_rejects_leading_dot_literal() -> None:
    with pytest.raises(SyntaxError):
        _parse_expr(".5")


def test_parser_rejects_trailing_dot_literal() -> None:
    with pytest.raises(SyntaxError):
        _parse_expr("5.")


def test_parser_unary_negative_is_unary_minus_over_positive_decimal_literal() -> None:
    from src.genia.ast_nodes import Unary

    node = _parse_expr("-1.25")
    assert isinstance(node, Unary)
    assert node.op == "MINUS"
    assert isinstance(node.expr, Number)
    assert node.expr.value == 1.25
    assert node.expr.source_kind == "decimal"


def test_parser_huge_integer_literal_preserves_exact_digits() -> None:
    huge = "123456789012345678901234567890"
    node = _parse_expr(huge)
    assert isinstance(node, Number)
    assert node.value == int(huge)
    assert node.source_kind == "integer"
    assert node.digits == huge
