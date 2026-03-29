import threading
import time

import pytest

from genia import make_global_env, run_source


def test_process_builtins_are_available_in_global_env():
    env = make_global_env([])
    assert callable(env.get("spawn"))
    assert callable(env.get("send"))
    assert callable(env.get("process_alive?"))


def test_spawn_returns_handle():
    env = make_global_env([])
    process = run_source("spawn((msg) -> msg)", env)
    assert process is not None
    assert "process" in repr(process)


def test_send_delivers_messages_in_order():
    env = make_global_env([])
    run_source(
        """
        out = ref([])
        p = spawn((msg) -> ref_update(out, (xs) -> append(xs, [msg])))
        send(p, 1)
        send(p, 2)
        send(p, 3)
        """,
        env,
    )

    for _ in range(100):
        if run_source("ref_get(out)", env) == [1, 2, 3]:
            break
        time.sleep(0.01)
    assert run_source("ref_get(out)", env) == [1, 2, 3]


def test_process_handler_updates_shared_state_predictably():
    env = make_global_env([])
    run_source(
        """
        total = ref(0)
        p = spawn((msg) -> ref_update(total, (n) -> n + msg))
        """,
        env,
    )

    threads = [threading.Thread(target=lambda: run_source("send(p, 1)", env)) for _ in range(25)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=1)

    for _ in range(100):
        if run_source("ref_get(total)", env) == 25:
            break
        time.sleep(0.01)
    assert run_source("ref_get(total)", env) == 25


def test_process_alive_reports_useful_status():
    env = make_global_env([])
    assert run_source("process_alive?(spawn((msg) -> msg))", env) is True


def test_send_rejects_non_process_value():
    env = make_global_env([])
    with pytest.raises(TypeError, match="send expected a process as first argument"):
        run_source("send(123, 1)", env)
