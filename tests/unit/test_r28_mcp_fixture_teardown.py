"""Python-host test-fixture cleanup of OS processes, not portable Genia semantics."""

import signal
import sys
import threading
import time

import pytest

from tests.fixtures.r28_mcp_helpers import (
    configured_session,
    LauncherSession,
    identity_exists,
    process_children,
    process_identity,
)


def test_client_context_exception_reaps_its_command_and_descendants():
    """An assertion in a client test must not abandon the launched process chain."""
    descendants = set()
    with pytest.raises(RuntimeError, match="public client test failure"):
        with configured_session() as session:
            session.wait_ready()
            descendants = {
                identity
                for pid in process_children(session.proc.pid)
                if (identity := process_identity(pid)) is not None
            }
            assert descendants, "the configured command must exercise descendant cleanup"
            raise RuntimeError("public client test failure")

    assert session.proc.poll() is not None, "the direct child was not waited for"
    deadline = time.monotonic() + 60
    wake = threading.Event()
    while any(identity_exists(identity) for identity in descendants):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        wake.wait(min(0.01, remaining))
    assert not any(identity_exists(identity) for identity in descendants), (
        "context exception left an owned command descendant behind"
    )


def test_context_exit_kills_and_reaps_a_sigterm_ignoring_direct_child():
    """Graceful teardown still forcibly reaps an uncooperative fixture command."""
    source = (
        "import json, signal\n"
        "signal.signal(signal.SIGTERM, signal.SIG_IGN)\n"
        "print(json.dumps({'ready': True}), flush=True)\n"
        "signal.pause()\n"
    )
    with LauncherSession(command=[sys.executable, "-c", source]) as session:
        assert session.read() == {"ready": True}
        identity = process_identity(session.proc.pid)
        assert identity is not None

    assert session.proc.returncode == -signal.SIGKILL
    assert not identity_exists(identity), "the forcibly stopped child was not reaped"
    assert all(stream.closed for stream in (
        session.proc.stdin, session.proc.stdout, session.proc.stderr
    ))
