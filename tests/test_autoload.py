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


def test_autoload_reduce_direct():
    src = """
    reduce((acc, x) -> acc + x, 0, [1, 2, 3, 4])
    """
    assert run_with_env(src) == 10


def test_autoload_same_file_loads_helper_too():
    env = make_global_env([])
    assert run_source("count([1, 2, 3])", env) == 3
    assert run_source("reduce((acc, x) -> acc + x, 0, [1, 2, 3])", env) == 6


def test_autoload_missing_file():
    env = make_global_env([])
    env.register_autoload("ghost", 1, "std/prelude/does_not_exist.genia")
    with pytest.raises(FileNotFoundError):
        run_source("ghost(1)", env)


def test_autoload_mutual_recursion_raises_recursion_error(tmp_path: Path):
    std = tmp_path / "std" / "prelude"
    std.mkdir(parents=True)

    (std / "a.genia").write_text(
        "a() = b()\n",
        encoding="utf-8",
    )
    (std / "b.genia").write_text(
        "b() = a()\n",
        encoding="utf-8",
    )

    env = make_global_env([])
    env.register_autoload("a", 0, str((std / "a.genia").resolve()))
    env.register_autoload("b", 0, str((std / "b.genia").resolve()))

    with pytest.raises(RecursionError):
        run_source("a()", env)