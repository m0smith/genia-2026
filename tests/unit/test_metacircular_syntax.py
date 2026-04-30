import pytest

from genia import make_global_env, run_source
from genia.utf8 import format_debug


def _run(src: str):
    env = make_global_env([])
    return run_source(src, env)


def test_representation_truth_for_assignment():
    assert format_debug(_run("quote(x = 10)")) == "(assign x 10)"


def test_representation_truth_for_lambda():
    assert format_debug(_run("quote((x) -> x + 1)")) == "(lambda (x) (app + x 1))"


def test_representation_truth_for_application():
    assert format_debug(_run("quote(f(1, 2))")) == "(app f 1 2)"


def test_representation_truth_for_block():
    src = """
    quote({
      x = 1
      x + 2
    })
    """
    assert format_debug(_run(src)) == "(block (assign x 1) (app + x 2))"


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
    assert format_debug(_run("lambda_body(quote((x) -> x + 1))")) == "(app + x 1)"


def test_application_helpers():
    assert _run("application_expr?(quote(f(1, 2)))") is True
    assert _run("operator(quote(f(1, 2))) == quote(f)") is True
    assert format_debug(_run("operands(quote(f(1, 2)))")) == "(1 2)"


def test_quoted_data_list_is_not_an_application(run):
    assert run("application_expr?(quote([a, b]))") is False


def test_characterization_for_quoted_data_list_shape():
    assert format_debug(_run("quote([f, 1, 2])")) == "(f 1 2)"


def test_nested_quoted_data_list_stays_data(run):
    assert run("application_expr?(car(cdr(quote([outer, [f, 1, 2]]))))") is False


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
    assert format_debug(result[1]) == "((assign x 1) (app + x 2))"


def test_match_expression_predicate(run):
    assert run("match_expr?(quote(0 -> 1 | _ -> 2))") is True


def test_match_branch_helpers(run):
    src = """
    branches = match_branches(quote(0 -> 1 | x ? x > 0 -> x))
    first_branch = car(branches)
    second_branch = car(cdr(branches))
    [
      branch_pattern(first_branch) == quote(0),
      branch_has_guard?(first_branch),
      branch_body(first_branch) == quote(1),
      branch_pattern(second_branch) == quote(x),
      branch_has_guard?(second_branch),
      branch_guard(second_branch) == quote(x > 0),
      branch_body(second_branch) == quote(x)
    ]
    """
    assert run(src) == [True, False, True, True, True, True, True]


def test_selector_failures_are_clear(run):
    with pytest.raises(TypeError, match="assignment_name expected an assignment expression"):
        run("assignment_name(quote(42))")
    with pytest.raises(TypeError, match="lambda_body expected a lambda expression"):
        run("lambda_body(quote(42))")
    with pytest.raises(TypeError, match="operator expected an application expression"):
        run("operator(quote(42))")
    with pytest.raises(TypeError, match="operator expected an application expression"):
        run("operator(quote([f, 1, 2]))")
    with pytest.raises(TypeError, match="match_branches expected a match expression"):
        run("match_branches(quote(42))")
    with pytest.raises(TypeError, match="branch_pattern expected a match branch"):
        run("branch_pattern(quote(42))")
    with pytest.raises(TypeError, match="branch_guard expected a guarded match branch"):
        run("branch_guard(car(match_branches(quote(_ -> 1))))")
