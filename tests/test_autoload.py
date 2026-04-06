from pathlib import Path

import pytest

from genia import make_global_env, run_source


def run_with_env(src: str):
    env = make_global_env([])
    return run_source(src, env)


def test_autoload_count():
    assert run_with_env("count([1, 2, 3, 4])") == 4


def test_autoload_sum():
    assert run_with_env("sum([1, 2, 3, 4])") == 10


def test_autoload_list_and_first():
    assert run_with_env("list(1, 2, 3)") == [1, 2, 3]
    assert run_with_env("unwrap_or(0, first([7, 8, 9]))") == 7
    assert run_with_env("unwrap_or(0, first_opt([7, 8, 9]))") == 7
    assert run_with_env("unwrap_or(0, last([7, 8, 9]))") == 9
    assert run_with_env("unwrap_or(0, find_opt((x) -> x == 8, [7, 8, 9]))") == 8


def test_autoload_length_and_reverse():
    assert run_with_env("length([1, 2, 3, 4])") == 4
    assert run_with_env("reverse([1, 2, 3])") == [3, 2, 1]


def test_autoload_range():
    assert run_with_env("range(4)") == [0, 1, 2, 3]
    assert run_with_env("range(1, 4)") == [1, 2, 3, 4]
    assert run_with_env("range(1, 7, 3)") == [1, 4, 7]


def test_autoload_math_helpers():
    assert run_with_env("inc(41)") == 42
    assert run_with_env("abs(-9)") == 9


def test_autoload_math_then_list_no_duplicate_function_error():
    env = make_global_env([])
    assert run_source("inc(1)", env) == 2
    assert run_source("[1, 2, 3] |> map(inc)", env) == [2, 3, 4]


def test_autoload_awkify():
    src = """
    odd_rows(n, row) =
      (n, row) ? n % 2 == 1 -> row |
      (_, _) -> nil
    awkify(odd_rows, ["a", "b", "c", "d"])
    """
    assert run_with_env(src) == ["a", "c"]


def test_autoload_reduce_direct():
    src = """
    reduce((acc, x) -> acc + x, 0, [1, 2, 3, 4])
    """
    assert run_with_env(src) == 10


def test_autoload_map_and_filter():
    src = """
    [map((x) -> x * 2, [1, 2, 3]), filter((x) -> x > 2, [1, 2, 3, 4])]
    """
    assert run_with_env(src) == [[2, 4, 6], [3, 4]]


def test_autoload_same_file_loads_helper_too():
    env = make_global_env([])
    assert run_source("count([1, 2, 3])", env) == 3
    assert run_source("reduce((acc, x) -> acc + x, 0, [1, 2, 3])", env) == 6


def test_autoload_missing_file():
    env = make_global_env([])
    env.register_autoload("ghost", 1, "std/prelude/does_not_exist.genia")
    with pytest.raises(FileNotFoundError):
        run_source("ghost(1)", env)


def test_autoload_mutual_tail_recursion_works(tmp_path: Path):
    std = tmp_path / "std" / "prelude"
    std.mkdir(parents=True)

    (std / "a.genia").write_text(
        "a(n) =\n"
        "  0 -> 0 |\n"
        "  n -> b(n - 1)\n",
        encoding="utf-8",
    )
    (std / "b.genia").write_text(
        "b(n) =\n"
        "  0 -> 0 |\n"
        "  n -> a(n - 1)\n",
        encoding="utf-8",
    )

    env = make_global_env([])
    env.register_autoload("a", 1, str((std / "a.genia").resolve()))
    env.register_autoload("b", 1, str((std / "b.genia").resolve()))

    assert run_source("a(5000)", env) == 0
