import time

from genia import make_global_env, run_source


def test_agent_increment_updates_state_correctly():
    env = make_global_env([])
    run_source(
        """
        a = agent(0)
        agent_send(a, (x) -> x + 1)
        agent_send(a, (x) -> x + 1)
        """,
        env,
    )

    for _ in range(100):
        if run_source("agent_get(a)", env) == 2:
            break
        time.sleep(0.01)

    assert run_source("agent_get(a)", env) == 2


def test_agent_processes_multiple_sends_in_order():
    env = make_global_env([])
    run_source(
        """
        a = agent(1)
        agent_send(a, (x) -> x + 2)
        agent_send(a, (x) -> x * 10)
        """,
        env,
    )

    for _ in range(100):
        if run_source("agent_get(a)", env) == 30:
            break
        time.sleep(0.01)

    assert run_source("agent_get(a)", env) == 30


def test_agent_get_and_agent_state_return_current_state():
    env = make_global_env([])
    run_source(
        """
        a = agent(41)
        agent_send(a, (x) -> x + 1)
        """,
        env,
    )

    for _ in range(100):
        if run_source("agent_state(a)", env) == 42:
            break
        time.sleep(0.01)

    assert run_source("agent_get(a)", env) == 42
    assert run_source("agent_state(a)", env) == 42


def test_agent_updates_are_asynchronous_relative_to_caller():
    env = make_global_env([])
    run_source(
        """
        gate = ref()
        a = agent(0)
        agent_send(a, (_) -> ref_get(gate))
        agent_send(a, (x) -> x + 1)
        """,
        env,
    )

    assert run_source("agent_get(a)", env) == 0

    run_source("ref_set(gate, 41)", env)
    for _ in range(100):
        if run_source("agent_get(a)", env) == 42:
            break
        time.sleep(0.01)

    assert run_source("agent_get(a)", env) == 42


def test_agent_alive_reports_worker_status():
    env = make_global_env([])
    assert run_source("agent_alive?(agent(0))", env) is True
