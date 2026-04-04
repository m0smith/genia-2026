import pytest

from genia import make_global_env, run_source
from genia.interpreter import GeniaFlow


def test_flow_reusable_stage_and_run(capsys):
    src = """
    clean(flow) =
      flow |> lines |> map(trim) |> filter((x) -> x != "")

    stdin |> clean |> each(print) |> run
    """
    env = make_global_env(stdin_data=["  a  ", "", " b "])
    result = run_source(src, env)
    captured = capsys.readouterr().out

    assert result is None
    assert captured == "a\nb\n"


def test_flow_is_single_use():
    src = """
    x = stdin |> lines
    x |> each(print) |> run
    x |> each(print) |> run
    """
    env = make_global_env(stdin_data=["a", "b"])
    with pytest.raises(RuntimeError, match="Flow has already been consumed"):
        run_source(src, env)


def test_collect_materializes_reusable_data():
    src = """
    xs = stdin |> lines |> collect
    [xs, xs]
    """
    env = make_global_env(stdin_data=["a", "b"])
    assert run_source(src, env) == [["a", "b"], ["a", "b"]]


def test_take_and_head_aliases():
    env = make_global_env(stdin_data=["a", "b", "c", "d"])
    assert run_source("stdin |> lines |> take(2) |> collect", env) == ["a", "b"]

    env = make_global_env(stdin_data=["a", "b", "c", "d"])
    assert run_source("stdin |> lines |> head |> collect", env) == ["a"]

    env = make_global_env(stdin_data=["a", "b", "c", "d"])
    assert run_source("stdin |> lines |> head(3) |> collect", env) == ["a", "b", "c"]


def test_take_zero_does_not_pull_upstream():
    env = make_global_env()
    state = {"pulled": 0}

    def ticks():
        def iterator():
            i = 0
            while True:
                state["pulled"] += 1
                yield i
                i += 1

        return GeniaFlow(iterator, label="ticks")

    env.set("ticks", ticks)
    assert run_source("ticks() |> take(0) |> collect", env) == []
    assert state["pulled"] == 0


def test_take_stops_without_overpulling_generator_backed_flow():
    env = make_global_env()
    state = {"pulled": 0}

    def ticks():
        def iterator():
            i = 0
            while True:
                state["pulled"] += 1
                yield i
                i += 1

        return GeniaFlow(iterator, label="ticks")

    env.set("ticks", ticks)
    assert run_source("ticks() |> take(3) |> collect", env) == [0, 1, 2]
    assert state["pulled"] == 3


def test_stdin_flow_binding_is_lazy_and_stops_on_take():
    calls = 0
    state = {"pulled": 0}

    def provider():
        nonlocal calls
        calls += 1

        def iterator():
            for item in ["a", "b", "c", "d"]:
                state["pulled"] += 1
                yield item

        return iterator()

    env = make_global_env(stdin_provider=provider)
    assert calls == 0
    assert state["pulled"] == 0
    assert run_source("stdin |> lines |> take(2) |> collect", env) == ["a", "b"]
    assert calls == 1
    assert state["pulled"] == 2
