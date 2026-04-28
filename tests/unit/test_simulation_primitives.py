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
