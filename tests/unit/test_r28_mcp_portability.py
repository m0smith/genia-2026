"""R28 E28-6 (issue #707, ledger R28-H47): portability of the governed `genia_run` profile.

Authentic VS Code run 2 on macOS (Darwin) found discovery, negotiation, capabilities and parse working while
every `genia_run` returned `internal_error`: the worker failed in its bootstrap, before it read the source.
Pre-flight: docs/design/r28-e28-6-macos-execution-preflight.md. These tests (a) reproduce the production
signature on any host by simulating a platform whose kernel rejects `RLIMIT_AS`, (b) pin the fail-closed rule
for every other limit and for Linux, (c) prove the macOS process-inspection backend (`ps`, `lsof`) works, on
Linux too, so the lifecycle conformance suite is portable, and (d) keep the development diagnostic off the wire.
Python-host tests; they add no Genia semantics and no MCP behavior.
"""

from __future__ import annotations

import errno
import json
import os
import subprocess
import sys
import textwrap
import time
from pathlib import Path

import pytest

from tests.fixtures.r28_mcp_conformance import (
    _HOST_CODE,
    assert_closed_failure,
    assert_completed,
)
from tests.fixtures.r28_mcp_helpers import (
    REPO_ROOT,
    RUN_POLICY_MESSAGE,
    RUN_RUNTIME_MESSAGE,
    SERVER_PATH,
    LauncherSession,
    parse_request,
    repository_revision,
    run_request,
    server_env,
    structured,
)

pytestmark = pytest.mark.unit

PORTABLE_LIMITS = ("RLIMIT_FSIZE", "RLIMIT_CORE", "RLIMIT_CPU", "RLIMIT_NOFILE")

# A worker whose kernel rejects the named limits, on a stated platform. Everything else is the real worker.
REJECTING_WORKER = """
import errno, resource
import hosts.python.mcp_worker as worker

worker.PLATFORM = {platform!r}
rejected = {rejected!r}
real = resource.setrlimit


def setrlimit(which, limits):
    for name in rejected:
        if which == getattr(resource, name):
            {raiser}
    return real(which, limits)


resource.setrlimit = setrlimit
raise SystemExit(worker.main())
"""
VALUE_ERROR = 'raise ValueError("current limit exceeds maximum limit")'
OS_ERROR = "raise OSError(errno.EINVAL, 'Invalid argument')"


def _script(tmp_path, platform, rejected, raiser=VALUE_ERROR):
    path = tmp_path / "rejecting_worker.py"
    path.write_text(
        textwrap.dedent(REJECTING_WORKER.format(platform=platform, rejected=tuple(rejected), raiser=raiser)),
        encoding="utf-8",
    )
    return path


def _capability(script):
    from hosts.python.mcp_run_capability import RunCapability

    return RunCapability(worker_argv=[sys.executable, "-B", str(script)], handshake=True, isolated=False)


def _status(capability, source):
    return json.loads(capability(source, lambda line: False))


# --- (a) the production signature, reproduced --------------------------------------------------


@pytest.mark.parametrize("raiser", [VALUE_ERROR, OS_ERROR], ids=["ValueError", "OSError-EINVAL"])
def test_a_darwin_kernel_rejecting_the_address_space_bound_does_not_break_every_run(tmp_path, raiser):
    capability = _capability(_script(tmp_path, "darwin", ["RLIMIT_AS"], raiser))
    assert _status(capability, "1 + 2") == {"status": "completed", "value": "3", "stdout": "", "stderr": ""}
    assert _status(capability, "f(x) =")["status"] == "parse_error"
    assert _status(capability, 'read_file("/etc/hostname")') == {"status": "policy_denied"}
    assert _status(capability, "1 / 0") == {"status": "runtime_error"}
    assert _status(capability, 'print("o")\nwriteln(stderr, "e")\n1')["stdout"] == "o\n"


def test_the_same_rejection_on_linux_fails_closed_for_every_run(tmp_path):
    capability = _capability(_script(tmp_path, "linux", ["RLIMIT_AS"]))
    for source in ("1 + 2", "f(x) =", 'read_file("/etc/hostname")'):
        assert _status(capability, source) == {"status": "internal_error"}  # never run without the bound


@pytest.mark.parametrize("limit", PORTABLE_LIMITS)
@pytest.mark.parametrize("platform", ["darwin", "linux"])
def test_a_rejected_portable_limit_fails_closed_on_every_platform(tmp_path, platform, limit):
    capability = _capability(_script(tmp_path, platform, [limit], OS_ERROR))
    assert _status(capability, "1 + 2") == {"status": "internal_error"}


def test_a_rejected_address_space_bound_on_darwin_does_not_skip_the_portable_limits(tmp_path, monkeypatch):
    import hosts.python.mcp_worker as worker
    import resource

    applied = []

    def setrlimit(which, limits):
        if which == resource.RLIMIT_AS:
            raise OSError(errno.EINVAL, "Invalid argument")
        applied.append((which, limits))

    monkeypatch.setattr(worker, "PLATFORM", "darwin")
    monkeypatch.setattr(resource, "setrlimit", setrlimit)
    worker.apply_limits()
    assert (resource.RLIMIT_FSIZE, (0, 0)) in applied
    assert (resource.RLIMIT_CORE, (0, 0)) in applied
    assert (resource.RLIMIT_CPU, (worker.CPU_SECONDS, worker.CPU_SECONDS)) in applied
    assert (resource.RLIMIT_NOFILE, (worker.OPEN_FILES, worker.OPEN_FILES)) in applied


def test_linux_still_applies_the_address_space_bound_and_fails_if_it_cannot(monkeypatch):
    import hosts.python.mcp_worker as worker
    import resource

    seen = []

    def setrlimit(which, limits):
        seen.append(which)
        if which == resource.RLIMIT_AS:
            raise OSError(errno.EINVAL, "Invalid argument")

    monkeypatch.setattr(worker, "PLATFORM", "linux")
    monkeypatch.setattr(resource, "setrlimit", setrlimit)
    with pytest.raises(OSError):
        worker.apply_limits()
    assert resource.RLIMIT_AS in seen


def test_only_the_address_space_bound_is_tolerated_and_only_on_darwin():
    text = (REPO_ROOT / "hosts" / "python" / "mcp_worker.py").read_text(encoding="utf-8")
    assert text.count('"darwin"') == 1  # one platform decision, in limit application
    assert "RLIMIT_AS" in text and "except (ValueError, OSError)" in text


# --- the wire-level regression: discovery and parse work, so `genia_run` must too ---------------


def _session(tmp_path, platform):
    script = _script(tmp_path, platform, ["RLIMIT_AS"], OS_ERROR)
    return LauncherSession(
        command=[sys.executable, "-c", _HOST_CODE, str(SERVER_PATH), repository_revision(), str(script)],
        cwd=REPO_ROOT,
        env=server_env(),
    )


def test_discovery_and_parse_working_while_every_run_fails_cannot_recur_on_a_darwin_like_host(tmp_path):
    with _session(tmp_path, "darwin") as session:
        session.wait_ready()
        session.send({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})  # compat era without a handshake: -32602
        session.read(60)
        session.send(parse_request("f(x) = x + 1", 2))
        assert structured(session.read(60))[1]["status"] == "ok"
        session.send(run_request("6 * 7", 3))
        assert assert_completed(session.read(60))["value"]["rendered"] == "42"
        session.send(run_request('read_file("/etc/hostname")', 4))
        assert_closed_failure(session.read(60), "policy_denied", "policy", RUN_POLICY_MESSAGE)
        session.send(run_request("1 / 0", 5))
        assert_closed_failure(session.read(60), "runtime_error", "execution", RUN_RUNTIME_MESSAGE)


def test_the_same_host_on_linux_semantics_fails_closed_at_the_wire(tmp_path):
    with _session(tmp_path, "linux") as session:
        session.wait_ready()
        session.send(run_request("6 * 7", 1))
        envelope = structured(session.read(60))[1]
        assert envelope["error"] == {
            "kind": "internal_error",
            "message": "Internal error while executing",
            "phase": "adapter",
        }


# --- (d) the development diagnostic stays off the wire -----------------------------------------


def test_the_worker_names_an_internal_failure_on_its_own_stderr_only_when_asked(tmp_path):
    script = _script(tmp_path, "linux", ["RLIMIT_AS"], OS_ERROR)
    base = {"PYTHONPATH": os.pathsep.join([str(REPO_ROOT), str(REPO_ROOT / "src")]), "PYTHONUTF8": "1"}

    def run(extra):
        return subprocess.run([sys.executable, "-B", str(script)], input=b"1", capture_output=True,
                              env=base | extra, cwd=str(tmp_path), check=False)

    quiet, asked = run({}), run({"GENIA_MCP_WORKER_DIAG": "1"})
    assert b"GENIA-WORKER-DIAG" not in quiet.stderr
    assert b"GENIA-WORKER-DIAG OSError: errno=22" in asked.stderr
    assert quiet.stdout == asked.stdout == b'{"status": "internal_error"}\n'


def test_the_supervisor_never_forwards_the_diagnostic_switch_and_the_wire_stays_sanitized(tmp_path, monkeypatch):
    from hosts.python import mcp_run_capability as supervisor

    monkeypatch.setenv("GENIA_MCP_WORKER_DIAG", "1")
    assert "GENIA_MCP_WORKER_DIAG" not in supervisor._worker_environment()
    monkeypatch.setenv("PATH", os.environ.get("PATH", ""))
    with _session(tmp_path, "linux") as session:
        session.wait_ready()
        session.send(run_request("1 + 2", 1))
        response = session.read(60)
        raw = session.raw_stdout
    assert b"GENIA-WORKER-DIAG" not in raw and b"errno" not in raw and b"OSError" not in raw
    assert response["result"]["structuredContent"]["error"]["kind"] == "internal_error"


def test_the_probe_reproduces_the_production_path_and_localizes_a_failure():
    done = subprocess.run(
        [sys.executable, "tools/mcp_diagnostics/worker_probe.py"],
        cwd=str(REPO_ROOT), capture_output=True, text=True, timeout=120, check=False,
        env={**os.environ, "PYTHONPATH": os.pathsep.join([str(REPO_ROOT), str(REPO_ROOT / "src")])},
    )
    assert done.returncode == 0, done.stdout + done.stderr
    report = json.loads(done.stdout[: done.stdout.rindex("VERDICT")])
    assert done.stdout.strip().splitlines()[-1].startswith("VERDICT OK")
    assert set(report["limits"]) == {"RLIMIT_FSIZE", "RLIMIT_CORE", "RLIMIT_CPU", "RLIMIT_NOFILE", "RLIMIT_AS"}
    assert report["supervised_reply"].startswith('{"status": "completed"')
    assert {"sys.platform", "has_proc", "ps", "lsof"} <= set(report["platform"])


# --- (c) the portable process-inspection backend (macOS: `ps` and `lsof`; proven here too) ---------

BACKENDS = ["proc", "ps"]


@pytest.fixture(params=BACKENDS)
def backend(request, monkeypatch):
    if request.param == "proc" and not Path("/proc/self/stat").exists():
        pytest.skip("no /proc on this platform (the macOS backend is `ps`)")
    monkeypatch.setenv("GENIA_R28_PROCESS_BACKEND", request.param)
    return request.param


def _sleeper(cwd=None):
    return subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(60)"],
        cwd=cwd, start_new_session=True, stdin=subprocess.DEVNULL,
    )


def _wait(condition, timeout=30):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if condition():
            return True
        time.sleep(0.02)
    return condition()


def test_the_backend_sees_descendants_their_command_lines_and_identities(backend):
    from tests.fixtures import r28_mcp_helpers as h

    child = _sleeper()
    try:
        assert _wait(lambda: child.pid in h.process_children(os.getpid()))
        assert any("time.sleep(60)" in part for part in h._cmdline(child.pid))
        identity = h.process_identity(child.pid)
        assert identity is not None and identity[0] == child.pid and h.identity_exists(identity)
        assert h.pid_alive(child.pid)
    finally:
        child.kill()
        child.wait()
    assert not h.identity_exists(identity) and not h.pid_alive(child.pid)


def test_the_backend_counts_an_unreaped_zombie_as_alive(backend):
    from tests.fixtures import r28_mcp_helpers as h

    child = subprocess.Popen(["true"])
    time.sleep(0.3)  # `true` has exited; it stays a zombie until waited for
    assert h.pid_alive(child.pid), "a zombie must count as not reaped"
    child.wait()
    assert _wait(lambda: not h.pid_alive(child.pid))


def test_the_backend_reads_a_processs_working_directory(backend, tmp_path):
    from tests.fixtures import r28_mcp_helpers as h

    child = _sleeper(cwd=tmp_path)
    try:
        identity = h.process_identity(child.pid)
        assert _wait(lambda: h.worker_workdir(identity) is not None)
        assert Path(h.worker_workdir(identity)).resolve() == tmp_path.resolve()
    finally:
        child.kill()
        child.wait()


def test_the_backend_finds_the_governed_worker_of_a_live_session_and_proves_cleanup(backend):
    with LauncherSession() as session:
        session.wait_ready()
        session.send(run_request("sleep(60000)", 1))
        workers = session.wait_for_worker()
        assert workers and all(session.proc.pid != w[0] for w in workers)
        from tests.fixtures import r28_mcp_helpers as h

        assert all(h.identity_exists(w) for w in workers)
        session.proc.terminate()
        assert _wait(lambda: session.proc.poll() is not None and not any(h.identity_exists(w) for w in workers))


def test_the_backend_sees_no_listener_for_the_launcher_chain(backend):
    from tests.fixtures import r28_mcp_helpers as h

    with LauncherSession() as session:
        session.wait_ready()
        before = h.listening_inodes()
        for pid in h.process_children(session.proc.pid) | {session.proc.pid}:
            assert not (h.socket_inodes(pid) & before), f"process {pid} is listening"
        assert h.listening_inodes() <= before  # no listener appeared while the session ran


def test_the_default_backend_is_proc_where_it_exists_and_ps_otherwise(monkeypatch):
    from tests.fixtures import r28_mcp_helpers as h

    monkeypatch.delenv("GENIA_R28_PROCESS_BACKEND", raising=False)
    assert h.process_backend() == ("proc" if Path("/proc/self/stat").exists() else "ps")
    monkeypatch.setenv("GENIA_R28_PROCESS_BACKEND", "ps")
    assert h.process_backend() == "ps"


# --- Darwin worker discovery (ledger R28-H47 sub-finding): argv shapes `ps` reports on macOS -----------------

MAC_FRAMEWORK_PYTHON = (
    "/usr/local/Cellar/python@3.12/3.12.9/Frameworks/Python.framework/Versions/3.12/Resources/"
    "Python.app/Contents/MacOS/Python"
)


@pytest.mark.parametrize(
    "argv, governed",
    [
        (["/repo/.venv/bin/python3", "-B", "-m", "hosts.python.mcp_worker"], True),
        ([MAC_FRAMEWORK_PYTHON, "-B", "-m", "hosts.python.mcp_worker"], True),  # macOS: executable is `Python`
        (["/usr/bin/python3.12", "-B", "-m", "hosts.python.mcp_worker"], True),
        (["/usr/bin/unshare", "--user", "--net", "--", "python", "-B", "-m", "hosts.python.mcp_worker"], False),
        ([MAC_FRAMEWORK_PYTHON, "-c", "import time; time.sleep(60)"], False),
        ([MAC_FRAMEWORK_PYTHON, "-B", "-m", "hosts.python.mcp_host"], False),
        ([MAC_FRAMEWORK_PYTHON, "-B", "-m"], False),
        ([], False),
    ],
    ids=["venv-python3", "mac-framework-Python", "python3.12", "unshare-wrapper", "other-python", "host", "dangling-m", "empty"],
)
def test_the_governed_worker_is_recognized_by_its_command_line_on_every_platform(monkeypatch, argv, governed):
    from tests.fixtures import r28_mcp_helpers as h

    monkeypatch.setattr(h, "_cmdline", lambda pid: argv)
    assert h.is_governed_worker(1) is governed


def test_the_ps_backend_asks_for_untruncated_command_lines(monkeypatch):
    # macOS `ps` cuts a command to the terminal width unless given -ww; a long interpreter path would hide `-m ...`.
    from tests.fixtures import r28_mcp_helpers as h

    seen = []
    real_run = subprocess.run

    def spy(command, *args, **kwargs):
        seen.append(list(command))
        return real_run(command, *args, **kwargs)

    monkeypatch.setenv("GENIA_R28_PROCESS_BACKEND", "ps")
    monkeypatch.setattr(h.subprocess, "run", spy)
    h.process_snapshot()
    h.process_snapshot(os.getpid())
    assert seen and all(any(arg.startswith("-") and arg.endswith("ww") for arg in command) for command in seen), seen


def test_the_ps_backend_sees_a_long_command_line_in_full(monkeypatch):
    from tests.fixtures import r28_mcp_helpers as h

    monkeypatch.setenv("GENIA_R28_PROCESS_BACKEND", "ps")
    padding = "x" * 400
    child = subprocess.Popen([sys.executable, "-c", f"import time; time.sleep(60)  # {padding}", "-m", "hosts.python.mcp_worker"])
    try:
        assert _wait(lambda: any("hosts.python.mcp_worker" in part for part in h._cmdline(child.pid)))
    finally:
        child.kill()
        child.wait()


def test_the_process_probe_reports_how_this_platform_shows_the_governed_worker():
    done = subprocess.run(
        [sys.executable, "tools/mcp_diagnostics/process_probe.py"],
        cwd=str(REPO_ROOT), capture_output=True, text=True, timeout=180, check=False,
        env={**os.environ, "PYTHONPATH": os.pathsep.join([str(REPO_ROOT), str(REPO_ROOT / "src")])},
    )
    assert done.returncode == 0, done.stdout + done.stderr
    assert done.stdout.strip().splitlines()[-1].startswith("VERDICT OK"), done.stdout
    report = json.loads(done.stdout[: done.stdout.rindex("VERDICT")])
    assert report["governed_workers"] and report["worker_rows"]
    assert {"raw_ps_default", "raw_ps_ww", "parsed_argv", "is_governed_worker"} <= set(report["worker_rows"][0])


# --- macOS suite findings (ledger R28-H48): decoding, platform-injected environment, the namespace probe -------

STRICT_STDIO = {"PYTHONIOENCODING": "utf-8:strict", "PYTHONUTF8": "0"}  # a typical macOS UTF-8 locale's stdin


def test_the_launcher_path_decodes_invalid_utf8_the_same_whatever_the_locales_stdin_handler_is():
    from tests.fixtures.r28_mcp_helpers import encode, frames, request, run_launcher_raw, server_env

    done = run_launcher_raw([b"\xff\xfe", encode(request("tools/list", 1))], env=server_env(STRICT_STDIO))
    assert done.returncode == 0, done.stderr
    out = [json.loads(frame) for frame in frames(done.stdout)]
    assert out[0]["error"]["code"] == -32700 and "id" not in out[0]  # contract A2: a protocol parse error
    assert "result" in out[1] and out[1]["id"] == 1  # and the session keeps serving


def test_plain_file_mode_depends_on_the_locales_stdin_decoder_which_is_pinned_for_the_tests():
    from tests.fixtures.r28_mcp_helpers import encode, frames, request, run_raw, server_env

    lines = [b"\xff\xfe", encode(request("tools/list", 1))]
    strict = run_raw(lines, env=server_env(STRICT_STDIO))
    assert strict.returncode != 0 and b"codec can't decode" in strict.stderr  # the documented dev-mode limitation
    pinned = run_raw(lines)  # the default: UTF-8 mode, as in a C/POSIX locale
    assert pinned.returncode == 0
    assert json.loads(frames(pinned.stdout)[0])["error"]["code"] == -32700


def test_the_namespace_probe_runs_only_on_linux(monkeypatch):
    from hosts.python import mcp_run_capability as supervisor

    monkeypatch.setattr(supervisor, "_namespace_probe", None)
    monkeypatch.setattr(supervisor.shutil, "which", lambda name: "/usr/bin/unshare")
    monkeypatch.setattr(supervisor.sys, "platform", "darwin")
    assert supervisor.network_isolation_available() is False  # never probed, never claimed

