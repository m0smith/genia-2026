import time

import pytest

from genia import make_global_env, run_source


def wait_for(env, expr, expected, *, timeout_s=1.0, sleep_s=0.01):
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        if run_source(expr, env) == expected:
            return
        time.sleep(sleep_s)
    assert run_source(expr, env) == expected


def test_cell_increment_updates_state_correctly():
    env = make_global_env([])
    run_source(
        """
        a = cell(0)
        cell_send(a, (x) -> x + 1)
        cell_send(a, (x) -> x + 1)
        """,
        env,
    )

    wait_for(env, "cell_get(a)", 2)


def test_cell_processes_multiple_sends_in_order():
    env = make_global_env([])
    run_source(
        """
        a = cell(1)
        cell_send(a, (x) -> x + 2)
        cell_send(a, (x) -> x * 10)
        """,
        env,
    )

    wait_for(env, "cell_get(a)", 30)


def test_cell_get_and_cell_state_return_current_state():
    env = make_global_env([])
    run_source(
        """
        a = cell(41)
        cell_send(a, (x) -> x + 1)
        """,
        env,
    )

    wait_for(env, "cell_state(a)", 42)
    assert run_source("cell_get(a)", env) == 42
    assert run_source("cell_state(a)", env) == 42


def test_cell_updates_are_asynchronous_relative_to_caller():
    env = make_global_env([])
    run_source(
        """
        gate = ref()
        a = cell(0)
        cell_send(a, (_) -> ref_get(gate))
        cell_send(a, (x) -> x + 1)
        """,
        env,
    )

    assert run_source("cell_get(a)", env) == 0

    run_source("ref_set(gate, 41)", env)
    wait_for(env, "cell_get(a)", 42)


def test_cell_alive_reports_worker_status():
    env = make_global_env([])
    assert run_source("cell_alive?(cell(0))", env) is True


def test_failed_update_preserves_prior_state_and_marks_failed():
    env = make_global_env([])
    run_source(
        """
        state = ref(1)
        a = cell_with_state(state)
        cell_send(a, (x) -> x + 1)
        cell_send(a, (_) -> map_get(1, "bad"))
        """,
        env,
    )

    wait_for(env, "cell_failed?(a)", True)
    assert run_source("ref_get(state)", env) == 2
    assert run_source('cell_status(a)', env) == "failed"
    assert run_source("is_some?(cell_error(a))", env) is True


def test_failed_cell_rejects_future_send_and_get():
    env = make_global_env([])
    run_source(
        """
        a = cell(1)
        cell_send(a, (_) -> map_get(1, "bad"))
        """,
        env,
    )

    wait_for(env, "cell_failed?(a)", True)

    with pytest.raises(RuntimeError, match="Cell has failed"):
        run_source("cell_send(a, (x) -> x + 1)", env)

    with pytest.raises(RuntimeError, match="Cell has failed"):
        run_source("cell_get(a)", env)


def test_cell_error_returns_none_when_ready_and_some_after_failure():
    env = make_global_env([])
    run_source("a = cell(1)", env)
    assert run_source("is_none?(cell_error(a))", env) is True

    run_source('cell_send(a, (_) -> map_get(1, "bad"))', env)
    wait_for(env, "cell_failed?(a)", True)
    assert run_source("is_some?(cell_error(a))", env) is True


def test_queued_messages_after_failure_are_not_processed():
    env = make_global_env([])
    run_source(
        """
        state = ref(1)
        a = cell_with_state(state)
        cell_send(a, (x) -> x + 1)
        cell_send(a, (_) -> map_get(1, "bad"))
        cell_send(a, (x) -> x + 100)
        """,
        env,
    )

    wait_for(env, "cell_failed?(a)", True)
    time.sleep(0.05)
    assert run_source("ref_get(state)", env) == 2


def test_restart_cell_clears_failure_discards_old_queue_and_restores_usability():
    env = make_global_env([])
    run_source(
        """
        state = ref(1)
        a = cell_with_state(state)
        cell_send(a, (_) -> map_get(1, "bad"))
        cell_send(a, (x) -> x + 100)
        """,
        env,
    )

    wait_for(env, "cell_failed?(a)", True)
    run_source("restart_cell(a, 5)", env)

    assert run_source("cell_failed?(a)", env) is False
    assert run_source("is_none?(cell_error(a))", env) is True
    assert run_source('cell_status(a)', env) == "ready"
    wait_for(env, "cell_get(a)", 5)
    time.sleep(0.05)
    assert run_source("ref_get(state)", env) == 5

    run_source("cell_send(a, (x) -> x + 1)", env)
    wait_for(env, "cell_get(a)", 6)


def test_nested_cell_send_from_failing_update_is_not_committed():
    env = make_global_env([])
    run_source(
        """
        source = cell(0)
        target = cell(10)
        cell_send(source, (x) -> {
          cell_send(target, (n) -> n + 5)
          map_get(1, "bad")
        })
        """,
        env,
    )

    wait_for(env, "cell_failed?(source)", True)
    time.sleep(0.05)
    assert run_source("cell_get(target)", env) == 10
