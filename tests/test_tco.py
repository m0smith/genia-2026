import pytest

from genia import make_global_env, run_source


def run_with_env(src: str):
    env = make_global_env([])
    return run_source(src, env)


def test_self_tail_recursion_large_depth():
    src = """
    sum_to(n, acc) =
      (0, acc) -> acc |
      (n, acc) -> sum_to(n - 1, acc + n)

    sum_to(5000, 0)
    """
    assert run_with_env(src) == 12502500


def test_non_tail_recursion_still_uses_stack():
    src = """
    countdown(n) =
      0 -> 0 |
      n -> 1 + countdown(n - 1)

    countdown(5000)
    """
    with pytest.raises(RecursionError):
        run_with_env(src)
