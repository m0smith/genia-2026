from __future__ import annotations

from hosts.python.exec_eval import run_eval_subprocess
from genia import make_global_env, run_source


def test_r25_await_idle_is_not_in_the_ordinary_environment() -> None:
    env = make_global_env([])
    try:
        run_source("_r25_await_idle()", env)
    except Exception as exc:  # noqa: BLE001
        assert "Undefined" in str(exc)
    else:  # pragma: no cover - required failing assertion
        raise AssertionError("private R25 fixture leaked into the ordinary environment")


def test_r25_fixture_waits_for_cell_failure_transition_without_polling() -> None:
    result = run_eval_subprocess(
        """
        state = ref(10)
        c = cell_with_state(state)
        cell_send(c, (x) -> x + 5)
        cell_send(c, (_) -> 1 / 0)
        _r25_await_idle()
        [ref_get(state), cell_failed?(c), cell_status(c), some?(cell_error(c))]
        """,
        None,
        ("r25_concurrency",),
    )
    assert result == {
        "stdout": '[15, true, "failed", true]\n',
        "stderr": "",
        "exit_code": 0,
    }


def test_r25_fixture_reaches_fixed_point_for_nested_committed_send() -> None:
    result = run_eval_subprocess(
        """
        target = cell(10)
        source = cell(0)
        cell_send(source, (x) -> {
          cell_send(target, (n) -> n + 5)
          x + 1
        })
        _r25_await_idle()
        [cell_get(source), cell_get(target)]
        """,
        None,
        ("r25_concurrency",),
    )
    assert result == {"stdout": "[1, 15]\n", "stderr": "", "exit_code": 0}
