import pytest

from genia import make_global_env, run_source
from genia.utf8 import format_debug


def _run(src: str):
    env = make_global_env([])
    return run_source(src, env)


def test_quasiquote_without_unquote_matches_quote(run):
    assert run("quasiquote([a, b, c]) == quote([a, b, c])") is True


def test_quasiquote_basic_unquote():
    src = """
    x = 10
    quasiquote([a, unquote(x), c])
    """
    assert format_debug(_run(src)) == "(a 10 c)"


def test_quasiquote_nested_structure():
    src = """
    x = 10
    quasiquote([outer, [inner, unquote(x)]])
    """
    assert format_debug(_run(src)) == "(outer (inner 10))"


def test_quasiquote_does_not_evaluate_plain_expression(run):
    assert run("quasiquote(1 + 2) != 3") is True
    assert format_debug(_run("quasiquote(1 + 2)")) == "(+ 1 2)"


def test_unquote_outside_quasiquote_fails(run):
    with pytest.raises(RuntimeError, match=r"unquote\(\.\.\.\) is only valid inside quasiquote"):
        run("unquote(1)")


def test_unquote_splicing_outside_quasiquote_fails(run):
    with pytest.raises(RuntimeError, match=r"unquote_splicing\(\.\.\.\) is only valid inside quasiquote"):
        run("unquote_splicing([1, 2])")


def test_nested_quasiquote_depth_behavior():
    src = """
    x = 7
    quasiquote([a, quasiquote([b, unquote(x)]), c])
    """
    assert format_debug(_run(src)) == "(a (quasiquote (b (unquote x))) c)"


def test_quasiquote_map_support():
    src = """
    x = 3
    q = quasiquote({ value: unquote(x) })
    map_get(q, quote(value))
    """
    assert _run(src) == 3


def test_unquote_splicing_in_list_context():
    src = """
    xs = [1, 2]
    quasiquote([a, unquote_splicing(xs), b])
    """
    assert format_debug(_run(src)) == "(a 1 2 b)"


def test_unquote_splicing_accepts_pair_chain_input():
    src = """
    xs = quote([1, 2])
    quasiquote([a, unquote_splicing(xs), b])
    """
    assert format_debug(_run(src)) == "(a 1 2 b)"


def test_invalid_unquote_splicing_usage_fails(run):
    with pytest.raises(RuntimeError, match=r"unquote_splicing\(\.\.\.\) is only valid in quasiquote list context"):
        run(
            """
            xs = [1, 2]
            quasiquote(unquote_splicing(xs))
            """
        )


def test_invalid_unquote_splicing_value_type_fails(run):
    with pytest.raises(TypeError, match="unquote_splicing expected a list or nil-terminated pair chain"):
        run("quasiquote([a, unquote_splicing(1), b])")
