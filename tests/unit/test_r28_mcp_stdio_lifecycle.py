"""R28 E28-4 (issue #705): shutdown, client disconnect, and process hygiene over stdio.

Every test uses the exact configured command (a four-level chain: wrapper, launcher, host, and
the governed worker) and strict reap checks (an unreaped process counts as alive). Synchronization
is by readiness barrier and bounded observable polling, never fixed sleeps. Pinned to
docs/design/r28-e28-4-stdio-transport-design.md section 6 (ledger R28-H37, R28-H38). Cases marked
RED fail until E28-4 lands; the others pin behavior that must not regress.
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time

import pytest

from tests.fixtures.r28_mcp_helpers import (
    REPO_ROOT,
    RUN_CANCELLED_MESSAGE,
    _cmdline,
    cancel_notification,
    completed_envelope,
    configured_session,
    error_envelope,
    identity_exists,
    process_children,
    process_identity,
    run_request,
    server_env,
    structured,
    worker_workdir,
)

pytestmark = pytest.mark.unit

CANCELLED = error_envelope("cancelled", "execution", RUN_CANCELLED_MESSAGE)
GRACE_S = 60  # an upper bound for observable conditions only, never a sleep


def _wait_until(condition, timeout=GRACE_S):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if condition():
            return True
        time.sleep(0.01)
    return condition()


def _chain(session):
    """Identities of every live process below the client-launched top process."""
    return {
        process_identity(pid)
        for pid in process_children(session.proc.pid)
        if process_identity(pid) is not None
    }


def _survivors(identities):
    return [i for i in identities if identity_exists(i)]


def _in_flight(session):
    """A run in flight with a governed worker; returns (chain, worker identities, workdirs)."""
    session.wait_ready()
    session.send(run_request("sleep(60000)", 1))
    workers = session.wait_for_worker()
    workdirs = {worker_workdir(w) for w in workers} - {None}
    return _chain(session), workers, workdirs


def _host_pid(session):
    for pid in process_children(session.proc.pid):
        if any("hosts.python.mcp_host" in part for part in _cmdline(pid)):
            return pid
    raise AssertionError("host process not found")


# --- behavior that already holds and must keep holding -------------------------------------


def test_closing_stdin_while_idle_exits_cleanly_and_leaves_nothing():
    with configured_session() as session:
        session.wait_ready()
        chain = _chain(session)
        session.proc.stdin.close()
        assert session.proc.wait(timeout=GRACE_S) == 0
        assert _wait_until(lambda: not _survivors(chain))


def test_closing_stdin_mid_run_lets_the_run_finish_then_exits():
    with configured_session() as session:
        session.wait_ready()
        session.send(run_request("sleep(1500)\n7", 1))
        session.proc.stdin.close()  # a half-close is a legitimate batch client
        response = session.read(timeout=GRACE_S)
        assert structured(response)[1] == completed_envelope("7")
        assert session.proc.wait(timeout=GRACE_S) == 0


def test_a_client_that_closes_both_streams_mid_run_leaves_no_survivors():
    with configured_session() as session:
        chain, workers, workdirs = _in_flight(session)
        session.proc.stdin.close()
        session.proc.stdout.close()
        session.proc.wait(timeout=GRACE_S)
        assert _wait_until(lambda: not _survivors(chain | workers))
        assert all(not d.exists() for d in workdirs)


def test_cancellation_still_reaps_the_worker_through_the_wrapper_chain():
    with configured_session() as session:
        session.wait_ready()
        session.send(run_request("sleep(60000)", 5))
        workers = session.wait_for_worker()
        session.send(cancel_notification(5))
        assert structured(session.read(timeout=GRACE_S))[1] == CANCELLED
        assert not _survivors(workers)


# --- RED: signals must tear the whole chain down --------------------------------------------


@pytest.mark.parametrize("sig", [signal.SIGTERM, signal.SIGINT], ids=["SIGTERM", "SIGINT"])
def test_a_signal_to_the_client_launched_process_stops_the_entire_chain_and_cleans_up(sig):
    with configured_session() as session:
        chain, workers, workdirs = _in_flight(session)
        assert workdirs, "the worker's private directory was not observable"
        os.kill(session.proc.pid, sig)  # what a stdio client sends to a server that lingers
        session.proc.wait(timeout=GRACE_S)
        assert _wait_until(lambda: not _survivors(chain | workers)), (
            "processes survived the signal: " + repr(_survivors(chain | workers))
        )
        assert all(not d.exists() for d in workdirs), "the worker's private directory leaked"


def test_sigterm_to_the_host_reaps_the_worker_and_removes_its_directory():
    with configured_session() as session:
        chain, workers, workdirs = _in_flight(session)
        assert workdirs
        os.kill(_host_pid(session), signal.SIGTERM)
        assert _wait_until(lambda: not _survivors(workers)), "the worker outlived its host"
        assert all(not d.exists() for d in workdirs), "the worker's private directory leaked"
        session.proc.stdin.close()
        session.proc.wait(timeout=GRACE_S)
        assert _wait_until(lambda: not _survivors(chain))


# --- RED: a worker whose host cannot clean up still ends (orphan backstop) -------------------


def _start_worker(backstop_seconds=None):
    code = "import hosts.python.mcp_worker as w\n"
    if backstop_seconds is not None:
        code += f"w.ORPHAN_BACKSTOP_SECONDS = {backstop_seconds}\n"
    code += "w.main()\n"
    return subprocess.Popen(
        [sys.executable, "-B", "-c", code],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=str(REPO_ROOT),
        env=server_env({"PYTHONPATH": f"{REPO_ROOT}:{REPO_ROOT / 'src'}"}),
    )


def _wait_ready(proc, timeout=GRACE_S):
    """Block until the worker prints its readiness marker (bootstrap is over)."""
    import select

    seen = b""
    deadline = time.monotonic() + timeout
    while b"GENIA-WORKER-READY" not in seen:
        remaining = deadline - time.monotonic()
        assert remaining > 0, "worker never reported readiness"
        if select.select([proc.stderr], [], [], remaining)[0]:
            chunk = os.read(proc.stderr.fileno(), 4096)
            assert chunk, "worker exited before reporting readiness"
            seen += chunk


def test_the_orphan_backstop_is_a_fixed_bound_beyond_the_execution_deadline():
    import hosts.python.mcp_run_capability as supervisor
    import hosts.python.mcp_worker as worker

    assert hasattr(worker, "ORPHAN_BACKSTOP_SECONDS"), "E28-4 not implemented: orphan backstop"
    # Not a second, shorter deadline: the supervisor ends a healthy run first.
    assert worker.ORPHAN_BACKSTOP_SECONDS > supervisor.DEADLINE_MS / 1000.0
    assert worker.ORPHAN_BACKSTOP_SECONDS <= 30


def test_a_worker_with_no_supervisor_ends_itself_after_the_backstop():
    proc = _start_worker(backstop_seconds=1)
    try:
        _wait_ready(proc)
        started = time.monotonic()
        proc.stdin.write(b"sleep(60000)")
        proc.stdin.close()  # the source is complete; nothing will ever kill or read the worker
        proc.wait(timeout=GRACE_S)
        elapsed = time.monotonic() - started
        assert proc.returncode == -signal.SIGALRM, proc.returncode
        assert elapsed < 30
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait()


def test_the_backstop_never_disturbs_a_run_that_finishes():
    proc = _start_worker(backstop_seconds=30)
    try:
        _wait_ready(proc)
        proc.stdin.write(b"1 + 2")
        proc.stdin.close()
        out = proc.stdout.read()
        proc.wait(timeout=GRACE_S)
        assert proc.returncode == 0
        assert b'"value": "3"' in out
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait()
