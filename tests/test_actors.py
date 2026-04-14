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


def test_actor_state_progression():
    """basic actor state progression through multiple actor_send calls"""
    env = make_global_env([])
    run_source(
        """
        handler(state, msg, _ctx) = ["ok", state + msg]
        a = actor(0, handler)
        actor_send(a, 1)
        actor_send(a, 2)
        actor_send(a, 10)
        """,
        env,
    )
    wait_for(env, 'cell_get(a("_cell"))', 13)


def test_actor_alive():
    """actor_alive? reports worker liveness"""
    env = make_global_env([])
    run_source(
        """
        handler(state, _msg, _ctx) = ["ok", state]
        a = actor(0, handler)
        """,
        env,
    )
    assert run_source("actor_alive?(a)", env) is True


def test_actor_invalid_handler_return():
    """invalid handler return shape marks actor as failed"""
    env = make_global_env([])
    run_source(
        """
        bad_handler(state, msg, _ctx) = "not-a-valid-effect"
        a = actor(0, bad_handler)
        actor_send(a, 1)
        """,
        env,
    )
    wait_for(env, 'cell_failed?(a("_cell"))', True)


def test_actor_failure_rejects_subsequent_sends():
    """subsequent actor_send raises after the actor has failed"""
    env = make_global_env([])
    run_source(
        """
        handler(state, msg, _ctx) = ["ok", state + msg]
        a = actor(0, handler)
        actor_send(a, 1)
        """,
        env,
    )
    wait_for(env, 'cell_get(a("_cell"))', 1)

    # Send a message whose handler will throw (division by zero)
    run_source(
        """
        crash_handler(_state, _msg, _ctx) = 1 / 0
        a2 = actor(0, crash_handler)
        actor_send(a2, 1)
        """,
        env,
    )
    wait_for(env, 'cell_failed?(a2("_cell"))', True)

    with pytest.raises(RuntimeError, match="Cell has failed"):
        run_source("actor_send(a2, 2)", env)
