import pytest

from genia import make_global_env, run_source
from genia.utf8 import format_debug


def test_force_delay_basic(run):
    assert run("force(delay(1 + 2))") == 3


def test_force_non_promise_passthrough(run):
    assert run("force(42)") == 42


def test_delay_does_not_eagerly_evaluate(run):
    src = """
    {
      n = 0
      p = delay({
        n = n + 1
        n
      })
      [n, force(p), n]
    }
    """
    assert run(src) == [0, 1, 1]


def test_promise_force_is_memoized(run):
    src = """
    {
      n = 0
      p = delay({
        n = n + 1
        n
      })
      [force(p), force(p), force(p)]
    }
    """
    assert run(src) == [1, 1, 1]


def test_promise_captures_lexical_environment(run):
    src = """
    {
      x = 10
      p = delay(x + 1)
      force(p)
    }
    """
    assert run(src) == 11


def test_promise_observes_lexical_rebinding_before_force(run):
    src = """
    {
      x = 10
      p = delay(x + 1)
      x = 20
      force(p)
    }
    """
    assert run(src) == 21


def test_stream_style_pair_tail_with_promises(run):
    src = """
    ones() = cons(1, delay(ones()))
    s = ones()
    [
      car(s),
      car(force(cdr(s))),
      car(force(cdr(force(cdr(s)))))
    ]
    """
    assert run(src) == [1, 1, 1]


def test_quote_delay_special_form_is_data(run):
    env = make_global_env([])
    result = run_source("quote(delay(x))", env)
    assert format_debug(result) == "(delay x)"


def test_delay_requires_exactly_one_argument():
    env = make_global_env([])
    with pytest.raises(SyntaxError, match=r"delay\(\.\.\.\) expects exactly one argument"):
        run_source("delay(1, 2)", env)


def test_delay_does_not_accept_spread():
    env = make_global_env([])
    with pytest.raises(SyntaxError, match=r"delay\(\.\.\.\) does not accept spread arguments"):
        run_source("delay(..xs)", env)


def test_failed_force_leaves_promise_retryable():
    env = make_global_env([])
    run_source(
        """
        attempts = 0
        current = () -> car(1)
        p = delay({
          attempts = attempts + 1
          current()
        })
        """,
        env,
    )

    with pytest.raises(TypeError, match="car expected a pair"):
        run_source("force(p)", env)

    assert run_source("attempts", env) == 1
    run_source("current = () -> attempts", env)
    assert run_source("[force(p), attempts]", env) == [2, 2]
