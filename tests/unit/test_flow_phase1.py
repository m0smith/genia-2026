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


def test_evolve_integer_progression_can_be_bounded_with_head():
    env = make_global_env()
    src = """
    inc(n) -> n + 1
    evolve(0, inc) |> head(4) |> collect
    """
    assert run_source(src, env) == [0, 1, 2, 3]


def test_evolve_integer_progression_is_deterministic_with_take():
    env = make_global_env()
    src = """
    inc(n) -> n + 1
    evolve(0, inc) |> take(5) |> collect
    """
    assert run_source(src, env) == [0, 1, 2, 3, 4]


def test_evolve_drives_discrete_time_progression_with_scan():
    env = make_global_env()
    src = """
    inc(n) -> n + 1
    evolve(0, inc) |> take(4) |> scan((state, _) -> [state + 10, state + 10], 0) |> collect
    """
    assert run_source(src, env) == [10, 20, 30, 40]


def test_evolve_one_arg_no_longer_selects_integer_count_mode():
    env = make_global_env()
    with pytest.raises(Exception):
        run_source("evolve(5) |> collect", env)


def test_stdin_keys_stream_can_feed_flow_stages_directly():
    env = make_global_env(
        stdin_keys_provider=lambda: iter(["a", "b", "\n", "q"]),
    )
    assert run_source("stdin_keys |> collect", env) == ["a", "b", "\n", "q"]


def test_stdin_keys_is_single_use_flow_like_other_flow_sources():
    src = """
    keys = stdin_keys
    first = keys |> head(2) |> collect
    second = keys |> collect
    [first, second]
    """
    env = make_global_env(stdin_keys_provider=lambda: iter(["x", "y", "z"]))
    with pytest.raises(RuntimeError, match="Flow has already been consumed"):
        run_source(src, env)


def test_stdin_lines_behavior_remains_newline_normalized():
    env = make_global_env(
        stdin_provider=lambda: iter(["a\n", "b\r\n"]),
        stdin_keys_provider=lambda: iter(["a", "b"]),
    )
    assert run_source("stdin |> lines |> collect", env) == ["a", "b"]


def test_tee_split_and_merge_recombines_without_data_loss():
        env = make_number_flow_env([1, 2, 3])
        src = """
        numbers() |> tee |> merge |> collect
        """
        assert run_source(src, env) == [1, 2, 3, 1, 2, 3]


def test_tee_public_result_is_list_pair_not_python_tuple():
        env = make_number_flow_env([1, 2, 3])
        result = run_source("numbers() |> tee", env)

        assert isinstance(result, list)
        assert len(result) == 2
        assert all(isinstance(branch, GeniaFlow) for branch in result)


def test_tee_zip_keeps_all_items_without_data_loss():
        env = make_number_flow_env([1, 2, 3, 4])
        src = """
        numbers() |> tee |> zip |> collect
        """
        assert run_source(src, env) == [[1, 1], [2, 2], [3, 3], [4, 4]]


def test_zip_preserves_lockstep_ordering():
        env = make_number_flow_env([1, 2, 3])
        src = """
        numbers() |> tee |> zip |> collect
        """
        assert run_source(src, env) == [[1, 1], [2, 2], [3, 3]]


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


def test_take_closes_generator_backed_upstream_on_early_stop():
    env = make_global_env()
    state = {"pulled": 0, "closed": 0}

    def ticks():
        def iterator():
            try:
                i = 0
                while True:
                    state["pulled"] += 1
                    yield i
                    i += 1
            finally:
                state["closed"] += 1

        return GeniaFlow(iterator, label="ticks")

    env.set("ticks", ticks)
    assert run_source("ticks() |> take(3) |> collect", env) == [0, 1, 2]
    assert state["pulled"] == 3
    assert state["closed"] == 1


def test_take_fast_path_closes_closable_upstream_on_early_stop():
    env = make_global_env()
    state = {"pulled": 0, "closed": 0}

    class ClosableCounter:
        def __init__(self):
            self._next = 0

        def __iter__(self):
            return self

        def __next__(self):
            if self._next >= 100:
                raise StopIteration
            value = self._next
            self._next += 1
            state["pulled"] += 1
            return value

        def close(self):
            state["closed"] += 1

    def ticks():
        return GeniaFlow(lambda: ClosableCounter(), label="ticks")

    env.set("ticks", ticks)
    assert run_source("ticks() |> take(2) |> collect", env) == [0, 1]
    assert state["pulled"] == 2
    assert state["closed"] == 1


def test_map_fast_path_propagates_early_close_to_upstream():
    env = make_global_env()
    state = {"pulled": 0, "closed": 0}

    class ClosableCounter:
        def __init__(self):
            self._next = 0

        def __iter__(self):
            return self

        def __next__(self):
            if self._next >= 100:
                raise StopIteration
            value = self._next
            self._next += 1
            state["pulled"] += 1
            return value

        def close(self):
            state["closed"] += 1

    def ticks():
        return GeniaFlow(lambda: ClosableCounter(), label="ticks")

    env.set("ticks", ticks)
    assert run_source("ticks() |> map((x) -> x + 1) |> take(2) |> collect", env) == [1, 2]
    assert state["pulled"] == 2
    assert state["closed"] == 1


def test_filter_fast_path_propagates_early_close_to_upstream():
    env = make_global_env()
    state = {"pulled": 0, "closed": 0}

    class ClosableCounter:
        def __init__(self):
            self._next = 0

        def __iter__(self):
            return self

        def __next__(self):
            if self._next >= 100:
                raise StopIteration
            value = self._next
            self._next += 1
            state["pulled"] += 1
            return value

        def close(self):
            state["closed"] += 1

    def ticks():
        return GeniaFlow(lambda: ClosableCounter(), label="ticks")

    env.set("ticks", ticks)
    assert run_source("ticks() |> filter((x) -> x % 2 == 0) |> take(2) |> collect", env) == [0, 2]
    assert state["pulled"] == 3
    assert state["closed"] == 1


def test_scan_running_sum_progression():
    env = make_number_flow_env([1, 2, 3, 4])
    src = """
    numbers() |> scan((state, x) -> [state + x, state + x], 0) |> collect
    """
    assert run_source(src, env) == [1, 3, 6, 10]


def test_scan_supports_windowing_with_internal_state():
    env = make_number_flow_env([1, 2, 3, 4])
    src = """
        trim_to_2(xs) =
            (xs) ? count(xs) > 2 -> drop(count(xs) - 2, xs) |
            (xs) -> xs

    window2(state, x) = {
      next = [..state, x]
            trimmed = trim_to_2(next)
      [trimmed, trimmed]
    }

    numbers() |> scan(window2, []) |> collect
    """
    assert run_source(src, env) == [[1], [1, 2], [2, 3], [3, 4]]


def test_scan_fast_path_propagates_early_close_to_upstream():
    env = make_global_env()
    state = {"pulled": 0, "closed": 0}

    class ClosableCounter:
        def __init__(self):
            self._next = 0

        def __iter__(self):
            return self

        def __next__(self):
            if self._next >= 100:
                raise StopIteration
            value = self._next
            self._next += 1
            state["pulled"] += 1
            return value

        def close(self):
            state["closed"] += 1

    def ticks():
        return GeniaFlow(lambda: ClosableCounter(), label="ticks")

    env.set("ticks", ticks)
    src = """
    ticks() |> scan((state, x) -> [state + x, state + x], 0) |> take(3) |> collect
    """
    assert run_source(src, env) == [0, 1, 3]
    assert state["pulled"] == 3
    assert state["closed"] == 1


def test_scan_rejects_non_pair_step_results_clearly():
    env = make_number_flow_env([1])
    src = """
    numbers() |> scan((state, x) -> state + x, 0) |> collect
    """
    with pytest.raises(TypeError, match=r"scan expected step\(state, item\) to return \[next_state, output\], received int"):
        run_source(src, env)


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


def test_keep_some_keeps_unwrapped_some_values_only():
    src = """
    ["10", "oops", "20"] |> lines |> map(parse_int) |> keep_some |> collect
    """
    env = make_global_env([])
    assert run_source(src, env) == [10, 20]


def test_keep_some_with_stage_sugar_keeps_successes_only():
    src = """
    ["10", "oops", "20"] |> lines |> keep_some(parse_int) |> collect
    """
    env = make_global_env([])
    assert run_source(src, env) == [10, 20]


def test_keep_some_rejects_non_option_items_clearly():
    src = """
    ["a", "b"] |> lines |> keep_some |> collect
    """
    env = make_global_env([])
    with pytest.raises(TypeError, match=r"keep_some expected items to be some\(\.\.\.\) or none\(\.\.\.\), received string"):
        run_source(src, env)


def test_keep_some_else_is_opt_in_and_does_not_change_ordinary_pipeline_option_behavior():
    src = """
    [some?("42" |> parse_int), "42" |> parse_int]
    """
    env = make_global_env([])
    result = run_source(src, env)
    assert result[0] is True
    assert format_debug(result[1]) == "some(42)"


# --- evolve(init, f) contract tests ---
# These tests define the intended behavior for issue #250.


def test_evolve_init_f_integer_progression():
    env = make_global_env()
    assert run_source("evolve(0, (n) -> n + 1) |> take(5) |> collect", env) == [0, 1, 2, 3, 4]


def test_evolve_init_f_doubles_from_seed():
    env = make_global_env()
    assert run_source("evolve(1, (n) -> n * 2) |> take(5) |> collect", env) == [1, 2, 4, 8, 16]


def test_evolve_init_f_identity_repeats_init():
    env = make_global_env()
    assert run_source("evolve(5, (x) -> x) |> take(3) |> collect", env) == [5, 5, 5]


def test_evolve_init_f_with_map_value_progression():
    env = make_global_env()
    src = """
    step(state) -> {tick: state/tick + 1}
    evolve({tick: 0}, step) |> take(3) |> collect
    """
    assert format_debug(run_source(src, env)) == "[{tick: 0}, {tick: 1}, {tick: 2}]"


def test_evolve_init_f_emits_init_without_calling_f():
    env = make_global_env()
    calls = {"count": 0}

    def counter(x):
        calls["count"] += 1
        return x + 1

    env.set("counter_fn", counter)
    result = run_source("evolve(0, counter_fn) |> take(1) |> collect", env)
    assert result == [0]
    assert calls["count"] == 0


def test_evolve_init_f_take_zero_does_not_call_f():
    env = make_global_env()
    calls = {"count": 0}

    def counter(x):
        calls["count"] += 1
        return x + 1

    env.set("counter_fn", counter)
    result = run_source("evolve(0, counter_fn) |> take(0) |> collect", env)
    assert result == []
    assert calls["count"] == 0


def test_evolve_init_f_f_called_n_minus_one_times_for_take_n():
    env = make_global_env()
    calls = {"count": 0}

    def counter(x):
        calls["count"] += 1
        return x + 1

    env.set("counter_fn", counter)
    result = run_source("evolve(0, counter_fn) |> take(5) |> collect", env)
    assert result == [0, 1, 2, 3, 4]
    assert calls["count"] == 4


def test_evolve_init_f_is_single_use():
    env = make_global_env()
    src = """
    x = evolve(0, (n) -> n + 1)
    first = x |> take(3) |> collect
    second = x |> take(3) |> collect
    [first, second]
    """
    with pytest.raises(RuntimeError, match="Flow has already been consumed"):
        run_source(src, env)


def test_evolve_init_f_non_callable_f_fails_clearly():
    env = make_global_env()
    with pytest.raises(TypeError, match="evolve.*callable"):
        run_source('evolve(0, "not_a_function") |> head(1) |> collect', env)


def test_evolve_zero_arg_is_no_longer_valid():
    env = make_global_env()
    with pytest.raises(Exception):
        run_source("evolve() |> head(1) |> collect", env)


def test_evolve_one_arg_is_no_longer_valid():
    env = make_global_env()
    with pytest.raises(Exception):
        run_source("evolve(5) |> collect", env)
