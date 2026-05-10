import time

import pytest
from genia.utf8 import format_debug


def test_rand_values_are_in_unit_interval(run):
    samples = [run("rand()") for _ in range(64)]
    assert all(isinstance(x, float) for x in samples)
    assert all(0.0 <= x < 1.0 for x in samples)


def test_rand_multiple_calls_are_not_constant(run):
    samples = [run("rand()") for _ in range(64)]
    assert len(set(samples)) > 1


def test_rand_int_values_within_bounds_and_not_constant(run):
    n = 7
    samples = [run(f"rand_int({n})") for _ in range(128)]
    assert all(isinstance(x, int) for x in samples)
    assert all(0 <= x < n for x in samples)
    assert len(set(samples)) > 1


def test_rand_int_rejects_non_integer_and_non_positive_inputs(run):
    with pytest.raises(TypeError, match="rand_int expected a positive integer"):
        run("rand_int(3.5)")
    with pytest.raises(ValueError, match="rand_int expected n > 0"):
        run("rand_int(0)")
    with pytest.raises(ValueError, match="rand_int expected n > 0"):
        run("rand_int(-1)")


def test_sleep_accepts_small_values_and_returns_nil(run):
    started = time.perf_counter()
    result = run("sleep(5)")
    elapsed_ms = (time.perf_counter() - started) * 1000.0
    assert format_debug(result) == 'none("nil")'
    assert elapsed_ms >= 1.0


def test_sleep_rejects_negative_and_non_numeric_values(run):
    with pytest.raises(ValueError, match="sleep expected ms >= 0"):
        run("sleep(-1)")
    with pytest.raises(TypeError, match="sleep expected a non-negative number"):
        run('sleep("1")')


def test_seeded_rand_same_seed_same_sequence(run):
    source = """
    pair_left(pair) = ([x, _]) -> x
    pair_right(pair) = ([_, x]) -> x

    r0 = rng(123)
    s1 = rand(r0)
    r1 = pair_left(s1)
    v1 = pair_right(s1)
    s2 = rand(r1)
    r2 = pair_left(s2)
    v2 = pair_right(s2)
    s3 = rand(r2)
    v3 = pair_right(s3)
    [v1, v2, v3]
    """

    assert run(source) == run(source)


def test_seeded_rand_different_seeds_produce_different_sequences(run):
    source1 = """
    pair_left(pair) = ([x, _]) -> x
    pair_right(pair) = ([_, x]) -> x

    r0 = rng(1)
    s1 = rand(r0)
    r1 = pair_left(s1)
    v1 = pair_right(s1)
    s2 = rand(r1)
    [v1, pair_right(s2)]
    """
    source2 = source1.replace("rng(1)", "rng(2)")

    assert run(source1) != run(source2)


def test_seeded_rand_int_is_deterministic_and_bounded(run):
    source = """
    pair_left(pair) = ([x, _]) -> x
    pair_right(pair) = ([_, x]) -> x

    r0 = rng(9)
    s1 = rand_int(r0, 7)
    r1 = pair_left(s1)
    v1 = pair_right(s1)
    s2 = rand_int(r1, 7)
    r2 = pair_left(s2)
    v2 = pair_right(s2)
    s3 = rand_int(r2, 7)
    v3 = pair_right(s3)
    [v1, v2, v3]
    """

    values = run(source)
    assert run(source) == values
    assert all(isinstance(x, int) for x in values)
    assert all(0 <= x < 7 for x in values)


def test_seeded_rng_rejects_invalid_seed_and_state_inputs(run):
    with pytest.raises(TypeError, match="rng expected an integer seed"):
        run('rng("oops")')
    with pytest.raises(ValueError, match="rng expected seed >= 0"):
        run("rng(-1)")
    with pytest.raises(TypeError, match="rand expected an rng state"):
        run("rand(1)")
    with pytest.raises(TypeError, match="rand_int expected an rng state"):
        run("rand_int(1, 5)")


def test_rand_flow_is_deterministic_bounded_and_unit_interval(run):
    first = run("rand_flow(42) |> take(8) |> collect")
    second = run("rand_flow(42) |> take(8) |> collect")

    assert first == second
    assert len(first) == 8
    assert all(isinstance(x, float) for x in first)
    assert all(0.0 <= x < 1.0 for x in first)


def test_rand_flow_distinct_seeds_and_empty_take(run):
    assert run("rand_flow(1) |> take(6) |> collect") != run(
        "rand_flow(2) |> take(6) |> collect"
    )
    assert run("rand_flow(42) |> take(0) |> collect") == []


def test_rand_int_flow_is_deterministic_bounded_and_composable(run):
    source = """
    rand_int_flow(123, 6)
      |> map((n) -> n + 1)
      |> take(10)
      |> collect
    """

    first = run(source)
    second = run(source)

    assert first == second
    assert len(first) == 10
    assert all(isinstance(x, int) for x in first)
    assert all(1 <= x <= 6 for x in first)


def test_rand_int_flow_n_one_and_empty_take(run):
    assert run("rand_int_flow(9, 1) |> take(5) |> collect") == [0, 0, 0, 0, 0]
    assert run("rand_int_flow(9, 7) |> take(0) |> collect") == []


def test_rand_flow_and_rand_int_flow_are_single_use(run):
    with pytest.raises(RuntimeError, match="Flow has already been consumed"):
        run(
            """
            flow = rand_flow(7)
            flow |> take(1) |> collect
            flow |> take(1) |> collect
            """
        )

    with pytest.raises(RuntimeError, match="Flow has already been consumed"):
        run(
            """
            flow = rand_int_flow(7, 10)
            flow |> take(1) |> collect
            flow |> take(1) |> collect
            """
        )


def test_rand_flow_rejects_invalid_seed(run):
    with pytest.raises(TypeError, match="rand_flow seed must be a non-negative integer"):
        run('rand_flow("oops")')
    with pytest.raises(ValueError, match="rand_flow seed must be a non-negative integer"):
        run("rand_flow(-1)")


def test_rand_int_flow_rejects_invalid_seed_and_n_eagerly(run):
    with pytest.raises(
        TypeError, match="rand_int_flow seed must be a non-negative integer"
    ):
        run('rand_int_flow("oops", 6)')
    with pytest.raises(
        ValueError, match="rand_int_flow seed must be a non-negative integer"
    ):
        run("rand_int_flow(-1, 6)")
    with pytest.raises(TypeError, match="rand_int_flow n must be a positive integer"):
        run('rand_int_flow(1, "6")')
    with pytest.raises(ValueError, match="rand_int_flow n must be a positive integer"):
        run("rand_int_flow(1, 0)")
    with pytest.raises(ValueError, match="rand_int_flow n must be a positive integer"):
        run("rand_int_flow(1, -1)")
