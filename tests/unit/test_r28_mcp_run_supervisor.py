"""R28 E28-3 (issue #704): the worker supervisor and the stdin line multiplexer.

Pinned to docs/design/r28-e28-3-genia-run-design.md §4.3-4.4 (ledger H26, H27).
The supervisor is exercised with small fake workers so process isolation, limits,
deadline, cancellation, and reaping are proven independently of Genia evaluation.
Expected to fail until E28-3 lands.
"""

from __future__ import annotations

import ast
import importlib
import json
import os
import sys
import textwrap
import threading
import time
from pathlib import Path

import pytest

from tests.fixtures.r28_mcp_helpers import (
    RUN_CAPABILITY_PATH,
    STDIN_MUX_PATH,
    pid_alive,
    process_children,
)

pytestmark = pytest.mark.unit


def _supervisor():
    assert RUN_CAPABILITY_PATH.is_file(), (
        "E28-3 not implemented: hosts/python/mcp_run_capability.py missing"
    )
    return importlib.import_module("hosts.python.mcp_run_capability")


def _mux_module():
    assert STDIN_MUX_PATH.is_file(), "E28-3 not implemented: hosts/python/mcp_stdin.py missing"
    return importlib.import_module("hosts.python.mcp_stdin")


def _script(tmp_path, body):
    path = tmp_path / "fake_worker.py"
    path.write_text(textwrap.dedent(body), encoding="utf-8")
    return [sys.executable, "-B", str(path)]


# Unit tests that are not about the deadline must not be exposed to it: a shared CI host can
# stall for seconds. The 5,000 ms profile value has its own tests (and `deadline_ms` is the
# constructor parameter they use); everything else gets a generous bound.
GENEROUS_DEADLINE_MS = 120_000


def _capability(argv, mux=None, **kwargs):
    kwargs.setdefault("deadline_ms", GENEROUS_DEADLINE_MS)
    # Unit tests of unrelated behavior do not create kernel namespaces (many parallel
    # create/destroy cycles can stall a shared host); namespace tests opt in explicitly.
    kwargs.setdefault("isolated", False)
    return _supervisor().RunCapability(mux, worker_argv=argv, **kwargs)


GOOD_REPLY = """
import json, sys
sys.stdin.buffer.read()
print(json.dumps({"status": "completed", "value": "1", "stdout": "", "stderr": ""}))
"""

FACTS = """
import json, os, sys
source = sys.stdin.buffer.read().decode("utf-8")
facts = {
    "env": sorted(os.environ),
    "cwd": os.getcwd(),
    "cwd_entries": os.listdir("."),
    "fds": sorted(int(n) for n in os.listdir("/proc/self/fd")),
    "argv": sys.argv[1:],
    "source": source,
    "pid": os.getpid(),
    "pgid_is_leader": os.getpgid(0) == os.getpid(),
    "net": [l.split(":")[0].strip() for l in open("/proc/net/dev").read().splitlines()[2:]],
}
print(json.dumps({"status": "completed", "value": json.dumps(facts), "stdout": "", "stderr": ""}))
"""


def _facts(tmp_path, source="SOURCE-TEXT", **kwargs):
    reply = json.loads(_capability(_script(tmp_path, FACTS), **kwargs)(source, lambda line: False))
    assert reply["status"] == "completed", reply
    return json.loads(reply["value"])


# --- worker process isolation floor ---------------------------------------------------------


def test_worker_gets_the_source_on_stdin_even_above_the_argv_limit(tmp_path):
    big = "x" * 262144  # larger than one argv element may be (ledger H06/H07)
    facts = _facts(tmp_path, source=big)
    assert facts["source"] == big and facts["argv"] == []


def test_worker_environment_is_a_fixed_minimal_allowlist(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", "/home/SENTINEL")
    monkeypatch.setenv("USER_SECRET_TOKEN", "SENTINEL")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "SENTINEL")
    facts = _facts(tmp_path)
    assert not {"HOME", "USER_SECRET_TOKEN", "AWS_SECRET_ACCESS_KEY", "PATH"} & set(facts["env"])
    assert set(facts["env"]) <= set(_supervisor().ENV_ALLOWLIST) | {"PYTHONPATH", "PYTHONUTF8",
                                                                   "PYTHONDONTWRITEBYTECODE",
                                                                   "LC_CTYPE", "PWD"}


def test_worker_runs_in_a_private_empty_directory_that_is_removed_afterwards(tmp_path):
    first, second = _facts(tmp_path), _facts(tmp_path)
    assert first["cwd_entries"] == [] and second["cwd_entries"] == []
    assert first["cwd"] != second["cwd"]
    assert Path(first["cwd"]).resolve().parent != Path(os.getcwd()).resolve()
    assert not Path(first["cwd"]).exists() and not Path(second["cwd"]).exists()


def test_worker_inherits_only_the_three_standard_streams(tmp_path):
    read_end, write_end = os.pipe()  # an unrelated descriptor the worker must not see
    try:
        facts = _facts(tmp_path)
    finally:
        os.close(read_end)
        os.close(write_end)
    assert facts["fds"][:3] == [0, 1, 2]
    assert len([fd for fd in facts["fds"] if fd > 2]) <= 1  # only the /proc listing fd itself


def test_each_call_is_a_fresh_process_in_its_own_process_group(tmp_path):
    first, second = _facts(tmp_path), _facts(tmp_path)
    assert first["pid"] != second["pid"]
    assert first["pgid_is_leader"] and second["pgid_is_leader"]
    assert not pid_alive(first["pid"]) and not pid_alive(second["pid"])


def test_network_namespace_is_used_only_when_verified_and_then_isolates(tmp_path):
    supervisor = _supervisor()
    available = supervisor.network_isolation_available()
    assert isinstance(available, bool)
    facts = _facts(tmp_path, isolated=None)  # None: use the verified-probe result
    if available:
        assert facts["net"] == ["lo"], facts["net"]
    else:
        pytest.skip("user+network namespaces unavailable here (best effort, not claimed)")


def test_namespace_wrapper_is_not_used_when_the_probe_fails(tmp_path, monkeypatch):
    supervisor = _supervisor()
    monkeypatch.setattr(supervisor, "network_isolation_available", lambda: False)
    command = supervisor.worker_command([sys.executable, "-B", "worker.py"])
    assert "unshare" not in " ".join(command) and command[-1] == "worker.py"


def test_default_deadline_is_the_fixed_5000_ms_profile_value():
    assert _supervisor().DEADLINE_MS == 5000


# --- reply validation ------------------------------------------------------------------------


def test_good_reply_is_returned_verbatim_as_one_line(tmp_path):
    text = _capability(_script(tmp_path, GOOD_REPLY))("1", lambda line: False)
    assert json.loads(text) == {"status": "completed", "value": "1", "stdout": "", "stderr": ""}
    assert "\n" not in text


@pytest.mark.parametrize(
    "body",
    [
        "import sys; sys.exit(3)",
        "import sys; sys.stdin.buffer.read(); print('not json at all')",
        "import sys; sys.stdin.buffer.read(); print('{}'); print('{}')",
        "import sys; sys.stdin.buffer.read(); sys.stdout.buffer.write(b'{\"status\": \"completed\", \"value\": \"\\xff\"}\\n')",
        "import sys; sys.stdin.buffer.read(); print('{\"status\": \"unknown_status\"}')",
        "import sys; sys.stdin.buffer.read()",
    ],
    ids=["crash", "garbage", "two-lines", "non-ascii", "unknown-status", "empty"],
)
def test_unusable_worker_output_is_internal_error(tmp_path, body):
    reply = json.loads(_capability(_script(tmp_path, body))("1", lambda line: False))
    assert reply == {"status": "internal_error"}


def test_worker_stderr_is_discarded_and_never_forwarded(tmp_path):
    body = """
    import json, sys
    sys.stdin.buffer.read()
    sys.stderr.write("SECRET-STDERR-LEAK" * 100000)
    print(json.dumps({"status": "completed", "value": "1", "stdout": "", "stderr": ""}))
    """
    text = _capability(_script(tmp_path, body))("1", lambda line: False)
    assert "SECRET-STDERR-LEAK" not in text and json.loads(text)["status"] == "completed"


def test_oversized_reply_is_killed_and_internal_error(tmp_path):
    body = """
    import sys
    sys.stdin.buffer.read()
    chunk = b"x" * 65536
    while True:
        sys.stdout.buffer.write(chunk)
    """
    started = time.monotonic()
    reply = json.loads(_capability(_script(tmp_path, body))("1", lambda line: False))
    assert reply == {"status": "internal_error"}
    assert time.monotonic() - started < 4.5


def test_a_worker_that_never_reads_stdin_does_not_hang_or_spin(tmp_path):
    big = "x" * 262144
    started = time.monotonic()
    reply = json.loads(
        _capability(_script(tmp_path, "import sys; sys.exit(0)"))(big, lambda line: False)
    )
    assert reply == {"status": "internal_error"}
    assert time.monotonic() - started < 3


# --- isolation profile is determined at initialization, not in a request (ledger R28-H33) ---


@pytest.fixture
def fresh_probe(monkeypatch):
    """A clean probe cache with a counting stand-in for the real probe."""
    supervisor = _supervisor()
    calls = []

    def counting_probe():
        calls.append(time.monotonic())
        return True

    monkeypatch.setattr(supervisor, "_namespace_probe", None)
    monkeypatch.setattr(supervisor, "_run_probe", counting_probe)
    return supervisor, calls


def test_probe_runs_once_at_construction_and_never_in_the_request_path(tmp_path, fresh_probe):
    supervisor, calls = fresh_probe
    capability = supervisor.RunCapability(
        None, worker_argv=_script(tmp_path, GOOD_REPLY), deadline_ms=GENEROUS_DEADLINE_MS
    )
    assert len(calls) == 1  # determined during initialization, before any request
    assert capability.isolation_profile == {"network_namespace": True}
    # Requests consume the cached profile. The stand-in claims a namespace the host may not
    # have, so run the requests with the real cached answer replaced by "unavailable".
    capability._isolated = False
    for _ in range(3):
        assert json.loads(capability("1", lambda line: False))["status"] == "completed"
    assert len(calls) == 1


def test_a_request_never_triggers_the_probe_even_if_the_cache_is_cold(tmp_path, monkeypatch):
    supervisor = _supervisor()
    capability = supervisor.RunCapability(
        None, worker_argv=_script(tmp_path, GOOD_REPLY), deadline_ms=GENEROUS_DEADLINE_MS
    )
    monkeypatch.setattr(supervisor, "_namespace_probe", None)  # as if never determined
    monkeypatch.setattr(
        supervisor, "_run_probe", lambda: pytest.fail("probe ran inside a request")
    )
    assert json.loads(capability("1", lambda line: False))["status"] == "completed"


def test_probe_timeout_is_bounded_and_means_unavailable_not_an_error(monkeypatch):
    import subprocess as sp

    supervisor = _supervisor()
    assert supervisor.PROBE_TIMEOUT_S <= 5
    monkeypatch.setattr(supervisor, "_namespace_probe", None)
    monkeypatch.setattr(supervisor.shutil, "which", lambda name: "/usr/bin/unshare")
    seen = {}

    def hanging_run(command, **kwargs):
        seen["timeout"] = kwargs.get("timeout")
        raise sp.TimeoutExpired(command, kwargs.get("timeout"))

    monkeypatch.setattr(supervisor.subprocess, "run", hanging_run)
    assert supervisor.network_isolation_available() is False
    assert seen["timeout"] == supervisor.PROBE_TIMEOUT_S


def test_failed_probe_leaves_requests_working_without_a_namespace(tmp_path, monkeypatch):
    supervisor = _supervisor()
    monkeypatch.setattr(supervisor, "_namespace_probe", None)
    monkeypatch.setattr(supervisor, "_run_probe", lambda: False)
    capability = supervisor.RunCapability(
        None, worker_argv=_script(tmp_path, FACTS), deadline_ms=GENEROUS_DEADLINE_MS
    )
    assert capability.isolation_profile == {"network_namespace": False}
    reply = json.loads(capability("x", lambda line: False))
    assert reply["status"] == "completed"  # requests still work, just unwrapped
    # Honest reporting: no wrapper is used and none is claimed.
    assert "unshare" not in " ".join(supervisor.worker_command(["w"], capability._isolated))


def test_request_time_does_not_include_any_probe_work(tmp_path, fresh_probe):
    supervisor, calls = fresh_probe
    capability = supervisor.RunCapability(
        None, worker_argv=_script(tmp_path, GOOD_REPLY), deadline_ms=GENEROUS_DEADLINE_MS
    )
    capability._isolated = False
    before = len(calls)
    started = time.monotonic()
    capability("1", lambda line: False)
    assert len(calls) == before
    assert time.monotonic() - started < supervisor.DEADLINE_MS / 1000.0


# --- the execution deadline starts at worker readiness, not at spawn (ledger R28-H34) ---

READY = 'import sys; sys.stderr.write("GENIA-WORKER-READY\\n"); sys.stderr.flush()'


def _handshake_script(tmp_path, before_ready, after_ready):
    body = f"""
import sys, time
{before_ready}
{READY}
{after_ready}
"""
    return _script(tmp_path, body)


def test_ready_marker_is_the_same_in_worker_and_supervisor():
    worker = importlib.import_module("hosts.python.mcp_worker")
    assert worker.READY_MARKER == _supervisor().READY_MARKER
    assert _supervisor().STARTUP_LIMIT_MS >= 10_000  # generous: only guards a worker that never starts


def test_slow_bootstrap_is_not_charged_against_the_execution_deadline(tmp_path):
    # Bootstrap takes longer (1.2 s) than the whole execution deadline (0.6 s) and the run
    # still completes: process launch is not part of parse/policy/evaluation/render.
    script = _handshake_script(
        tmp_path,
        "time.sleep(1.2)",
        'import json; sys.stdin.buffer.read(); print(json.dumps({"status": "completed", "value": "1", "stdout": "", "stderr": ""}))',
    )
    capability = _supervisor().RunCapability(None, worker_argv=script, deadline_ms=600, handshake=True)
    assert json.loads(capability("1", lambda line: False))["status"] == "completed"


def test_deadline_is_measured_from_readiness_not_from_spawn(tmp_path):
    script = _handshake_script(tmp_path, "time.sleep(0.8)", "time.sleep(60)")
    capability = _supervisor().RunCapability(None, worker_argv=script, deadline_ms=600, handshake=True)
    started = time.monotonic()
    assert json.loads(capability("1", lambda line: False)) == {"status": "timeout"}
    # >= bootstrap (0.8 s) + deadline (0.6 s): the clock did not start at spawn.
    assert time.monotonic() - started >= 1.3
    assert not _worker_processes_left()


def test_without_a_handshake_the_deadline_still_runs_from_spawn(tmp_path):
    started = time.monotonic()
    reply = json.loads(
        _capability(_script(tmp_path, SLEEPER), deadline_ms=600, handshake=False)("1", lambda line: False)
    )
    assert reply == {"status": "timeout"} and time.monotonic() - started < 3


def test_worker_that_never_becomes_ready_is_internal_error_after_the_startup_limit(tmp_path):
    script = _script(tmp_path, SLEEPER)  # never writes the marker
    capability = _supervisor().RunCapability(
        None, worker_argv=script, deadline_ms=GENEROUS_DEADLINE_MS, startup_ms=700, handshake=True
    )
    started = time.monotonic()
    assert json.loads(capability("1", lambda line: False)) == {"status": "internal_error"}
    assert 0.6 <= time.monotonic() - started < 5
    assert not _worker_processes_left()


def test_marker_after_other_stderr_noise_is_still_recognized(tmp_path):
    script = _handshake_script(
        tmp_path,
        'sys.stderr.write("some interpreter warning\\n" * 100); sys.stderr.flush()',
        'import json; sys.stdin.buffer.read(); print(json.dumps({"status": "completed", "value": "1", "stdout": "", "stderr": ""}))',
    )
    capability = _supervisor().RunCapability(None, worker_argv=script, deadline_ms=2000, handshake=True)
    assert json.loads(capability("1", lambda line: False))["status"] == "completed"


def test_cancel_during_bootstrap_cancels_and_reaps(tmp_path):
    mux, write_end = _pipe_mux()
    marker = tmp_path / "bootstrapping"
    body = """
import sys, time
marker = sys.stdin.buffer.read().decode("utf-8")
open(marker, "w").close()  # observable: the worker exists but has not reported ready
time.sleep(60)
"""
    threading.Thread(
        target=lambda: (_wait_for(marker), os.write(write_end, b"CANCEL\n")), daemon=True
    ).start()
    capability = _supervisor().RunCapability(
        mux, worker_argv=_script(tmp_path, body), deadline_ms=GENEROUS_DEADLINE_MS, handshake=True
    )
    reply = json.loads(capability(str(marker), lambda line: line == "CANCEL"))
    assert reply == {"status": "cancelled"} and marker.exists()
    assert not _worker_processes_left()


def test_the_real_worker_reports_readiness_and_completes():
    capability = _supervisor().RunCapability(None, deadline_ms=GENEROUS_DEADLINE_MS)
    assert capability._handshake is True  # the default worker is the handshaking one
    reply = json.loads(capability("1 + 2", lambda line: False))
    assert reply == {"status": "completed", "value": "3", "stdout": "", "stderr": ""}


# --- deadline and reaping --------------------------------------------------------------------

SLEEPER = """
import os, sys, time
sys.stdin.buffer.read()
time.sleep(60)
"""


def test_deadline_returns_timeout_and_reaps_the_worker(tmp_path):
    started = time.monotonic()
    reply = json.loads(
        _capability(_script(tmp_path, SLEEPER), deadline_ms=600)("1", lambda line: False)
    )
    assert reply == {"status": "timeout"}
    assert 0.5 <= time.monotonic() - started < 3
    assert not _worker_processes_left()


def _worker_processes_left():
    """Live fake workers that are descendants of *this* process (xdist-safe)."""
    found = []
    for pid in process_children(os.getpid()):
        if b"fake_worker.py" in _read(Path(f"/proc/{pid}/cmdline")) and pid_alive(pid):
            found.append(pid)
    return found


@pytest.mark.parametrize("isolated", [False, True], ids=["plain", "namespace"])
def test_worker_children_die_with_the_worker(tmp_path, isolated):
    supervisor = _supervisor()
    if isolated and not supervisor.network_isolation_available():
        pytest.skip("namespace not verified on this host (best effort, not claimed)")
    body = """
    import os, subprocess, sys, time
    sys.stdin.buffer.read()
    subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
    time.sleep(60)
    """
    capability = _capability(_script(tmp_path, body), deadline_ms=600, isolated=isolated)
    reply = json.loads(capability("1", lambda line: False))
    assert reply == {"status": "timeout"}
    # The group kill and reap finished before the reply: nothing may remain, not even a zombie.
    leaked = [
        pid
        for pid in process_children(os.getpid())
        if b"time.sleep(60)" in _read(Path(f"/proc/{pid}/cmdline")) and pid_alive(pid)
    ]
    assert leaked == [], "worker descendants survived"


def test_strict_reap_check_sees_an_unreaped_zombie():
    # The reap assertions are only meaningful if an unreaped child is detected as alive.
    import subprocess

    child = subprocess.Popen(["true"])
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        fields = Path(f"/proc/{child.pid}/stat").read_text().rsplit(")", 1)[1].split()
        if fields[0] == "Z":
            break
        time.sleep(0.01)
    assert pid_alive(child.pid), "a zombie must count as not reaped"
    child.wait()
    assert not pid_alive(child.pid)


def _read(path):
    try:
        return path.read_bytes()
    except OSError:
        return b""


# --- cancellation through the multiplexer -------------------------------------------------


def _pipe_mux():
    mux_module = _mux_module()
    read_end, write_end = os.pipe()
    return mux_module.LineMux(read_end), write_end


def test_cancel_line_already_queued_with_the_request_cancels(tmp_path):
    mux, write_end = _pipe_mux()
    os.write(write_end, b"CANCEL\nnext\n")
    mux.pump(1)
    started = time.monotonic()
    reply = json.loads(
        _capability(_script(tmp_path, SLEEPER), mux)("1", lambda line: line == "CANCEL")
    )
    assert reply == {"status": "cancelled"}
    assert time.monotonic() - started < 3
    assert list(mux.pending) == ["next"]  # the cancel line is consumed, the rest stays
    assert not _worker_processes_left()


MARKER_WORKER = """
import os, sys, time
marker = sys.stdin.buffer.read().decode("utf-8")
{pre}
open(marker, "w").close()  # observable: the worker is running its program
time.sleep(60)
"""


def _wait_for(path, timeout=60):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if path.exists():
            return
        time.sleep(0.01)
    raise AssertionError(f"{path} never appeared")


def test_cancel_line_arriving_mid_run_cancels_and_other_lines_are_preserved(tmp_path):
    mux, write_end = _pipe_mux()
    marker = tmp_path / "running"
    body = MARKER_WORKER.format(pre="")

    def after_worker_is_running():
        _wait_for(marker)  # an observable condition, not a fixed sleep
        os.write(write_end, b"other-1\nCANCEL\nother-2\n")

    threading.Thread(target=after_worker_is_running, daemon=True).start()
    reply = json.loads(
        _capability(_script(tmp_path, body), mux)(str(marker), lambda line: line == "CANCEL")
    )
    assert reply == {"status": "cancelled"}
    assert marker.exists()  # it really was cancelled mid-run, not before it started
    assert list(mux.pending) == ["other-1", "other-2"]  # order preserved, cancel dropped
    assert not _worker_processes_left()


def test_cancel_mid_reply_returns_only_the_fixed_cancelled_reply(tmp_path):
    # The worker has already written a partial completed reply when the cancel arrives.
    mux, write_end = _pipe_mux()
    marker = tmp_path / "running"
    pre = (
        "sys.stdout.write('{\"status\": \"completed\", \"value\": \"partial-out\"')\n"
        "sys.stdout.flush()"
    )
    body = MARKER_WORKER.format(pre=pre)
    threading.Thread(
        target=lambda: (_wait_for(marker), os.write(write_end, b"CANCEL\n")), daemon=True
    ).start()
    text = _capability(_script(tmp_path, body), mux)(str(marker), lambda line: line == "CANCEL")
    assert json.loads(text) == {"status": "cancelled"} and "partial-out" not in text


def test_deadline_with_partial_output_is_only_the_fixed_timeout_reply(tmp_path):
    body = MARKER_WORKER.format(
        pre="sys.stdout.write('{\"status\": \"completed\", \"value\": \"partial-out\"')\nsys.stdout.flush()"
    )
    marker = tmp_path / "running"
    text = _capability(_script(tmp_path, body), deadline_ms=1500)(str(marker), lambda line: False)
    assert json.loads(text) == {"status": "timeout"} and "partial-out" not in text


def test_non_matching_lines_do_not_cancel(tmp_path):
    mux, write_end = _pipe_mux()
    os.write(write_end, b"hello\n")
    reply = json.loads(
        _capability(_script(tmp_path, GOOD_REPLY), mux)("1", lambda line: False)
    )
    assert reply["status"] == "completed" and list(mux.pending) == ["hello"]


def test_finished_worker_result_wins_over_a_later_cancel(tmp_path):
    mux, write_end = _pipe_mux()
    reply = json.loads(
        _capability(_script(tmp_path, GOOD_REPLY), mux)("1", lambda line: line == "CANCEL")
    )
    os.write(write_end, b"CANCEL\n")  # arrives after the terminal state was recorded
    mux.pump(1)
    assert reply["status"] == "completed"


def test_a_raising_predicate_is_not_a_cancel(tmp_path):
    mux, write_end = _pipe_mux()
    os.write(write_end, b"x\n")

    def boom(line):
        raise RuntimeError("predicate failure")

    reply = json.loads(_capability(_script(tmp_path, GOOD_REPLY), mux)("1", boom))
    assert reply["status"] == "completed"


def test_eof_during_a_run_lets_the_run_finish(tmp_path):
    mux, write_end = _pipe_mux()
    os.close(write_end)
    reply = json.loads(_capability(_script(tmp_path, GOOD_REPLY), mux)("1", lambda line: False))
    assert reply["status"] == "completed"


# --- the line multiplexer --------------------------------------------------------------------


def test_mux_splits_on_newline_only_and_keeps_other_separators_inside_lines():
    mux, write_end = _pipe_mux()
    os.write(write_end, "a\u2028b\rc\x00d\n".encode("utf-8") + b"\xff\xfe-bad\nlast")
    os.close(write_end)
    lines = list(mux.provider())
    assert lines[0] == "a\u2028b\rc\x00d"
    assert lines[1].endswith("-bad")  # invalid UTF-8 survives (surrogateescape) like sys.stdin
    assert lines[2] == "last"  # an unterminated final line is still delivered at EOF


def test_mux_delivers_partial_lines_across_reads_and_ends_at_eof():
    mux, write_end = _pipe_mux()
    got = []
    consumer = threading.Thread(target=lambda: got.extend(mux.provider()))
    consumer.start()
    os.write(write_end, b"par")
    time.sleep(0.1)
    os.write(write_end, b"tial\nsecond\n")
    time.sleep(0.1)
    os.close(write_end)
    consumer.join(timeout=5)
    assert got == ["partial", "second"] and not consumer.is_alive()


def test_mux_applies_back_pressure_instead_of_unbounded_buffering():
    mux_module = _mux_module()
    mux, write_end = _pipe_mux()
    assert mux_module.MAX_PENDING_BYTES == 8 * 1024 * 1024
    line = b"x" * 65535 + b"\n"
    written = 0
    os.set_blocking(write_end, False)
    try:
        for _ in range(400):  # 400 * 64 KiB = 25 MiB offered
            try:
                os.write(write_end, line)
                written += len(line)
            except BlockingIOError:
                pass
            mux.pump(0)
    finally:
        os.close(write_end)
    assert mux.pending_bytes <= mux_module.MAX_PENDING_BYTES + 65536


# --- host module hygiene (architecture) ---------------------------------------------------


def _imports(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            names.add(node.module.split(".")[0])
    return names


def test_multiplexer_does_no_protocol_work_and_imports_only_system_modules():
    assert STDIN_MUX_PATH.is_file(), "E28-3 not implemented"
    assert _imports(STDIN_MUX_PATH) <= {"__future__", "collections", "os", "select"}


def test_supervisor_never_interprets_the_reply_as_protocol():
    assert RUN_CAPABILITY_PATH.is_file(), "E28-3 not implemented"
    imports = _imports(RUN_CAPABILITY_PATH)
    assert imports <= {"__future__", "collections", "os", "re", "select", "shutil", "signal",
                       "subprocess", "sys", "tempfile", "time", "pathlib", "hosts"}, imports
    assert "json" not in imports  # it checks reply shape only; native Genia decodes it
