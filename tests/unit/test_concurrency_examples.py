import time

from genia import make_global_env, run_source


def wait_for(env, expr, expected, *, timeout_s=1.0, sleep_s=0.01):
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        if run_source(expr, env) == expected:
            return
        time.sleep(sleep_s)
    assert run_source(expr, env) == expected


def test_example_basic_process_send():
    env = make_global_env([])
    run_source(
        '''
        inbox = ref([])
        p = spawn((msg) -> ref_update(inbox, (xs) -> append(xs, [msg])))
        send(p, "a")
        send(p, "b")
        send(p, "c")
        ''',
        env,
    )

    wait_for(env, "ref_get(inbox)", ["a", "b", "c"])


def test_example_ref_used_with_process():
    env = make_global_env([])
    run_source(
        '''
        total = ref(0)
        p = spawn((msg) -> ref_update(total, (n) -> n + msg))
        send(p, 10)
        send(p, 5)
        send(p, -2)
        ''',
        env,
    )

    wait_for(env, "ref_get(total)", 13)


def test_example_simple_counter_cell():
    env = make_global_env([])
    run_source(
        '''
        counter = cell(0)
        cell_send(counter, (n) -> n + 1)
        cell_send(counter, (n) -> n + 1)
        cell_send(counter, (n) -> n + 1)
        ''',
        env,
    )

    wait_for(env, "cell_get(counter)", 3)


def test_example_logging_background_worker_pattern():
    env = make_global_env([])
    run_source(
        '''
        append_logged(xs, msg) {
          log(msg)
          append(xs, [msg])
        }

        logs = ref([])
        logger = spawn((msg) -> ref_update(logs, (xs) -> append_logged(xs, msg)))
        send(logger, "boot")
        send(logger, "request")
        send(logger, "done")
        ''',
        env,
    )

    wait_for(env, "ref_get(logs)", ["boot", "request", "done"])


# ---------------------------------------------------------------------------
# Process fail-stop behaviour
# ---------------------------------------------------------------------------


def test_process_fail_stop_marks_failed():
    """Handler exception sets process_failed? to true."""
    env = make_global_env([])
    run_source(
        '''
        boom = spawn((msg) -> 1 / 0)
        send(boom, "trigger")
        ''',
        env,
    )
    wait_for(env, "process_failed?(boom)", True)
    wait_for(env, "process_alive?(boom)", False)


def test_process_fail_stop_error_message():
    """process_error returns Some(message) after failure."""
    env = make_global_env([])
    run_source(
        '''
        bad = spawn((msg) -> 1 / 0)
        send(bad, "x")
        ''',
        env,
    )
    wait_for(env, "process_failed?(bad)", True)
    result = run_source("process_error(bad)", env)
    # GeniaOptionSome wraps the error string
    assert hasattr(result, "value"), f"expected Some(...), got {result!r}"
    assert "ZeroDivisionError" in result.value


def test_process_error_none_when_healthy():
    """process_error returns none on a healthy process."""
    env = make_global_env([])
    run_source(
        '''
        ok_proc = spawn((msg) -> msg)
        send(ok_proc, "hello")
        ''',
        env,
    )
    # Give process time to consume message
    import time
    time.sleep(0.05)
    result = run_source("process_error(ok_proc)", env)
    # Should be OPTION_NONE (no .value attribute)
    assert not hasattr(result, "value"), f"expected none, got {result!r}"


def test_process_send_after_failure_raises():
    """Sending to a failed process raises a runtime error."""
    import pytest as _pytest

    env = make_global_env([])
    run_source(
        '''
        doomed = spawn((msg) -> 1 / 0)
        send(doomed, "first")
        ''',
        env,
    )
    wait_for(env, "process_failed?(doomed)", True)
    with _pytest.raises(Exception, match="Process has failed"):
        run_source('send(doomed, "second")', env)


def test_process_processes_messages_before_failure():
    """A process handles messages in order; earlier ones complete before a later one fails."""
    env = make_global_env([])
    run_source(
        '''
        log = ref([])
        handle(msg) {
            ref_update(log, (xs) -> append(xs, [msg]))
            1 / msg
        }
        fragile = spawn(handle)
        send(fragile, 2)
        send(fragile, 1)
        send(fragile, 0)
        ''',
        env,
    )
    wait_for(env, "process_failed?(fragile)", True)
    # Messages 2 and 1 succeed (1/2, 1/1 ok). Message 0 triggers div-by-zero after updating log.
    wait_for(env, "ref_get(log)", [2, 1, 0])
