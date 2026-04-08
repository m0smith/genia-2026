import pytest

from genia.utf8 import format_debug

from genia import make_global_env, run_source


def run_with_env(src: str):
    env = make_global_env([])
    return run_source(src, env)


def test_self_tail_recursion_large_depth():
    src = """
    sum_to(n, acc) =
      (0, acc) -> acc |
      (n, acc) -> sum_to(n - 1, acc + n)

    sum_to(100000, 0)
    """
    assert run_with_env(src) == 5000050000


def test_mutual_tail_recursion_large_depth():
    src = """
    even(n) =
      0 -> true |
      n -> odd(n - 1)

    odd(n) =
      0 -> false |
      n -> even(n - 1)

    even(100000)
    """
    assert run_with_env(src) is True


def test_tail_call_in_final_pipeline_stage_uses_constant_stack():
    src = """
    sum_pipe(acc, n) =
      (acc, 0) -> acc |
      (acc, n) -> (n - 1) |> sum_pipe(acc + n)

    sum_pipe(0, 50000)
    """
    assert run_with_env(src) == 1250025000


def test_tail_call_in_final_block_expression_uses_constant_stack():
    src = """
    sum_block(n, acc) {
      acc
      (n, acc) ? n == 0 -> acc |
      (n, acc) -> sum_block(n - 1, acc + n)
    }

    sum_block(50000, 0)
    """
    assert run_with_env(src) == 1250025000


def test_non_tail_recursion_still_uses_stack():
    src = """
    countdown(n) =
      0 -> 0 |
      n -> 1 + countdown(n - 1)

    countdown(5000)
    """
    with pytest.raises(RecursionError):
        run_with_env(src)


def test_nth_loop_optimization_correctness():
    src = """
    nth(n, xs) =
      (_, []) -> nil |
      (0, [x, .._]) -> x |
      (n, [_, ..rest]) -> nth(n - 1, rest)

    [nth(0, [1, 2, 3]), nth(2, [1, 2, 3]), nth(5, [1, 2, 3])]
    """
    assert format_debug(run_with_env(src)) == '[1, 3, none("nil")]'


def test_nth_negative_index_returns_nil():
    src = """
    nth(n, xs) =
      (_, []) -> nil |
      (0, [x, .._]) -> x |
      (n, [_, ..rest]) -> nth(n - 1, rest)

    nth(-1, [1, 2, 3])
    """
    assert format_debug(run_with_env(src)) == 'none("nil")'


def test_debug_print_for_list_traversal_optimization(monkeypatch, capsys):
    monkeypatch.setenv("GENIA_DEBUG_OPT", "1")
    src = """
    nth(n, xs) =
      (_, []) -> nil |
      (0, [x, .._]) -> x |
      (n, [_, ..rest]) -> nth(n - 1, rest)

    nth(0, [1])
    """
    run_with_env(src)
    captured = capsys.readouterr()
    assert "Applied list traversal optimization to function nth/2" in captured.out
