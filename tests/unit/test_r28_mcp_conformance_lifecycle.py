"""R28 E28-5 (issue #706): conformance matrix, cancellation, timeout, lifecycle and leaks.

Matrix rows X1-X10, T1-T8, Y1-Y12 in docs/mcp/conformance-matrix.md. Python-host resource and
lifecycle tests (subprocess, signals, /proc); they add no Genia semantics. The existing E28-3/E28-4
suites (test_r28_mcp_run.py, test_r28_mcp_run_supervisor.py, test_r28_mcp_stdio_lifecycle.py)
remain the evidence for what they cover; this module adds the matrix edges they do not.

Synchronization follows ledger R28-H33: a readiness barrier, then bounded polling of observable
state (a governed worker exists, a directory is gone). Nothing here sleeps to *create* a
condition. Where a race is the subject (cancel against deadline or completion) the assertion is
the invariant (exactly one terminal state, no partial data, nothing survives), never which side
won. The 5,000 ms deadline is never lengthened to make a test pass.
"""

from __future__ import annotations

import json
import os
import signal
import time

import pytest

from tests.fixtures.r28_mcp_conformance import (
    NS_MODES,
    assert_closed_failure,
    assert_completed,
    env_for,
)
from tests.fixtures.r28_mcp_helpers import (
    RUN_CANCELLED_MESSAGE,
    RUN_TIMEOUT_MESSAGE,
    LauncherSession,
    cancel_notification,
    configured_session,
    identity_exists,
    notification,
    process_children,
    request,
    run_request,
    structured,
    worker_workdir,
)

pytestmark = pytest.mark.unit

LOOP = "loop(n) = loop(n + 1)\nloop(0)"
DEADLINE_S = 5.0
GRACE_S = 60


def _gone(identities):
    return [i for i in identities if identity_exists(i)] == []


def _wait_until(condition, timeout=GRACE_S):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if condition():
            return True
        time.sleep(0.01)
    return condition()


def _session(mode):
    return LauncherSession(env=env_for(mode))


# --- X: the cancellation matrix --------------------------------------------------------------


@pytest.mark.parametrize(
    "label, message",
    [
        ("string-id-for-an-integer-request", notification("notifications/cancelled", {"requestId": "7"})),
        ("missing-requestId", notification("notifications/cancelled", {"reason": "x"})),
        ("null-requestId", notification("notifications/cancelled", {"requestId": None})),
        ("no-params", notification("notifications/cancelled")),
        ("wrong-request-id", cancel_notification(8)),
        ("cancel-sent-as-a-request", request("notifications/cancelled", 99, {"requestId": 7})),
    ],
    ids=lambda v: v if isinstance(v, str) else "",
)
def test_a_cancel_that_does_not_name_the_running_request_is_ignored(label, message):
    with LauncherSession() as session:
        session.wait_ready()
        session.send(run_request("sleep(800)\n5", 7))
        session.wait_for_worker()
        session.send(message)
        response = session.read(timeout=60)
        assert response["id"] == 7
        assert assert_completed(response)["value"]["rendered"] == "5"  # not cancelled


def test_duplicate_cancellations_cancel_exactly_once_and_never_a_later_request():
    with LauncherSession() as session:
        session.wait_ready()
        session.send(run_request(LOOP, 7))
        workers = session.wait_for_worker()
        for _ in range(3):
            session.send(cancel_notification(7))
        first = session.read(timeout=60)
        assert first["id"] == 7
        assert_closed_failure(first, "cancelled", "execution", RUN_CANCELLED_MESSAGE)
        # Stale duplicates left in the queue must not cancel the next request.
        session.send(run_request("sleep(500)\n11", 8))
        second = session.read(timeout=60)
        assert second["id"] == 8 and assert_completed(second)["value"]["rendered"] == "11"
        assert _gone(workers) and session.governed_workers() == set()


@pytest.mark.parametrize("mode", NS_MODES)
def test_cancel_queued_with_the_request_wins_and_the_worker_is_reaped(mode):
    with _session(mode) as session:
        session.wait_ready()
        session.send(run_request(LOOP, 3))
        session.send(cancel_notification(3))
        response = session.read(timeout=60)
        assert_closed_failure(response, "cancelled", "execution", RUN_CANCELLED_MESSAGE)
        assert session.governed_workers() == set()


@pytest.mark.parametrize("mode", NS_MODES)
def test_cancel_during_evaluation_returns_no_partial_data_and_removes_the_workdir(mode):
    with _session(mode) as session:
        session.wait_ready()
        session.send(run_request('print("PARTIAL-OUT")\nwriteln(stderr, "PARTIAL-ERR")\n' + LOOP, 4))
        workers = session.wait_for_worker()
        workdirs = {worker_workdir(w) for w in workers} - {None}
        assert workdirs, "the worker's private directory was not observable"
        session.send(cancel_notification(4))
        response = session.read(timeout=60)
        assert_closed_failure(response, "cancelled", "execution", RUN_CANCELLED_MESSAGE)
        assert "PARTIAL" not in json.dumps(response)
        assert _gone(workers)
        assert all(not d.exists() for d in workdirs), "private temp directory outlived the call"
        # first terminal state wins: a later cancel for the finished id changes nothing
        session.send(cancel_notification(4))
        session.send(run_request("1 + 1", 5))
        after = session.read(timeout=60)
        assert after["id"] == 5 and assert_completed(after)["value"]["rendered"] == "2"


def test_cancellation_near_successful_completion_yields_exactly_one_whole_terminal_state():
    delays = [0.0, 0.15, 0.3, 0.5, 0.9]  # the same program, cancel arriving ever later
    with LauncherSession() as session:
        session.wait_ready()
        outcomes = []
        for index, delay in enumerate(delays):
            rid = 100 + index
            session.send(run_request('print("whole")\nsleep(400)\n7', rid))
            workers = session.wait_for_worker()
            time.sleep(delay)  # the race is the subject; the assertion below is an invariant
            session.send(cancel_notification(rid))
            response = session.read(timeout=60)
            assert response["id"] == rid
            envelope = structured(response)[1]
            if envelope["status"] == "ok":  # finished first: complete and unmodified
                result = assert_completed(response)
                assert (result["value"]["rendered"], result["stdout"]) == ("7", "whole\n")
                outcomes.append("completed")
            else:  # cancelled first: only the fixed envelope, nothing partial
                assert_closed_failure(response, "cancelled", "execution", RUN_CANCELLED_MESSAGE)
                assert "whole" not in json.dumps(response)
                outcomes.append("cancelled")
            assert _wait_until(lambda: session.governed_workers() == set())
            assert _gone(workers)
        # nothing extra was written: one frame per request, in order
        assert session.raw_stdout.count(b"\n") - 1 == len(delays)  # minus the readiness probe
        assert set(outcomes) <= {"completed", "cancelled"}


def test_cancellation_near_the_deadline_yields_exactly_one_terminal_state():
    with LauncherSession() as session:
        session.wait_ready()
        for rid, delay in ((201, DEADLINE_S - 0.6), (202, DEADLINE_S + 0.4)):
            session.send(run_request(LOOP, rid))
            workers = session.wait_for_worker()
            time.sleep(delay)
            session.send(cancel_notification(rid))
            response = session.read(timeout=60)
            assert response["id"] == rid
            envelope = structured(response)[1]
            assert envelope["status"] == "error" and envelope["result"] is None
            assert envelope["error"]["kind"] in {"cancelled", "timeout"}
            expected = {
                "cancelled": RUN_CANCELLED_MESSAGE,
                "timeout": RUN_TIMEOUT_MESSAGE,
            }[envelope["error"]["kind"]]
            assert_closed_failure(response, envelope["error"]["kind"], "execution", expected)
            assert _gone(workers) and session.governed_workers() == set()
        session.send(run_request("2 + 2", 203))
        assert assert_completed(session.read(timeout=60))["value"]["rendered"] == "4"


# --- T: the timeout matrix -------------------------------------------------------------------


@pytest.mark.parametrize("mode", NS_MODES)
def test_timeout_is_fixed_closed_partial_free_and_the_next_request_still_works(mode):
    source = 'print("PARTIAL-OUT")\nwriteln(stderr, "PARTIAL-ERR")\n' + LOOP
    with _session(mode) as session:
        session.wait_ready()
        session.send(run_request(source, 1))
        workers = session.wait_for_worker()
        workdirs = {worker_workdir(w) for w in workers} - {None}
        session.send(run_request("6 * 7", 2))  # queued behind the run; not charged to its deadline
        sent = time.monotonic()
        response = session.read(timeout=60)
        elapsed = time.monotonic() - sent
        assert_closed_failure(response, "timeout", "execution", RUN_TIMEOUT_MESSAGE)
        assert "PARTIAL" not in json.dumps(response)
        # The clock starts at worker readiness, which is after the worker appeared, so the
        # response cannot precede the deadline (a load-independent lower bound).
        assert elapsed >= DEADLINE_S - 0.5, elapsed
        assert _gone(workers), "timed-out worker was not killed and reaped"
        assert all(not d.exists() for d in workdirs)
        follow = session.read(timeout=60)
        assert follow["id"] == 2 and assert_completed(follow)["value"]["rendered"] == "42"


@pytest.mark.parametrize(
    "source",
    ["rand_flow(1) |> each((x) -> x) |> run", "sleep(600000)"],
    ids=["unbounded-flow-without-output", "long-sleep"],
)
def test_other_unbounded_programs_are_bounded_by_the_same_fixed_deadline(source):
    with LauncherSession() as session:
        session.wait_ready()
        session.send(run_request(source, 1))
        workers = session.wait_for_worker()
        response = session.read(timeout=60)
        assert_closed_failure(response, "timeout", "execution", RUN_TIMEOUT_MESSAGE)
        assert _gone(workers) and session.governed_workers() == set()


def test_overflow_kills_the_worker_and_removes_its_private_directory():
    flood = (
        'rand_flow(1) |> each((x) -> write(stdout, '
        '"xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")) |> run'
    )
    with LauncherSession() as session:
        session.wait_ready()
        session.send(run_request(flood, 1))
        workers = session.wait_for_worker()
        workdirs = {worker_workdir(w) for w in workers} - {None}
        response = session.read(timeout=60)
        assert structured(response)[1]["error"]["kind"] == "result_limit"
        assert _gone(workers) and all(not d.exists() for d in workdirs)


def test_no_worker_remains_after_a_mixed_session_of_every_terminal_state():
    sources = [
        "1 + 1",  # completed
        "f(x) =",  # parse_error
        'read_file("/etc/hostname")',  # policy_denied
        "1 / 0",  # runtime_error
        "= " * 140000,  # input_limit
    ]
    with LauncherSession() as session:
        session.wait_ready()
        for index, source in enumerate(sources):
            session.send(run_request(source, index + 1))
            assert session.read(timeout=60)["id"] == index + 1
            assert session.governed_workers() == set()
        before = session.descendants()
        session.send(run_request(LOOP, 90))
        session.wait_for_worker()
        session.send(cancel_notification(90))
        session.read(timeout=60)
        assert session.governed_workers() == set()
        assert session.descendants() == before  # no extra process of any kind remains


# --- Y: lifecycle and leaks --------------------------------------------------------------------


def test_sighup_to_the_client_launched_process_stops_the_chain_and_cleans_up():
    # SIGTERM and SIGINT are covered by test_r28_mcp_stdio_lifecycle.py; SIGHUP is forwarded by the
    # launcher too (E28-4 design section 6) and is recorded here as matrix row Y5.
    with configured_session() as session:
        session.wait_ready()
        session.send(run_request("sleep(60000)", 1))
        workers = session.wait_for_worker()
        workdirs = {worker_workdir(w) for w in workers} - {None}
        chain = {i for i in (_identity(p) for p in process_children(session.proc.pid)) if i}
        session.proc.send_signal(signal.SIGHUP)
        assert _wait_until(lambda: session.proc.poll() is not None)
        assert _wait_until(lambda: _gone(chain | workers)), "processes survived SIGHUP"
        assert _wait_until(lambda: all(not d.exists() for d in workdirs))


def _identity(pid):
    from tests.fixtures.r28_mcp_helpers import process_identity

    return process_identity(pid)


def test_a_discover_probe_launch_followed_by_a_session_launch_leaves_nothing_behind():
    # The official v2 client in `auto` mode starts a `server/discover` probe process and then the
    # session process (ledger R28-H37). Each launch is independent and fully cleaned up.
    seen = []
    for launch in range(2):
        with configured_session() as session:
            session.wait_ready()
            if launch == 1:
                session.send(run_request("21 * 2", 1))
                assert assert_completed(session.read(timeout=60))["value"]["rendered"] == "42"
            seen.append(session.proc.pid)
            chain = {i for i in (_identity(p) for p in process_children(session.proc.pid)) if i}
        assert _wait_until(lambda: _gone(chain)), "a launch left processes behind"
    assert seen[0] != seen[1]


@pytest.mark.parametrize("mode", NS_MODES)
def test_sigterm_to_the_host_mid_run_reaps_the_worker_and_removes_its_directory(mode):
    with _session(mode) as session:
        session.wait_ready()
        session.send(run_request("sleep(60000)", 1))
        workers = session.wait_for_worker()
        workdirs = {worker_workdir(w) for w in workers} - {None}
        assert workdirs
        host_pid = _host_of(session)
        os.kill(host_pid, signal.SIGTERM)
        assert _wait_until(lambda: _gone(workers)), "worker survived host SIGTERM"
        assert _wait_until(lambda: all(not d.exists() for d in workdirs))


def _host_of(session):
    from tests.fixtures.r28_mcp_helpers import _cmdline

    for pid in process_children(session.proc.pid):
        if any("hosts.python.mcp_host" in part for part in _cmdline(pid)):
            return pid
    # Direct launcher mode: the host is the launcher's child; fall back to any python child.
    for pid in process_children(session.proc.pid):
        if any("mcp_host" in part for part in _cmdline(pid)):
            return pid
    raise AssertionError("host process not found")
