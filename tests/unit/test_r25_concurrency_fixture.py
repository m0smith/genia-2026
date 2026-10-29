"""Python-host scheduling tests for private R25 fixture mechanics, not portable authority."""

from __future__ import annotations

from pathlib import Path
import threading

import yaml

from hosts.python.exec_r25_concurrency_fixture import _build_env
from hosts.python.exec_eval import run_eval_subprocess
from genia import make_global_env, run_source
from genia.values import GeniaProcess, GeniaRef


def test_shared_fifo_fixture_admits_messages_before_terminal_failure(monkeypatch) -> None:
    """Force the worker ahead of the sender, exposing admission races without sleeps."""
    case_path = Path(__file__).resolve().parents[2] / "spec/eval/r25-process-fifo-fail-stop.yaml"
    case = yaml.safe_load(case_path.read_text(encoding="utf-8"))
    boundary = threading.Event()
    failed_handler = threading.Event()
    sender_thread = threading.current_thread()
    original_get = GeniaRef.get
    original_error_text = GeniaProcess._error_text
    original_send = GeniaProcess.send

    def observe_blocking_read(ref):
        """Signal that the worker reached a Ref wait the sender can release."""
        if threading.current_thread() is not sender_thread and not ref.is_set():
            boundary.set()
        return original_get(ref)

    def observe_handler_failure(process, error):
        """Signal an ungated handler error while preserving diagnostic formatting."""
        failed_handler.set()
        boundary.set()
        return original_error_text(process, error)

    def yield_to_worker_after_boom(process, message):
        """Advance the worker to a causal boundary before the sender continues."""
        original_send(process, message)
        if message == "boom":
            assert boundary.wait(5), "worker reached neither blocking Ref nor failure"
            if failed_handler.is_set():
                process._thread.join(5)
                assert not process._thread.is_alive(), "failing worker did not terminate"

    monkeypatch.setattr(GeniaRef, "get", observe_blocking_read)
    monkeypatch.setattr(GeniaProcess, "_error_text", observe_handler_failure)
    monkeypatch.setattr(GeniaProcess, "send", yield_to_worker_after_boom)
    result = run_source(case["input"]["source"], _build_env())
    assert result == [[1, 2], True, False, True]


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


def test_r25_fixture_waits_for_process_failure_thread_exit() -> None:
    result = run_eval_subprocess(
        """
        log = ref([])
        handle(msg) =
          "boom" -> 1 / 0 |
          value -> ref_update(log, (xs) -> append(xs, [value]))
        p = spawn(handle)
        send(p, 1)
        send(p, "boom")
        _r25_await_idle()
        [ref_get(log), process_failed?(p), process_alive?(p), some?(process_error(p))]
        """,
        None,
        ("r25_concurrency",),
    )
    assert result == {
        "stdout": "[[1], true, false, true]\n",
        "stderr": "",
        "exit_code": 0,
    }


def test_r25_fixture_post_failure_send_keeps_python_error_contract() -> None:
    """Settling terminal failure must not reopen admission in the Python host."""
    result = run_eval_subprocess(
        """
        p = spawn((msg) -> 1 / 0)
        send(p, 1)
        _r25_await_idle()
        send(p, 2)
        print("unreachable")
        """,
        None,
        ("r25_concurrency",),
    )
    assert result == {
        "stdout": "",
        "stderr": "Error: Process has failed: ZeroDivisionError: exact division by zero\n",
        "exit_code": 1,
    }
