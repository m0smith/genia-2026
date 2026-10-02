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
    REPO_ROOT,
    RUN_CAPABILITY_PATH,
    STDIN_MUX_PATH,
    pid_alive,
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


def _capability(argv, mux=None, **kwargs):
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
    facts = _facts(tmp_path)
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
    found = []
    for entry in Path("/proc").iterdir():
        if entry.name.isdigit():
            try:
                cmdline = (entry / "cmdline").read_bytes()
            except OSError:
                continue
            if b"fake_worker.py" in cmdline and pid_alive(int(entry.name)):
                found.append(int(entry.name))
    return found


def test_worker_children_die_with_the_worker(tmp_path):
    body = """
    import os, subprocess, sys, time
    sys.stdin.buffer.read()
    subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
    time.sleep(60)
    """
    before = set(_worker_processes_left())
    reply = json.loads(
        _capability(_script(tmp_path, body), deadline_ms=600)("1", lambda line: False)
    )
    assert reply == {"status": "timeout"}
    time.sleep(0.3)
    leaked = [
        e.name
        for e in Path("/proc").iterdir()
        if e.name.isdigit()
        and b"time.sleep(60)" in _read(e / "cmdline")
        and pid_alive(int(e.name))
    ]
    assert leaked == [], "worker descendants survived"


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


def test_cancel_line_arriving_mid_run_cancels_and_other_lines_are_preserved(tmp_path):
    mux, write_end = _pipe_mux()

    def later():
        time.sleep(0.8)
        os.write(write_end, b"other-1\nCANCEL\nother-2\n")

    threading.Thread(target=later, daemon=True).start()
    started = time.monotonic()
    reply = json.loads(
        _capability(_script(tmp_path, SLEEPER), mux)("1", lambda line: line == "CANCEL")
    )
    assert reply == {"status": "cancelled"}
    assert 0.7 <= time.monotonic() - started < 4
    assert list(mux.pending) == ["other-1", "other-2"]  # order preserved, cancel dropped
    assert not _worker_processes_left()


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
