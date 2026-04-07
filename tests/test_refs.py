import threading
import time

from genia import make_global_env, run_source


def test_ref_holds_initial_value(run):
    src = '''
    r = ref(41)
    ref_get(r)
    '''
    assert run(src) == 41


def test_ref_public_wrappers_work_as_function_values(run):
    src = '''
    r = apply(ref, [41])
    apply(ref_update, [r, (x) -> x + 1])
    apply(ref_get, [r])
    '''
    assert run(src) == 42


def test_ref_update_is_atomic_function_application(run):
    src = '''
    r = ref(1)
    ref_update(r, (x) -> x + 41)
    ref_get(r)
    '''
    assert run(src) == 42


def test_ref_get_blocks_until_set():
    env = make_global_env([])
    run_source("r = ref()", env)

    result: dict[str, object] = {}

    def waiting_reader():
        result["value"] = run_source("ref_get(r)", env)

    reader = threading.Thread(target=waiting_reader)
    reader.start()

    time.sleep(0.05)
    assert reader.is_alive()

    run_source("ref_set(r, 99)", env)
    reader.join(timeout=1)

    assert result["value"] == 99


def test_multiple_waiting_readers_wake_after_set():
    env = make_global_env([])
    run_source("r = ref()", env)

    started = threading.Barrier(4)
    results: list[object] = []
    lock = threading.Lock()

    def waiting_reader():
        started.wait()
        value = run_source("ref_get(r)", env)
        with lock:
            results.append(value)

    readers = [threading.Thread(target=waiting_reader) for _ in range(3)]
    for reader in readers:
        reader.start()

    started.wait()
    time.sleep(0.05)
    assert all(reader.is_alive() for reader in readers)

    run_source("ref_set(r, 123)", env)
    for reader in readers:
        reader.join(timeout=1)

    assert results == [123, 123, 123]


def test_multiple_sequential_ref_update_calls_are_serialized(run):
    src = """
    r = ref(0)
    ref_update(r, (x) -> x + 1)
    ref_update(r, (x) -> x + 2)
    ref_update(r, (x) -> x * 10)
    ref_get(r)
    """
    assert run(src) == 30


def test_ref_update_blocks_until_set():
    env = make_global_env([])
    run_source("r = ref()", env)

    result: dict[str, object] = {}

    def waiting_updater():
        result["value"] = run_source("ref_update(r, (x) -> x + 1)", env)

    updater = threading.Thread(target=waiting_updater)
    updater.start()

    time.sleep(0.05)
    assert updater.is_alive()
    assert run_source("ref_is_set(r)", env) is False

    run_source("ref_set(r, 41)", env)
    updater.join(timeout=1)

    assert result["value"] == 42
    assert run_source("ref_get(r)", env) == 42
    assert run_source("ref_is_set(r)", env) is True
