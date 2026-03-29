import time

import pytest


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
    assert result is None
    assert elapsed_ms >= 1.0


def test_sleep_rejects_negative_and_non_numeric_values(run):
    with pytest.raises(ValueError, match="sleep expected ms >= 0"):
        run("sleep(-1)")
    with pytest.raises(TypeError, match="sleep expected a non-negative number"):
        run('sleep("1")')
