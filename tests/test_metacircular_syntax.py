import pytest

from genia import make_global_env, run_source
from genia.utf8 import format_debug


def _run(src: str):
    env = make_global_env([])
    return run_source(src, env)


def test_representation_truth_for_assignment():
    assert format_debug(_run("quote(x = 10)")) == "(assign x 10)"


def test_representation_truth_for_lambda():
    assert format_debug(_run("quote((x) -> x + 1)")) == "(lambda (x) (+ x 1))"


def test_representation_truth_for_application():
    assert format_debug(_run("quote(f(1, 2))")) == "(f 1 2)"


def test_representation_truth_for_block():
    src = """
    quote({
      x = 1
      x + 2
    })
    """
    assert format_debug(_run(src)) == "(block (assign x 1) (+ x 2))"


def test_representation_truth_for_match_expression():
    assert format_debug(_run("quote(0 -> 1 | _ -> 2)")) == "(match (clause 0 1) (clause _ 2))"


def test_self_evaluating_predicate(run):
    assert run("self_evaluating?(quote(42))") is True
    assert run('self_evaluating?(quote("x"))') is True
    assert run("self_evaluating?(quote(nil))") is True
    assert run("self_evaluating?(quote(none))") is True
    assert run("self_evaluating?(quote(x))") is False


def test_symbol_expression_predicate(run):
    assert run("symbol_expr?(quote(x))") is True
    assert run("symbol_expr?(quote(42))") is False


def test_quoted_expression_detection_and_selector(run):
    assert run("quoted_expr?(quote(quote(x)))") is True
    assert run("text_of_quotation(quote(quote(x))) == quote(x)") is True


def test_quasiquoted_expression_detection(run):
    assert run("quasiquoted_expr?(quote(quasiquote([a, unquote(x)])))") is True


def test_assignment_helpers(run):
    assert run("assignment_expr?(quote(x = 10))") is True
    assert run("assignment_name(quote(x = 10)) == quote(x)") is True
    assert run("assignment_value(quote(x = 10)) == quote(10)") is True


def test_lambda_helpers():
    assert _run("lambda_expr?(quote((x) -> x + 1))") is True
    assert format_debug(_run("lambda_params(quote((x) -> x + 1))")) == "(x)"
    assert format_debug(_run("lambda_body(quote((x) -> x + 1))")) == "(+ x 1)"


def test_application_helpers():
    assert _run("application_expr?(quote(f(1, 2)))") is True
    assert _run("operator(quote(f(1, 2))) == quote(f)") is True
    assert format_debug(_run("operands(quote(f(1, 2)))")) == "(1 2)"


def test_application_predicate_currently_matches_quoted_pair_data_too(run):
    assert run("application_expr?(quote([a, b]))") is True


def test_block_helpers():
    src = """
    e = quote({
      x = 1
      x + 2
    })
    [block_expr?(e), block_expressions(e)]
    """
    result = _run(src)
    assert result[0] is True
    assert format_debug(result[1]) == "((assign x 1) (+ x 2))"


def test_match_expression_predicate(run):
    assert run("match_expr?(quote(0 -> 1 | _ -> 2))") is True


def test_selector_failures_are_clear(run):
    with pytest.raises(TypeError, match="assignment_name expected an assignment expression"):
        run("assignment_name(quote(42))")
    with pytest.raises(TypeError, match="lambda_body expected a lambda expression"):
        run("lambda_body(quote(42))")
    with pytest.raises(TypeError, match="operator expected an application expression"):
        run("operator(quote(42))")
