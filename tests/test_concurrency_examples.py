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


def test_example_simple_counter_agent():
    env = make_global_env([])
    run_source(
        '''
        counter = agent(0)
        agent_send(counter, (n) -> n + 1)
        agent_send(counter, (n) -> n + 1)
        agent_send(counter, (n) -> n + 1)
        ''',
        env,
    )

    wait_for(env, "agent_get(counter)", 3)


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
