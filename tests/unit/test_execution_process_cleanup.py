"""FAILING-TEST PHASE — Group I: cleanup / no leaked child (CRITICAL).

Targets `genia.process_transport.launch_process`. For every terminal path
that starts a child, no owned child may remain running after the call
returns (contract §8/§12: "no owned child may remain running indefinitely
after the call returns").

To observe child liveness without relying on the OS eventually reaping a
zombie, these tests inject a spy PID collector via an anticipated
`spawn_hook` keyword on `launch_process` (mirroring `send_http_request`'s
existing `transport=None` injection seam in
`src/genia/http_transport.py`). If the implementation phase settles on a
different injection seam name, these call sites need matching adjustment
-- the *liveness assertion* (`_process_is_alive`, using `os.kill(pid, 0)`,
zero-signal probing, which is portable across POSIX Python hosts) is what
encodes the actual portable guarantee, not the seam's exact name.

Uses bounded polling (`_wait_until_dead`), never a fixed long sleep, per
the RED-phase reliability rules.

`execution.process` is NOT implemented yet; every test fails today with
`ModuleNotFoundError` -- the correct RED state for this phase.
"""

from __future__ import annotations

import os
import signal
import time

import pytest

from tests.fixtures.process_fixtures import (
    exit_with,
    sleep_forever_ignoring_term,
    write_n_bytes,
    OUTPUT_LIMIT_BYTES,
)

_POLL_INTERVAL_SECONDS = 0.05
_POLL_BOUND_SECONDS = 5


def _process_is_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _wait_until_dead(pid: int, *, bound_seconds: float = _POLL_BOUND_SECONDS) -> bool:
    """Bounded polling, not an arbitrary long sleep: returns True once the
    process is confirmed dead, False if it is still alive after the bound.
    """
    deadline = time.monotonic() + bound_seconds
    while time.monotonic() < deadline:
        if not _process_is_alive(pid):
            return True
        time.sleep(_POLL_INTERVAL_SECONDS)
    return not _process_is_alive(pid)


def _launch_capturing_pid(argv: list[str], timeout_ms: int):
    from tests.fixtures.execution_process_helpers import process_transport_module

    module = process_transport_module()
    executable, *args = argv
    captured: dict[str, int] = {}

    def _spawn_hook(pid: int) -> None:
        captured["pid"] = pid

    result = module.launch_process(executable, args, timeout_ms, spawn_hook=_spawn_hook)
    return result, captured.get("pid")


def _assert_no_leaked_child(pid, *, context: str) -> None:
    if pid is None:
        pytest.fail(
            f"{context}: no PID was captured via spawn_hook -- either no child "
            "was ever created (fine for a pure resolution failure) or the "
            "anticipated spawn_hook seam does not exist yet"
        )
    try:
        still_alive = not _wait_until_dead(pid)
        assert not still_alive, (
            f"{context}: child pid {pid} is still alive after the call returned "
            "and after bounded polling -- this is exactly the owned-child leak "
            "the contract forbids (contract §8/§12)"
        )
    finally:
        # Force-kill regardless of outcome: a genuinely broken implementation
        # must not leave a real process running on the test host past this
        # test's failure, even though the assertion above already reports
        # the defect.
        if _process_is_alive(pid):
            try:
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass


def test_no_leaked_child_after_normal_exit():
    result, pid = _launch_capturing_pid(exit_with(0), timeout_ms=5000)
    _assert_no_leaked_child(pid, context="normal exit 0")


def test_no_leaked_child_after_nonzero_exit():
    result, pid = _launch_capturing_pid(exit_with(7), timeout_ms=5000)
    _assert_no_leaked_child(pid, context="nonzero exit 7")


def test_no_leaked_child_after_timeout_even_when_child_ignores_sigterm():
    """The strongest version of this guarantee: the child deliberately
    ignores SIGTERM, so cleanup must use a mechanism strong enough to still
    guarantee termination (e.g. SIGKILL on POSIX) -- a cleanup path that
    only sends SIGTERM and trusts the child to cooperate is not sufficient.
    """
    result, pid = _launch_capturing_pid(sleep_forever_ignoring_term(), timeout_ms=200)
    _assert_no_leaked_child(pid, context="timeout against a SIGTERM-ignoring child")


def test_no_leaked_child_after_stdout_overflow():
    result, pid = _launch_capturing_pid(
        write_n_bytes("stdout", OUTPUT_LIMIT_BYTES + 1), timeout_ms=15000
    )
    _assert_no_leaked_child(pid, context="stdout overflow")


def test_no_leaked_child_after_stderr_overflow():
    result, pid = _launch_capturing_pid(
        write_n_bytes("stderr", OUTPUT_LIMIT_BYTES + 1), timeout_ms=15000
    )
    _assert_no_leaked_child(pid, context="stderr overflow")


def test_no_leaked_child_after_launch_failure():
    """A launch failure may mean no child was ever created at all (contract
    §7 ownership table: "no child was ever created, or a partially-created
    one is killed"). This test only asserts the *outcome* is a normalized
    failure -- if a PID was captured, it must still not be leaked.
    """
    from tests.fixtures.process_fixtures import nonexistent_target_path
    from tests.fixtures.execution_process_helpers import process_transport_module

    module = process_transport_module()
    captured: dict[str, int] = {}

    def _spawn_hook(pid: int) -> None:
        captured["pid"] = pid

    result = module.launch_process(
        nonexistent_target_path(), [], 1000, spawn_hook=_spawn_hook
    )

    assert isinstance(result, module.ProcessTransportFailure)
    assert result.kind == "launch"
    if "pid" in captured:
        _assert_no_leaked_child(captured["pid"], context="launch failure (partial create)")
