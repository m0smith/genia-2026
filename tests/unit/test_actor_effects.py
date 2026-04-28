"""Tests for the standardized actor handler effect protocol.

Covers:
1. ["ok", new_state] updates state
2. ["reply", new_state, value] returns value via actor_call
3. ["stop", reason, new_state] terminates actor
4. invalid return shape triggers clear error
"""

import time

import pytest

from genia import make_global_env, run_source
from genia.interpreter import GeniaOptionNone


def wait_for(env, expr, expected, *, timeout_s=1.0, sleep_s=0.01):
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        if run_source(expr, env) == expected:
            return
        time.sleep(sleep_s)
    assert run_source(expr, env) == expected


# --- ["ok", new_state] ---


def test_ok_effect_updates_state():
    """["ok", new_state] updates state via actor_send."""
    env = make_global_env([])
    run_source(
        """
        handler(state, msg, _ctx) = ["ok", state + msg]
        a = actor(0, handler)
        actor_send(a, 5)
        actor_send(a, 3)
        """,
        env,
    )
    wait_for(env, "actor_state(a)", 8)


def test_ok_effect_via_actor_call_returns_new_state():
    """["ok", new_state] via actor_call replies with new_state."""
    env = make_global_env([])
    run_source(
        """
        handler(state, msg, _ctx) = ["ok", state + msg]
        a = actor(0, handler)
        """,
        env,
    )
    assert run_source("actor_call(a, 7)", env) == 7
    assert run_source("actor_call(a, 3)", env) == 10


# --- ["reply", new_state, value] ---


def test_reply_effect_returns_value_via_actor_call():
    """["reply", new_state, value] returns value via actor_call."""
    env = make_global_env([])
    run_source(
        """
        handler(state, msg, _ctx) = ["reply", state + msg, msg * 2]
        a = actor(0, handler)
        """,
        env,
    )
    assert run_source("actor_call(a, 5)", env) == 10
    # state should be 5 now
    assert run_source("actor_state(a)", env) == 5


def test_reply_effect_via_actor_send_discards_response():
    """["reply", new_state, value] via actor_send discards the response."""
    env = make_global_env([])
    run_source(
        """
        handler(state, msg, _ctx) = ["reply", state + msg, "ignored"]
        a = actor(0, handler)
        actor_send(a, 10)
        """,
        env,
    )
    wait_for(env, "actor_state(a)", 10)


# --- ["stop", reason, new_state] ---


def test_stop_effect_via_actor_send():
    """["stop", reason, new_state] commits state and stops the actor."""
    env = make_global_env([])
    run_source(
        """
        handler(state, msg, _ctx) = ["stop", "done", state + msg]
        a = actor(0, handler)
        actor_send(a, 42)
        """,
        env,
    )
    wait_for(env, "actor_alive?(a)", False)
    assert run_source("actor_status(a)", env) == "stopped"
    # final state was committed
    assert run_source('cell_get(a("_cell"))', env) == 42


def test_stop_effect_via_actor_call():
    """["stop", reason, new_state] via actor_call replies with none("actor-stopped")."""
    env = make_global_env([])
    run_source(
        """
        handler(state, msg, _ctx) = ["stop", "shutdown", state + msg]
        a = actor(0, handler)
        """,
        env,
    )
    result = run_source("actor_call(a, 10)", env)
    assert isinstance(result, GeniaOptionNone)
    assert result.reason == "actor-stopped"
    wait_for(env, "actor_alive?(a)", False)


def test_stop_effect_rejects_subsequent_sends():
    """After ["stop", ...], actor_send raises."""
    env = make_global_env([])
    run_source(
        """
        handler(state, msg, _ctx) = ["stop", "done", state]
        a = actor(0, handler)
        actor_send(a, 1)
        """,
        env,
    )
    wait_for(env, "actor_alive?(a)", False)
    with pytest.raises(RuntimeError, match="stopped"):
        run_source("actor_send(a, 2)", env)


def test_stop_effect_commits_final_state():
    """["stop", ...] commits the new_state before stopping."""
    env = make_global_env([])
    run_source(
        """
        handler(state, msg, _ctx) = ["stop", "final", msg * 100]
        a = actor(0, handler)
        actor_send(a, 7)
        """,
        env,
    )
    wait_for(env, "actor_alive?(a)", False)
    assert run_source('cell_get(a("_cell"))', env) == 700


# --- invalid return shape ---


def test_invalid_return_string():
    """A handler returning a string triggers a clear error."""
    env = make_global_env([])
    run_source(
        """
        bad(state, msg, _ctx) = "not-valid"
        a = actor(0, bad)
        actor_send(a, 1)
        """,
        env,
    )
    wait_for(env, "actor_failed?(a)", True)
    from genia.interpreter import GeniaOptionSome

    error = run_source("actor_error(a)", env)
    assert isinstance(error, GeniaOptionSome)
    assert "actor handler must return" in error.value
    assert '"not-valid"' in error.value


def test_invalid_return_number():
    """A handler returning a number triggers a clear error."""
    env = make_global_env([])
    run_source(
        """
        bad(state, msg, _ctx) = 42
        a = actor(0, bad)
        actor_send(a, 1)
        """,
        env,
    )
    wait_for(env, "actor_failed?(a)", True)
    from genia.interpreter import GeniaOptionSome

    error = run_source("actor_error(a)", env)
    assert isinstance(error, GeniaOptionSome)
    assert "actor handler must return" in error.value
    assert "42" in error.value


def test_invalid_return_wrong_tag():
    """A handler returning a list with unknown tag triggers a clear error."""
    env = make_global_env([])
    run_source(
        """
        bad(state, msg, _ctx) = ["nope", state]
        a = actor(0, bad)
        actor_send(a, 1)
        """,
        env,
    )
    wait_for(env, "actor_failed?(a)", True)
    from genia.interpreter import GeniaOptionSome

    error = run_source("actor_error(a)", env)
    assert isinstance(error, GeniaOptionSome)
    assert "actor handler must return" in error.value


def test_invalid_return_via_actor_call():
    """Invalid return via actor_call returns none("actor-error")."""
    env = make_global_env([])
    result = run_source(
        """
        bad(state, msg, _ctx) = "invalid"
        a = actor(0, bad)
        actor_call(a, 1)
        """,
        env,
    )
    assert isinstance(result, GeniaOptionNone)
    assert result.reason == "actor-error"


# --- effect protocol completeness ---


def test_all_three_effects_in_sequence():
    """An actor can process ok then stop effects in sequence."""
    env = make_global_env([])
    # First use ok effect to accumulate state
    run_source(
        """
        ok_handler(state, msg, _ctx) = ["ok", state + msg]
        a1 = actor(0, ok_handler)
        actor_send(a1, 1)
        actor_send(a1, 2)
        """,
        env,
    )
    wait_for(env, "actor_state(a1)", 3)

    # Use reply effect via actor_call
    env2 = make_global_env([])
    run_source(
        """
        reply_handler(state, msg, _ctx) = ["reply", state + msg, state + msg]
        a2 = actor(0, reply_handler)
        """,
        env2,
    )
    assert run_source("actor_call(a2, 10)", env2) == 10

    # Use stop effect
    env3 = make_global_env([])
    run_source(
        """
        stop_handler(state, msg, _ctx) = ["stop", "done", state + msg]
        a3 = actor(0, stop_handler)
        actor_send(a3, 99)
        """,
        env3,
    )
    wait_for(env3, "actor_alive?(a3)", False)
    assert run_source('cell_get(a3("_cell"))', env3) == 99
