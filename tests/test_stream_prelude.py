from pathlib import Path

from genia import make_global_env, run_source


def test_infinite_ones_stream(run):
    src = """
    ones() =
      stream_cons(1, () -> ones())

    stream_take(3, ones())
    """
    assert run(src) == [1, 1, 1]


def test_naturals_stream(run):
    src = """
    from(n) =
      stream_cons(n, () -> from(n + 1))

    stream_take(5, from(1))
    """
    assert run(src) == [1, 2, 3, 4, 5]


def test_stream_map(run):
    src = """
    from(n) =
      stream_cons(n, () -> from(n + 1))

    stream_take(5, stream_map((x) -> x + 1, from(0)))
    """
    assert run(src) == [1, 2, 3, 4, 5]


def test_stream_filter(run):
    src = """
    from(n) =
      stream_cons(n, () -> from(n + 1))

    stream_take(5, stream_filter((x) -> x % 2 == 0, from(1)))
    """
    assert run(src) == [2, 4, 6, 8, 10]


def test_stream_take_one_is_lazy_enough(run):
    src = """
    from(n) =
      stream_cons(n, () -> from(n + 1))

    stream_take(1, from(1))
    """
    assert run(src) == [1]


def test_direct_stream_prelude_load_without_autoload():
    env = make_global_env([])
    prelude_path = Path("src/genia/std/prelude/stream.genia")
    run_source(prelude_path.read_text(encoding="utf-8"), env, filename=str(prelude_path.resolve()))
    assert run_source("stream_take(3, stream_cons(1, () -> stream_cons(2, () -> stream_cons(3, () -> nil))))", env) == [1, 2, 3]
