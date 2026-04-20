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


def test_actor_failure_rejects_subsequent_calls():
    """subsequent actor_call raises after the actor has failed"""
    env = make_global_env([])
    run_source(
        """
        crash_handler(_state, _msg, _ctx) = 1 / 0
        a = actor(0, crash_handler)
        actor_send(a, 1)
        """,
        env,
    )
    wait_for(env, 'cell_failed?(a("_cell"))', True)

    with pytest.raises(RuntimeError, match="Cell has failed"):
        run_source("actor_call(a, 2)", env)


# --- actor_call tests ---


def test_actor_call_returns_reply():
    """actor_call returns the response from a reply effect"""
    env = make_global_env([])
    run_source(
        """
        handler(state, msg, _ctx) = ["reply", state + msg, state + msg]
        a = actor(0, handler)
        """,
        env,
    )
    assert run_source("actor_call(a, 5)", env) == 5
    assert run_source("actor_call(a, 10)", env) == 15


def test_actor_call_updates_state_and_returns_response():
    """actor_call updates state and returns a different response value"""
    env = make_global_env([])
    run_source(
        """
        handler(state, msg, _ctx) = ["reply", state + msg, state * 10 + msg]
        a = actor(10, handler)
        """,
        env,
    )
    # state=10, msg=3 -> new_state=13, response=10*10+3=103
    assert run_source("actor_call(a, 3)", env) == 103
    # state=13, msg=2 -> new_state=15, response=13*10+2=132
    assert run_source("actor_call(a, 2)", env) == 132


def test_actor_call_with_ok_effect_replies_with_new_state():
    """actor_call with an ok effect replies with the new state"""
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


def test_actor_send_tolerates_reply_effect():
    """actor_send accepts reply effect and discards the response"""
    env = make_global_env([])
    run_source(
        """
        handler(state, msg, _ctx) = ["reply", state + msg, "ignored"]
        a = actor(0, handler)
        actor_send(a, 5)
        actor_send(a, 10)
        """,
        env,
    )
    wait_for(env, 'cell_get(a("_cell"))', 15)


def test_actor_call_interleaved_with_send():
    """actor_call and actor_send interleave correctly"""
    env = make_global_env([])
    run_source(
        """
        handler(state, msg, _ctx) = ["reply", state + msg, state + msg]
        a = actor(0, handler)
        actor_send(a, 1)
        """,
        env,
    )
    wait_for(env, 'cell_get(a("_cell"))', 1)
    assert run_source("actor_call(a, 10)", env) == 11


def test_actor_call_on_failing_handler_returns_error_none():
    """actor_call returns none('actor-error') when handler throws"""
    env = make_global_env([])
    result = run_source(
        """
        crash(state, msg, _ctx) = 1 / 0
        a = actor(0, crash)
        actor_call(a, 1)
        """,
        env,
    )
    # Should be a none("actor-error") value
    from genia.interpreter import GeniaOptionNone
    assert isinstance(result, GeniaOptionNone)
    assert result.reason == "actor-error"


# --- actor_stop tests ---


def test_actor_stop_drains_mailbox():
    """actor_stop processes remaining messages before stopping"""
    env = make_global_env([])
    run_source(
        """
        handler(state, msg, _ctx) = ["ok", state + msg]
        a = actor(0, handler)
        actor_send(a, 1)
        actor_send(a, 2)
        actor_stop(a)
        """,
        env,
    )
    # Wait for worker to finish
    wait_for(env, "actor_alive?(a)", False)
    # All messages should have been processed before stop
    assert run_source('cell_get(a("_cell"))', env) == 3


def test_actor_stop_rejects_subsequent_sends():
    """actor_send raises after actor_stop"""
    env = make_global_env([])
    run_source(
        """
        handler(state, msg, _ctx) = ["ok", state + msg]
        a = actor(0, handler)
        actor_stop(a)
        """,
        env,
    )
    wait_for(env, "actor_alive?(a)", False)
    with pytest.raises(RuntimeError, match="stopped"):
        run_source("actor_send(a, 1)", env)


def test_actor_stop_rejects_subsequent_calls():
    """actor_call raises after actor_stop"""
    env = make_global_env([])
    run_source(
        """
        handler(state, msg, _ctx) = ["reply", state + msg, state + msg]
        a = actor(0, handler)
        actor_stop(a)
        """,
        env,
    )
    wait_for(env, "actor_alive?(a)", False)
    with pytest.raises(RuntimeError, match="stopped"):
        run_source("actor_call(a, 1)", env)


def test_actor_stop_is_idempotent():
    """calling actor_stop multiple times is a no-op"""
    env = make_global_env([])
    run_source(
        """
        handler(state, msg, _ctx) = ["ok", state]
        a = actor(0, handler)
        actor_stop(a)
        actor_stop(a)
        """,
        env,
    )
    wait_for(env, "actor_alive?(a)", False)


def test_actor_alive_false_after_stop():
    """actor_alive? returns false after stop completes"""
    env = make_global_env([])
    run_source(
        """
        handler(state, msg, _ctx) = ["ok", state]
        a = actor(0, handler)
        actor_stop(a)
        """,
        env,
    )
    wait_for(env, "actor_alive?(a)", False)


# --- actor_restart tests ---


def test_actor_restart_after_failure_resumes_sends():
    """after restart from failure, actor_send works again"""
    env = make_global_env([])
    run_source(
        """
        handler(state, msg, _ctx) = ["ok", state + msg]
        a = actor(0, handler)
        actor_send(a, 5)
        """,
        env,
    )
    wait_for(env, 'cell_get(a("_cell"))', 5)

    # Force failure
    run_source(
        'cell_send(a("_cell"), (_) -> 1 / 0)',
        env,
    )
    wait_for(env, 'cell_failed?(a("_cell"))', True)

    # Restart with fresh state — original handler is preserved
    run_source("actor_restart(a, 0)", env)
    run_source("actor_send(a, 10)", env)
    wait_for(env, 'cell_get(a("_cell"))', 10)


def test_actor_restart_after_stop():
    """actor_restart after actor_stop resumes message processing"""
    env = make_global_env([])
    run_source(
        """
        handler(state, msg, _ctx) = ["ok", state + msg]
        a = actor(0, handler)
        actor_send(a, 5)
        actor_stop(a)
        """,
        env,
    )
    wait_for(env, "actor_alive?(a)", False)

    # Restart after stop — worker thread relaunched
    run_source("actor_restart(a, 0)", env)
    assert run_source("actor_alive?(a)", env) is True
    run_source("actor_send(a, 7)", env)
    wait_for(env, 'cell_get(a("_cell"))', 7)


def test_actor_restart_preserves_handler():
    """actor_restart preserves the original handler for actor_call"""
    env = make_global_env([])
    run_source(
        """
        handler(state, msg, _ctx) = ["reply", state + msg, state + msg]
        a = actor(0, handler)
        """,
        env,
    )
    assert run_source("actor_call(a, 5)", env) == 5
    run_source("actor_restart(a, 100)", env)
    assert run_source("actor_call(a, 1)", env) == 101


def test_actor_restart_returns_actor():
    """actor_restart returns the actor reference"""
    env = make_global_env([])
    run_source(
        """
        handler(state, msg, _ctx) = ["ok", state]
        a = actor(0, handler)
        result = actor_restart(a, 42)
        """,
        env,
    )
    # result should be the actor map (has _handler key)
    assert run_source('result("_handler")', env) is not None


# --- actor inspection tests ---


def test_actor_state_reads_current_state():
    """actor_state returns the current state without sending a message"""
    env = make_global_env([])
    run_source(
        """
        handler(state, msg, _ctx) = ["ok", state + msg]
        a = actor(0, handler)
        actor_send(a, 5)
        """,
        env,
    )
    wait_for(env, "actor_state(a)", 5)
    run_source("actor_send(a, 3)", env)
    wait_for(env, "actor_state(a)", 8)


def test_actor_state_raises_on_failed_actor():
    """actor_state raises RuntimeError on a failed actor"""
    env = make_global_env([])
    run_source(
        """
        bad(_s, _m, _c) = 1 / 0
        a = actor(0, bad)
        actor_send(a, 1)
        """,
        env,
    )
    wait_for(env, "actor_failed?(a)", True)
    with pytest.raises(RuntimeError, match="Cell has failed"):
        run_source("actor_state(a)", env)


def test_actor_failed_and_error_on_healthy_actor():
    """actor_failed? is false and actor_error is none on healthy actor"""
    env = make_global_env([])
    run_source(
        """
        handler(state, msg, _ctx) = ["ok", state]
        a = actor(0, handler)
        """,
        env,
    )
    assert run_source("actor_failed?(a)", env) is False
    from genia.interpreter import OPTION_NONE
    assert run_source("actor_error(a)", env) is OPTION_NONE


def test_actor_failed_and_error_on_crashed_actor():
    """actor_failed? is true and actor_error is some after failure"""
    env = make_global_env([])
    run_source(
        """
        bad(_s, _m, _c) = 1 / 0
        a = actor(0, bad)
        actor_send(a, 1)
        """,
        env,
    )
    wait_for(env, "actor_failed?(a)", True)
    from genia.interpreter import GeniaOptionSome
    error = run_source("actor_error(a)", env)
    assert isinstance(error, GeniaOptionSome)
    assert "ZeroDivisionError" in error.value


def test_actor_status_lifecycle():
    """actor_status reflects ready, failed, and stopped states"""
    env = make_global_env([])
    run_source(
        """
        handler(state, msg, _ctx) = ["ok", state]
        a = actor(0, handler)
        """,
        env,
    )
    assert run_source("actor_status(a)", env) == "ready"

    # Stop and check
    run_source("actor_stop(a)", env)
    assert run_source("actor_status(a)", env) == "stopped"

    # Restart and check
    run_source("actor_restart(a, 0)", env)
    assert run_source("actor_status(a)", env) == "ready"
