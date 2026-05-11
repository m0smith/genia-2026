import pytest

from genia import make_global_env, run_source
from genia.interpreter import GeniaFlow


def test_adjacent_flow_map_filter_map_chain_is_represented_as_one_fused_flow():
    env = make_global_env()

    flow = run_source(
        """
        ["a", "bb", "ccc"]
          |> lines
          |> map((x) -> concat(x, "!"))
          |> filter((x) -> x != "bb!")
          |> map((x) -> concat(x, "?"))
        """,
        env,
    )

    assert isinstance(flow, GeniaFlow)
    assert flow.__class__.__name__ == "_FusedFlow"
    assert len(flow._stages) == 3
    assert repr(flow._upstream) == "<flow lines ready>"
    assert list(flow.consume()) == ["a!?", "ccc!?"]


def test_flow_map_filter_fusion_preserves_bounded_pulling_and_close():
    env = make_global_env()
    state = {"pulled": 0, "closed": 0}

    class ClosableCounter:
        def __init__(self):
            self._next = 0

        def __iter__(self):
            return self

        def __next__(self):
            value = self._next
            self._next += 1
            state["pulled"] += 1
            return value

        def close(self):
            state["closed"] += 1

    def ticks():
        return GeniaFlow(lambda: ClosableCounter(), label="ticks")

    env.set("ticks", ticks)

    assert run_source(
        """
        ticks()
          |> map((x) -> x + 1)
          |> filter((x) -> x % 2 == 0)
          |> map((x) -> x * 10)
          |> take(3)
          |> collect
        """,
        env,
    ) == [20, 40, 60]
    assert state == {"pulled": 6, "closed": 1}


def test_fused_flow_map_callback_error_propagates_and_closes_upstream():
    env = make_global_env()
    state = {"pulled": [], "closed": 0}
    mapper_error = RuntimeError("boom from mapper")

    class ClosableCounter:
        def __init__(self):
            self._next = 0

        def __iter__(self):
            return self

        def __next__(self):
            value = self._next
            self._next += 1
            state["pulled"].append(value)
            return value

        def close(self):
            state["closed"] += 1

    def ticks():
        return GeniaFlow(lambda: ClosableCounter(), label="ticks")

    def boom_on_three(value):
        if value == 3:
            raise mapper_error
        return value

    env.set("ticks", ticks)
    env.set("boom_on_three", boom_on_three)

    with pytest.raises(RuntimeError, match="boom from mapper") as exc_info:
        run_source(
            """
            ticks()
              |> map((x) -> x + 1)
              |> filter((x) -> x < 10)
              |> map(boom_on_three)
              |> collect
            """,
            env,
        )

    assert exc_info.value is mapper_error
    assert state == {"pulled": [0, 1, 2], "closed": 1}


def test_fused_flow_filter_callback_error_propagates_and_closes_upstream():
    env = make_global_env()
    state = {"pulled": [], "closed": 0}
    predicate_error = RuntimeError("boom from predicate")

    class ClosableCounter:
        def __init__(self):
            self._next = 0

        def __iter__(self):
            return self

        def __next__(self):
            value = self._next
            self._next += 1
            state["pulled"].append(value)
            return value

        def close(self):
            state["closed"] += 1

    def ticks():
        return GeniaFlow(lambda: ClosableCounter(), label="ticks")

    def boom_predicate_on_three(value):
        if value == 3:
            raise predicate_error
        return True

    env.set("ticks", ticks)
    env.set("boom_predicate_on_three", boom_predicate_on_three)

    with pytest.raises(RuntimeError, match="boom from predicate") as exc_info:
        run_source(
            """
            ticks()
              |> map((x) -> x + 1)
              |> filter(boom_predicate_on_three)
              |> map((x) -> x * 10)
              |> collect
            """,
            env,
        )

    assert exc_info.value is predicate_error
    assert state == {"pulled": [0, 1, 2], "closed": 1}


def test_fused_flow_still_enforces_single_use():
    env = make_global_env()

    flow = run_source(
        """
        ["1", "2", "3"]
          |> lines
          |> map((x) -> concat(x, "!"))
          |> filter((x) -> x != "2!")
        """,
        env,
    )

    assert flow.__class__.__name__ == "_FusedFlow"
    assert list(flow.consume()) == ["1!", "3!"]

    try:
        list(flow.consume())
    except RuntimeError as exc:
        assert str(exc) == "Flow has already been consumed"
    else:  # pragma: no cover - assertion path
        raise AssertionError("fused Flow was consumed twice without an error")


def test_list_map_filter_chain_remains_eager_reusable_list_behavior():
    env = make_global_env()

    result = run_source(
        """
        xs = [1, 2, 3]
        ys = xs |> map((x) -> x + 1) |> filter((x) -> x > 2)
        [ys, ys]
        """,
        env,
    )

    assert result == [[3, 4], [3, 4]]
