import pytest

from genia import make_global_env, run_source
from genia.interpreter import GeniaFlow
from genia.utf8 import format_debug


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

    assert result == run_source("nil", make_global_env([]))
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


def test_partially_consumed_flow_cannot_be_reused():
    src = """
    x = stdin |> lines
    first = x |> head(1) |> collect
    again = x |> collect
    [first, again]
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


def test_flow_and_value_bridges_remain_explicit():
    env = make_global_env(stdin_data=["a", "b"])
    with pytest.raises(TypeError, match="each expected a flow, received list"):
        run_source("stdin |> lines |> collect |> each(print) |> run", env)


def test_invalid_flow_source_reports_clear_runtime_error():
    env = make_global_env()
    env.set("badflow", lambda: GeniaFlow(lambda: None, label="badflow"))
    with pytest.raises(TypeError, match="Flow source badflow did not produce an iterable"):
        run_source("badflow() |> collect", env)


def test_take_and_head_aliases():
    env = make_global_env(stdin_data=["a", "b", "c", "d"])
    assert run_source("stdin |> lines |> take(2) |> collect", env) == ["a", "b"]

    env = make_global_env(stdin_data=["a", "b", "c", "d"])
    assert run_source("stdin |> lines |> head |> collect", env) == ["a"]

    env = make_global_env(stdin_data=["a", "b", "c", "d"])
    assert run_source("stdin |> lines |> head(3) |> collect", env) == ["a", "b", "c"]


def test_flow_wrappers_autoload_as_function_values():
    env = make_global_env(stdin_data=["a", "b"])
    src = """
    source = lines
    sink = collect
    stdin |> source |> sink
    """
    assert run_source(src, env) == ["a", "b"]


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


def test_rules_none_with_reason_and_context_remains_no_effect():
    env = make_number_flow_env([1, 2])
    src = """
    no_match(record, ctx) =
      (record, ctx) ? record == 1 -> none("no-match") |
      (_, _) -> none("no-match", { record: record })

    emit(record, ctx) = rule_emit(record)

    numbers() |> rules(no_match, emit) |> collect
    """
    assert run_source(src, env) == [1, 2]


def test_rules_some_map_defaults_record_ctx_emit_and_halt():
    env = make_number_flow_env([1, 2, 3])
    src = """
    remember(record, ctx) = some({ ctx: map_put(ctx, "last", record) })

    rewrite(record, ctx) =
      (record, ctx) ? record == 2 -> some({ record: 20 }) |
      (_, _) -> some({})

    emit(record, ctx) = rule_emit([record, unwrap_or(0, get("last", ctx))])

    numbers() |> rules(remember, rewrite, emit) |> collect
    """
    assert run_source(src, env) == [[1, 1], [20, 2], [3, 3]]


def test_rules_invalid_non_option_result_errors_clearly():
    env = make_number_flow_env([1])
    src = """
    bad(record, ctx) = 42

    numbers() |> rules(bad) |> collect
    """
    with pytest.raises(RuntimeError, match=r"invalid-rules-result: rule 1 returned 42; expected none\(\.\.\.\) or some\(result\)"):
        run_source(src, env)


def test_rules_invalid_some_non_map_result_errors_clearly():
    env = make_number_flow_env([1])
    src = """
    bad(record, ctx) = some(42)

    numbers() |> rules(bad) |> collect
    """
    with pytest.raises(RuntimeError, match=r"invalid-rules-result: rule 1 returned some\(result\) with 42; expected a map"):
        run_source(src, env)


def test_rules_invalid_emit_shape_errors_clearly():
    env = make_number_flow_env([1])
    src = """
    bad(record, ctx) = some({ emit: 42 })

    numbers() |> rules(bad) |> collect
    """
    with pytest.raises(RuntimeError, match=r"invalid-rules-result: rule 1 returned emit = 42; expected a list"):
        run_source(src, env)


def test_rules_invalid_halt_shape_errors_clearly():
    env = make_number_flow_env([1])
    src = """
    bad(record, ctx) = some({ emit: [record], halt: 42 })

    numbers() |> rules(bad) |> collect
    """
    with pytest.raises(RuntimeError, match=r"invalid-rules-result: rule 1 returned halt = 42; expected a boolean"):
        run_source(src, env)


def test_rules_compose_with_existing_flow_helpers_and_run(capsys):
    src = """
    shout(record, ctx) = rule_emit(upper(record))

    stdin |> lines |> rules(shout) |> head(2) |> each(print) |> run
    """
    env = make_global_env(stdin_data=["a", "b", "c"])
    result = run_source(src, env)
    captured = capsys.readouterr().out

    assert result == run_source("nil", make_global_env([]))
    assert captured == "A\nB\n"


def test_none_input_short_circuits_before_flow_stage_execution(capsys):
    src = """
    none("missing-key", { key: "name" }) |> each(print) |> run
    """
    env = make_global_env(stdin_data=["a", "b"])
    result = run_source(src, env)
    captured = capsys.readouterr().out

    assert format_debug(result) == 'none("missing-key", {key: "name"})'
    assert captured == ""


def test_none_result_from_flow_stage_short_circuits_later_stages(capsys):
    src = """
    stop(flow) = none("stopped", { stage: "stop" })
    stdin |> lines |> stop |> each(print) |> run
    """
    env = make_global_env(stdin_data=["a", "b"])
    result = run_source(src, env)
    captured = capsys.readouterr().out

    assert format_debug(result) == 'none("stopped", {stage: "stop"})'
    assert captured == ""


def test_keep_some_else_emits_unwrapped_successes_and_routes_original_failures():
    src = """
    dead = ref([])

    remember_dead(x) = ref_update(dead, (xs) -> append(xs, [x]))

    rows() = ["10", "oops", "20"]

    [
      rows() |> lines |> keep_some_else(parse_int, remember_dead) |> collect,
      ref_get(dead)
    ]
    """
    env = make_global_env([])
    assert run_source(src, env) == [[10, 20], ["oops"]]


def test_keep_some_else_accepts_structured_none_variants():
    src = """
    dead = ref([])

    remember_dead(x) = ref_update(dead, (xs) -> append(xs, [x]))

    stage(x) =
      ("a") -> none |
      ("b") -> none("missing-key") |
      ("c") -> none("missing-key", { key: "name" }) |
      ("4") -> some(40)

    [
      ["a", "b", "c", "4"] |> lines |> keep_some_else(stage, remember_dead) |> collect,
      ref_get(dead)
    ]
    """
    env = make_global_env([])
    assert run_source(src, env) == [[40], ["a", "b", "c"]]


def test_keep_some_else_rejects_non_option_stage_results_clearly():
    src = """
    bad(x) = 123
    sink(x) = log(x)

    ["a", "b", "c"] |> lines |> keep_some_else(bad, sink) |> collect
    """
    env = make_global_env([])
    with pytest.raises(TypeError, match=r"keep_some_else expected stage\(item\) to return some\(\.\.\.\) or none\(\.\.\.\), received int"):
        run_source(src, env)


def test_keep_some_else_is_opt_in_and_does_not_change_ordinary_pipeline_option_behavior():
    src = """
    [some?("42" |> parse_int), "42" |> parse_int]
    """
    env = make_global_env([])
    result = run_source(src, env)
    assert result[0] is True
    assert format_debug(result[1]) == "some(42)"
