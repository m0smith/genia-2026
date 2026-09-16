"""Verifies the runnable examples quoted in docs/releases/R21.md are accurate.

Not a general-purpose test; exists so the release doc's small examples stay
truthful if the underlying behavior ever changes. Mirrors
tests/unit/test_r19_release_doc_examples.py's pattern.
"""
from __future__ import annotations

from genia import make_global_env, run_source
from src.genia.ir import IrLiteral
from src.genia.lexer import lex
from src.genia.lowering import lower_node
from src.genia.parser import Parser


def _run(src: str):
    env = make_global_env([])
    return run_source(src, env)


def _lower_expr(src: str):
    tokens = lex(src)
    parser = Parser(tokens, source=src, filename="<test>")
    program = parser.parse_program()
    node = program[0]
    node = getattr(node, "expr", node)
    return lower_node(node)


def test_release_doc_integer_and_decimal_source_examples():
    assert _run("1") == 1
    assert _run("1.0") == 1.0
    assert _run("1.25") == 1.25
    assert _run("1e3") == 1000.0
    assert _run("1E+3") == 1000.0
    assert _run("1.25e-2") == 0.0125


def test_release_doc_leading_trailing_dot_rejected():
    for src in (".5", "5."):
        try:
            _run(src)
            assert False, f"expected SyntaxError for {src!r}"
        except SyntaxError:
            pass


def test_release_doc_malformed_exponent_rejected():
    for src in ("1e", "1e+"):
        try:
            _run(src)
            assert False, f"expected SyntaxError for {src!r}"
        except SyntaxError:
            pass


def test_release_doc_equivalent_decimal_spellings_equal():
    assert _run("1.0 == 1.00") is True
    assert _run("100e-2 == 1") is True


def test_release_doc_unary_negative_example():
    assert _run("-1.25") == -1.25


def test_release_doc_integer_tagged_payload_example():
    ir = _lower_expr("42")
    assert isinstance(ir, IrLiteral)
    assert ir.value == {"kind": "integer", "digits": "42"}


def test_release_doc_decimal_tagged_payload_example():
    ir = _lower_expr("1.25")
    assert isinstance(ir, IrLiteral)
    assert ir.value == {"kind": "decimal", "coefficient": "125", "exponent": "-2"}
