import pytest

from genia import make_global_env, run_source
from genia.utf8 import format_debug


def _run(src: str):
    env = make_global_env([])
    return run_source(src, env)


def test_basic_cons_car_cdr(run):
    assert run("car(cons(1, 2))") == 1
    assert run("cdr(cons(1, 2))") == 2


def test_pair_list_structure(run):
    src = """
    xs = cons(1, cons(2, cons(3, nil)))
    [car(xs), car(cdr(xs)), car(cdr(cdr(xs)))]
    """
    assert run(src) == [1, 2, 3]


def test_pair_structural_equality(run):
    assert run("cons(1, cons(2, nil)) == cons(1, cons(2, nil))") is True


def test_quote_of_list_produces_pair_chain(run):
    assert run("pair?(quote([a, b]))") is True
    assert run("car(quote([a, b])) == quote(a)") is True
    assert run("pair?(cdr(quote([a, b])))") is True
    assert run("null?(cdr(cdr(quote([a, b]))))") is True


def test_null_predicate(run):
    assert run("null?(nil)") is True
    assert run("null?(cons(1, nil))") is False


def test_quote_nested_pair_structure_works_with_symbols_and_lists():
    assert format_debug(_run("quote([a, [b, c]])")) == "(a (b c))"


def test_pair_predicate_distinguishes_lists(run):
    assert run("pair?(cons(1, nil))") is True
    assert run("pair?([1, 2])") is False


def test_pair_debug_format_is_readable():
    assert format_debug(_run("cons(1, 2)")) == "(1 . 2)"
    assert format_debug(_run("cons(1, cons(2, cons(3, nil)))")) == "(1 2 3)"


def test_car_and_cdr_reject_non_pairs():
    with pytest.raises(TypeError, match="car expected a pair"):
        _run("car(1)")
    with pytest.raises(TypeError, match="cdr expected a pair"):
        _run("cdr(nil)")
