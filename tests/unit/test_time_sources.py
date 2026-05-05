import time

import pytest

from genia import make_global_env, run_source
from genia.interpreter import GeniaFlow
from genia.values import is_none


def test_every_returns_a_flow():
    result = run_source("every(1)", make_global_env())
    assert isinstance(result, GeniaFlow)


def test_every_take_3_emits_3_tick_values():
    result = run_source("every(1) |> take(3) |> collect", make_global_env())
    assert len(result) == 3
    assert all(is_none(v) and v.reason == "tick" for v in result)


def test_every_emits_after_minimum_elapsed_time():
    started = time.perf_counter()
    run_source("every(5) |> take(2) |> collect", make_global_env())
    elapsed_ms = (time.perf_counter() - started) * 1000.0
    assert elapsed_ms >= 5.0


def test_every_accepts_zero():
    result = run_source("every(0) |> take(2) |> collect", make_global_env())
    assert len(result) == 2


def test_every_rejects_non_number():
    with pytest.raises(TypeError, match="every expected a non-negative number"):
        run_source('every("1")', make_global_env())


def test_every_rejects_negative():
    with pytest.raises(ValueError, match="every expected ms >= 0"):
        run_source("every(-1)", make_global_env())


def test_every_flow_is_single_use():
    src = """
    t = every(1)
    t |> take(1) |> collect
    t |> take(1) |> collect
    """
    with pytest.raises(RuntimeError, match="Flow has already been consumed"):
        run_source(src, make_global_env())


def test_every_early_termination_does_not_continue_ticking():
    started = time.perf_counter()
    result = run_source("every(100) |> take(1) |> collect", make_global_env())
    elapsed_ms = (time.perf_counter() - started) * 1000.0
    assert len(result) == 1
    assert elapsed_ms < 500.0
