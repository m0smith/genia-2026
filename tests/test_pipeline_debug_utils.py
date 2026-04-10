from genia import make_global_env, run_source


def test_trace_and_inspect_preserve_pipeline_output(run, capsys):
    src = """
    [1, 2, 3] |> trace("before sum") |> inspect |> sum
    """
    assert run(src) == 6

    captured = capsys.readouterr()
    assert "before sum [1, 2, 3]" in captured.err
    assert "[1, 2, 3]" in captured.err
    assert captured.out == ""


def test_tap_runs_side_effects_and_returns_original_value(run):
    src = """
    seen = ref([])
    value = 41 |> tap((x) -> ref_update(seen, (xs) -> append(xs, [x])))
    [value, ref_get(seen)]
    """
    assert run(src) == [41, [41]]


def test_inspect_wraps_some_and_propagates_none(run, capsys):
    # inspect(some(5)) must log and return some(5) unchanged
    src = """
    unwrap_or(0, inspect(some(5)))
    """
    assert run(src) == 5

    captured = capsys.readouterr()
    assert "some(5)" in captured.err

    # inspect(none(...)) short-circuits: the none propagates without logging (correct behavior)
    src2 = 'is_none?(inspect(none("missing-key", { key: "name" })))'
    capsys.readouterr()
    assert run(src2) is True

    # trace in pipeline short-circuits on none — stage is skipped, no log emitted
    src3 = 'is_none?(none("missing-key") |> trace("label"))'
    capsys.readouterr()
    assert run(src3) is True
    assert "label" not in capsys.readouterr().err


def test_trace_on_flow_does_not_force_full_evaluation(capsys):
    src = """
    seen = ref(0)

    mark(x) = {
      ref_update(seen, (n) -> n + 1)
      x
    }

    [
      stdin |> lines |> map(mark) |> trace("after map") |> head(1) |> collect,
      ref_get(seen)
    ]
    """
    env = make_global_env(["a", "b", "c"])

    assert run_source(src, env) == [["a"], 1]
    assert "after map <flow map ready>" in capsys.readouterr().err
