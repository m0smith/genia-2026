import pytest

from genia import make_global_env, run_source


def pytest_collection_modifyitems(items):
    """Keep loopback socket tests on one xdist worker.

    Several loopback tests discover an unused port before their server thread
    binds it. Running those tests on different workers leaves a cross-process
    race where a request can reach another test's server and receive its 404.
    The loopback partition is small, so grouping it provides deterministic
    ownership without changing runtime behavior or hiding genuine failures.
    """
    for item in items:
        if item.get_closest_marker("loopback") is not None:
            item.add_marker(pytest.mark.xdist_group("loopback"))


def eval_code(src: str, stdin_data=None):
    env = make_global_env([] if stdin_data is None else stdin_data)
    return run_source(src, env)


@pytest.fixture
def run():
    return eval_code
