import pytest

from genia import make_global_env, run_source
from genia.interpreter import GeniaFlow


def make_number_flow_env(values):
    env = make_global_env()

    def numbers():
        return GeniaFlow(lambda: iter(values), label="numbers")

    env.set("numbers", numbers)
    return env


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


def test_rules_zero_rules_stage_is_identity_for_any_flow():
    env = make_number_flow_env([1, 2, 3])
    src = """
    identity = rules()
    numbers() |> identity |> collect
    """
    assert run_source(src, env) == [1, 2, 3]


def test_rules_one_rule_emits_one_value():
    env = make_number_flow_env([1, 2, 3, 4])
    src = """
    only_even(record, ctx) =
      (record, ctx) ? record % 2 == 0 -> rule_emit(record * 10) |
      (_, _) -> rule_skip()

    numbers() |> rules(only_even) |> collect
    """
    assert run_source(src, env) == [20, 40]


def test_rules_one_rule_emits_multiple_values():
    env = make_number_flow_env([3, 4])
    src = """
    fanout(record, ctx) = rule_emit_many([record, record + 100])

    numbers() |> rules(fanout) |> collect
    """
    assert run_source(src, env) == [3, 103, 4, 104]


def test_rules_later_rules_see_rewritten_record():
    env = make_number_flow_env([1, 2, 3])
    src = """
    rewrite(record, ctx) =
      (record, ctx) ? record == 2 -> rule_set(20) |
      (_, _) -> rule_skip()

    emit(record, ctx) = rule_emit(record)

    numbers() |> rules(rewrite, emit) |> collect
    """
    assert run_source(src, env) == [1, 20, 3]


def test_rules_ctx_persists_across_multiple_input_records():
    env = make_number_flow_env([1, 2, 3])
    src = """
    running_total(record, ctx) = {
      total = unwrap_or(0, get("total", ctx))
      next = total + record
      rule_step(record, map_put(ctx, "total", next), [next])
    }

    numbers() |> rules(running_total) |> collect
    """
    assert run_source(src, env) == [1, 3, 6]


def test_rules_halt_stops_later_rules_for_current_record():
    env = make_number_flow_env([1, 2, 3])
    src = """
    stop_here(record, ctx) = some({ emit: [record], halt: true })
    later(record, ctx) = rule_emit(record + 100)

    numbers() |> rules(stop_here, later) |> collect
    """
    assert run_source(src, env) == [1, 2, 3]


def test_rules_invalid_non_option_result_errors_clearly():
    env = make_number_flow_env([1])
    src = """
    bad(record, ctx) = 42

    numbers() |> rules(bad) |> collect
    """
    with pytest.raises(RuntimeError, match=r"invalid-rules-result: rule 1 returned 42; expected none\(\.\.\.\) or some\(result\)"):
        run_source(src, env)


def test_rules_invalid_emit_shape_errors_clearly():
    env = make_number_flow_env([1])
    src = """
    bad(record, ctx) = some({ emit: 42 })

    numbers() |> rules(bad) |> collect
    """
    with pytest.raises(RuntimeError, match=r"invalid-rules-result: rule 1 returned emit = 42; expected a list"):
        run_source(src, env)


def test_rules_compose_with_existing_flow_helpers_and_run(capsys):
    src = """
    shout(record, ctx) = rule_emit(upper(record))

    stdin |> lines |> rules(shout) |> head(2) |> each(print) |> run
    """
    env = make_global_env(stdin_data=["a", "b", "c"])
    result = run_source(src, env)
    captured = capsys.readouterr().out

    assert result is None
    assert captured == "A\nB\n"
