import pytest

from genia import make_global_env, run_source


def run(src: str, stdin_data=None):
    env = make_global_env([] if stdin_data is None else stdin_data)
    return run_source(src, env)


def run_internal(src: str, stdin_data=None):
    env = make_global_env([] if stdin_data is None else stdin_data)
    env.internal_access = True
    try:
        return run_source(src, env)
    finally:
        env.internal_access = False


def test_seq_transform_list_maps_one_emit_per_item():
    src = """
    _seq_transform(0, (state, x) -> { emit: [x + 1] }, [1, 2, 3])
    """
    assert run_internal(src) == [2, 3, 4]


def test_seq_transform_list_supports_zero_and_many_emits():
    src = """
    step(state, x) =
      (_, 2) -> { emit: [] } |
      (_, x) -> { emit: [x, x + 10] }

    _seq_transform(0, step, [1, 2, 3])
    """
    assert run_internal(src) == [1, 11, 3, 13]


def test_seq_transform_list_threads_state_and_defaults_missing_fields():
    src = """
    step(state, x) =
      (_, 2) -> {} |
      (state, x) -> { state: state + x, emit: [state + x] }

    _seq_transform(0, step, [1, 2, 3])
    """
    assert run_internal(src) == [1, 4]


def test_seq_transform_list_halt_emits_current_item_then_stops():
    src = """
    _seq_transform(0, (state, x) -> { emit: [x], halt: x == 2 }, [1, 2, 3])
    """
    assert run_internal(src) == [1, 2]


def test_seq_transform_flow_returns_lazy_collectable_flow():
    src = """
    ["a", "b"]
      |> lines
      |> _seq_transform(0, (state, row) -> { emit: [concat(row, "!")] })
      |> collect
    """
    assert run_internal(src) == ["a!", "b!"]


def test_seq_transform_flow_halt_does_not_overpull_upstream():
    src = """
    count_ref = ref(0)
    next(n) = {
      ref_update(count_ref, (count) -> count + 1)
      n + 1
    }
    values = evolve(0, next)
      |> _seq_transform(0, (state, x) -> { emit: [x], halt: x == 2 })
      |> collect
    [values, ref_get(count_ref)]
    """
    assert run_internal(src) == [[0, 1, 2], 2]


def test_seq_transform_rejects_non_seq_source():
    with pytest.raises(
        TypeError,
        match="_seq_transform expected list or flow as third argument, received int",
    ):
        run_internal("_seq_transform(0, (state, x) -> { emit: [x] }, 42)")


def test_seq_transform_rejects_non_map_step_result():
    with pytest.raises(RuntimeError, match="invalid-seq-transform-result:"):
        run_internal("_seq_transform(0, (state, x) -> 42, [1])")


def test_seq_transform_rejects_invalid_emit_shape():
    with pytest.raises(RuntimeError, match="invalid-seq-transform-result:"):
        run_internal('_seq_transform(0, (state, x) -> { emit: "bad" }, [1])')


def test_seq_transform_rejects_invalid_halt_shape():
    with pytest.raises(RuntimeError, match="invalid-seq-transform-result:"):
        run_internal('_seq_transform(0, (state, x) -> { emit: [x], halt: "yes" }, [1])')
