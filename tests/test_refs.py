import threading
import time

from genia import make_global_env, run_source


def test_ref_holds_initial_value(run):
    src = '''
    r = ref(41)
    ref_get(r)
    '''
    assert run(src) == 41


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
