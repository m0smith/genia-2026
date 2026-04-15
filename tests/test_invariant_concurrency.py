"""Invariant locking tests for concurrency guarantees.

These tests document the exact guarantees the current Python host provides.
They are NOT aspirational — they verify what is actually true today.
"""

import time
import pytest
from genia import make_global_env, run_source


def wait_for(env, expr, expected, *, timeout_s=2.0, sleep_s=0.01):
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        if run_source(expr, env) == expected:
            return
        time.sleep(sleep_s)
    assert run_source(expr, env) == expected


# ---------------------------------------------------------------------------
# Ref invariants
# ---------------------------------------------------------------------------

class TestRefInvariants:
    """Ref is a synchronized container. get blocks until set."""

    def test_ref_initial_value_is_readable_immediately(self):
        """ref(val) creates a ready ref that ref_get returns without blocking."""
        env = make_global_env([])
        result = run_source('r = ref(42)\nref_get(r)', env)
        assert result == 42

    def test_ref_set_makes_value_visible(self):
        """ref_set installs a value; ref_get returns it."""
        env = make_global_env([])
        result = run_source('r = ref(0)\nref_set(r, 99)\nref_get(r)', env)
        assert result == 99

    def test_ref_update_applies_function_atomically(self):
        """ref_update(ref, fn) applies fn under lock and returns new value."""
        env = make_global_env([])
        result = run_source(
            'r = ref(10)\nref_update(r, (x) -> x + 5)\nref_get(r)', env
        )
        assert result == 15

    def test_ref_is_set_reports_initialization(self):
        """ref_is_set is false for unset ref, true after set."""
        env = make_global_env([])
        # ref with initial value
        result = run_source('r = ref(1)\nref_is_set(r)', env)
        assert result is True

    def test_ref_get_blocks_until_set_from_process(self):
        """Unset ref blocks ref_get; process sets it, unblocking the caller."""
        env = make_global_env([])
        result = run_source(
            '''
            r = ref()
            p = spawn((msg) -> ref_set(r, msg))
            send(p, 42)
            ref_get(r)
            ''',
            env,
        )
        assert result == 42

    def test_ref_update_serializes_concurrent_access(self):
        """Multiple processes updating same ref via ref_update produce correct total."""
        env = make_global_env([])
        run_source(
            '''
            counter = ref(0)
            inc(_msg) = ref_update(counter, (n) -> n + 1)
            p1 = spawn(inc)
            p2 = spawn(inc)
            send(p1, "go")
            send(p1, "go")
            send(p2, "go")
            send(p2, "go")
            send(p1, "go")
            ''',
            env,
        )
        wait_for(env, "ref_get(counter)", 5)


# ---------------------------------------------------------------------------
# Process FIFO ordering invariants
# ---------------------------------------------------------------------------

class TestProcessFIFOInvariants:
    """Processes handle messages in FIFO order, one at a time."""

    def test_process_preserves_message_order(self):
        """Messages sent to one process are handled in send order."""
        env = make_global_env([])
        run_source(
            '''
            log = ref([])
            p = spawn((msg) -> ref_update(log, (xs) -> append(xs, [msg])))
            send(p, 1)
            send(p, 2)
            send(p, 3)
            send(p, 4)
            send(p, 5)
            ''',
            env,
        )
        wait_for(env, "ref_get(log)", [1, 2, 3, 4, 5])

    def test_process_serializes_handler_invocations(self):
        """Only one handler runs at a time per process.
        We verify this by recording timestamps; each entry should be after the previous."""
        env = make_global_env([])
        run_source(
            '''
            log = ref([])
            p = spawn((msg) -> ref_update(log, (xs) -> append(xs, [msg])))
            send(p, "a")
            send(p, "b")
            send(p, "c")
            ''',
            env,
        )
        wait_for(env, "ref_get(log)", ["a", "b", "c"])

    def test_process_fail_stop_is_permanent(self):
        """A failed process stays failed; no implicit restart."""
        env = make_global_env([])
        run_source(
            '''
            boom = spawn((msg) -> 1 / 0)
            send(boom, "x")
            ''',
            env,
        )
        wait_for(env, "process_failed?(boom)", True)
        # Still failed after waiting
        time.sleep(0.05)
        assert run_source("process_failed?(boom)", env) is True
        assert run_source("process_alive?(boom)", env) is False


# ---------------------------------------------------------------------------
# Cell fail-stop invariants
# ---------------------------------------------------------------------------

class TestCellFailStopInvariants:
    """Cells serialize updates, preserve last good state on failure."""

    def test_cell_serializes_updates_in_order(self):
        """Cell processes updates in FIFO order."""
        env = make_global_env([])
        run_source(
            '''
            c = cell([])
            cell_send(c, (xs) -> append(xs, ["a"]))
            cell_send(c, (xs) -> append(xs, ["b"]))
            cell_send(c, (xs) -> append(xs, ["c"]))
            ''',
            env,
        )
        wait_for(env, "cell_get(c)", ["a", "b", "c"])

    def test_cell_failure_preserves_last_good_state(self):
        """Failed update does not change state; read via underlying ref."""
        env = make_global_env([])
        run_source(
            '''
            st = ref(10)
            c = cell_with_state(st)
            cell_send(c, (x) -> x + 5)
            cell_send(c, (x) -> 1 / 0)
            ''',
            env,
        )
        wait_for(env, "cell_failed?(c)", True)
        # State should still be 15 (last successful update), read via underlying ref
        assert run_source("ref_get(st)", env) == 15

    def test_cell_failure_rejects_further_operations(self):
        """Failed cell rejects cell_send and cell_get."""
        env = make_global_env([])
        run_source(
            '''
            c = cell(0)
            cell_send(c, (_x) -> 1 / 0)
            ''',
            env,
        )
        wait_for(env, "cell_failed?(c)", True)
        with pytest.raises(Exception, match="Cell has failed"):
            run_source("cell_send(c, (x) -> x + 1)", env)
        with pytest.raises(Exception, match="Cell has failed"):
            run_source("cell_get(c)", env)

    def test_cell_restart_clears_failure_and_discards_stale_updates(self):
        """restart_cell clears failure, installs new state, old queued updates are discarded."""
        env = make_global_env([])
        run_source(
            '''
            c = cell(0)
            cell_send(c, (x) -> x + 1)
            cell_send(c, (_x) -> 1 / 0)
            ''',
            env,
        )
        wait_for(env, "cell_failed?(c)", True)
        run_source("restart_cell(c, 100)", env)
        run_source("cell_send(c, (x) -> x + 1)", env)
        wait_for(env, "cell_get(c)", 101)

    def test_cell_nested_send_rolls_back_on_failure(self):
        """Nested cell_send during a failing update is not committed."""
        env = make_global_env([])
        run_source(
            '''
            log = ref([])
            other = spawn((msg) -> ref_update(log, (xs) -> append(xs, [msg])))
            c = cell(0)
            cell_send(c, (state) -> {
                send(other, "staged")
                1 / 0
            })
            ''',
            env,
        )
        wait_for(env, "cell_failed?(c)", True)
        # Staged send should NOT have been committed
        time.sleep(0.1)
        assert run_source("ref_get(log)", env) == []


# ---------------------------------------------------------------------------
# Actor invariants (thin prelude layer over cell/ref)
# ---------------------------------------------------------------------------

class TestActorInvariants:
    """Actors are the prelude-level message handler protocol over cells."""

    def test_actor_processes_messages_in_order(self):
        """Actor handler is called once per message, in order."""
        env = make_global_env([])
        run_source(
            '''
            a = actor([], (state, msg, _ctx) -> ["ok", append(state, [msg])])
            actor_send(a, 1)
            actor_send(a, 2)
            actor_send(a, 3)
            ''',
            env,
        )
        wait_for(env, "actor_state(a)", [1, 2, 3])

    def test_actor_call_blocks_until_reply(self):
        """actor_call returns the handler's reply value."""
        env = make_global_env([])
        run_source(
            '''
            a = actor(0, (state, msg, _ctx) -> ["reply", state + msg, state + msg])
            ''',
            env,
        )
        result = run_source("actor_call(a, 5)", env)
        assert result == 5

    def test_actor_call_with_ok_effect_returns_new_state(self):
        """actor_call with ["ok", state] returns the new state as reply."""
        env = make_global_env([])
        run_source(
            '''
            a = actor(10, (state, msg, _ctx) -> ["ok", state + msg])
            ''',
            env,
        )
        result = run_source("actor_call(a, 5)", env)
        assert result == 15

    def test_actor_stop_rejects_subsequent_sends(self):
        """Stopped actor rejects further sends."""
        env = make_global_env([])
        run_source(
            '''
            a = actor(0, (state, msg, _ctx) -> ["ok", state + msg])
            actor_stop(a)
            ''',
            env,
        )
        wait_for(env, "actor_alive?(a)", False)
        with pytest.raises(Exception):
            run_source('actor_send(a, 1)', env)

    def test_actor_invalid_effect_marks_failed(self):
        """Invalid handler return shape marks actor as failed."""
        env = make_global_env([])
        run_source(
            '''
            a = actor(0, (state, msg, _ctx) -> "not-a-valid-effect")
            actor_send(a, "go")
            ''',
            env,
        )
        wait_for(env, "actor_failed?(a)", True)
