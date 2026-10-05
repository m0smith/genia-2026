"""Shared harness for the R28 E28-1 native Genia MCP skeleton tests.

The harness speaks raw newline-delimited JSON-RPC (MCP 2026-07-28 stdio) to the
native ``apps/mcp/mcp.genia`` program started by the ordinary Genia CLI. It
contains no MCP application logic: it builds requests, runs the server, and
splits stdout on ``\\n`` only (never ``str.splitlines``, which also splits on
U+2028/U+2029 and would mask a framing defect).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from functools import lru_cache
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SERVER_PATH = REPO_ROOT / "apps" / "mcp" / "mcp.genia"
LAUNCHER_PATH = REPO_ROOT / "hosts" / "python" / "mcp_launch.py"

GENIA_MAIN = "from genia.interpreter import _main; raise SystemExit(_main())"

REVISION = "0123456789abcdef0123456789abcdef01234567"
OTHER_REVISION = "fedcba9876543210fedcba9876543210fedcba98"

PROTOCOL_VERSION = "2026-07-28"
META_VERSION = "io.modelcontextprotocol/protocolVersion"
META_CAPABILITIES = "io.modelcontextprotocol/clientCapabilities"
META_CLIENT_INFO = "io.modelcontextprotocol/clientInfo"
META_SERVER_INFO = "io.modelcontextprotocol/serverInfo"


def good_meta(**extra):
    meta = {META_VERSION: PROTOCOL_VERSION, META_CAPABILITIES: {}}
    meta.update(extra)
    return meta


def request(method, req_id=1, params=None, *, meta=True):
    """Build one JSON-RPC request object (per-request ``_meta`` by default)."""
    body = dict(params or {})
    if meta is True:
        body["_meta"] = good_meta()
    elif meta is not False:
        body["_meta"] = meta
    return {"jsonrpc": "2.0", "id": req_id, "method": method, "params": body}


def notification(method, params=None):
    message = {"jsonrpc": "2.0", "method": method}
    if params is not None:
        message["params"] = params
    return message


def encode(message, *, ensure_ascii=True) -> bytes:
    return json.dumps(message, ensure_ascii=ensure_ascii, separators=(",", ":")).encode("utf-8")


def server_env(extra=None):
    env = dict(os.environ)
    src = str(REPO_ROOT / "src")
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = src if not existing else os.pathsep.join([src, existing])
    if os.environ.get(DENY_NAMESPACE_SWITCH) == "1":
        # E28-5: run the whole R28 suite as on a host that forbids unprivileged namespaces.
        env["PATH"] = denied_namespace_path(env.get("PATH", ""))
    env.update(extra or {})
    return env


# --- E28-5: simulating a host that denies unprivileged namespaces ------------------------

DENY_NAMESPACE_SWITCH = "GENIA_R28_TEST_DENY_NAMESPACE"
_DENIED_UNSHARE_DIR = []


def denied_namespace_path(path: str) -> str:
    """`path` with a fake `unshare` first that always fails like a hardened CI host.

    The server must then degrade honestly (workers run without the namespace) and every
    policy and runtime layer must still hold: the namespace is defense in depth, never the
    security contract (E28-3 design section 5).
    """
    import atexit
    import shutil
    import stat
    import tempfile

    if not _DENIED_UNSHARE_DIR:
        directory = Path(tempfile.mkdtemp(prefix="genia-r28-denied-ns-"))
        script = directory / "unshare"
        script.write_text(
            "#!/bin/sh\necho 'unshare: unshare failed: Operation not permitted' >&2\nexit 1\n"
        )
        script.chmod(script.stat().st_mode | stat.S_IEXEC)
        _DENIED_UNSHARE_DIR.append(directory)
        atexit.register(shutil.rmtree, directory, True)
    return os.pathsep.join([str(_DENIED_UNSHARE_DIR[0]), path])


def server_command(args):
    assert SERVER_PATH.is_file(), (
        "E28-1 not implemented: apps/mcp/mcp.genia does not exist "
        "(native Genia MCP server expected at this path)"
    )
    # Same invocation as hosts/python/exec_cli.py (`-m genia.interpreter` would emit
    # a runpy RuntimeWarning on stderr, which must stay free of protocol noise).
    return [sys.executable, "-c", GENIA_MAIN, str(SERVER_PATH), *args]


def run_raw(lines, *, args=(REVISION,), cwd=None, env=None, timeout=60):
    """Run the server directly (no launcher) with raw byte lines on stdin."""
    stdin = b"".join(line + b"\n" for line in lines)
    return subprocess.run(
        server_command(list(args)),
        input=stdin,
        capture_output=True,
        cwd=str(cwd) if cwd else str(REPO_ROOT),
        env=env if env is not None else server_env(),
        timeout=timeout,
    )


def run_messages(messages, **kwargs):
    return run_raw([encode(m) for m in messages], **kwargs)


def frames(stdout: bytes):
    """Split stdout into protocol frames on newline only."""
    assert stdout == b"" or stdout.endswith(b"\n"), "last frame not newline-terminated"
    if stdout == b"":
        return []
    return stdout[:-1].split(b"\n")


def responses(completed):
    assert completed.returncode == 0, completed.stderr.decode("utf-8", "replace")
    decoded = []
    for frame in frames(completed.stdout):
        assert frame != b"", "empty protocol line on stdout"
        decoded.append(json.loads(frame.decode("utf-8")))
    return decoded


def call(message, **kwargs):
    """Send one request, return its single decoded response."""
    out = responses(run_messages([message], **kwargs))
    assert len(out) == 1, out
    return out[0]


@lru_cache(maxsize=None)
def _cached(key):
    kind, payload = key
    message = json.loads(payload)
    return call(message)


def cached_call(message):
    return _cached(("call", json.dumps(message, sort_keys=True)))


def expected_capabilities(revision=REVISION, tools=("genia_capabilities",)):
    return {
        "server": {"name": "genia-mcp", "contract": "genia.mcp.v1"},
        "mcp": {"protocol_version": PROTOCOL_VERSION, "transport": "stdio"},
        "genia": {
            "host": "python-reference",
            "contract_revision": revision,
            "portable_mcp_implementation": False,
        },
        "tools": list(tools),
        "execution_profile": {
            "name": "source-only-isolated-v1",
            "source_max_bytes": 262144,
            "timeout_ms": 5000,
            "stdout_max_bytes": 1048576,
            "stderr_max_bytes": 1048576,
            "value_max_bytes": 1048576,
            "diagnostic_max_bytes": 65536,
            "filesystem": False,
            "environment": False,
            "configuration": False,
            "secrets": False,
            "network": False,
        },
    }


def expected_envelope(revision=REVISION, tools=("genia_capabilities",)):
    return {
        "schema_version": "genia.mcp.v1",
        "status": "ok",
        "result": expected_capabilities(revision, tools),
        "error": None,
    }


FIXED_MESSAGES = {
    -32700: "Parse error",
    -32600: "Invalid request",
    -32601: "Method not found",
    -32602: "Invalid params",
    -32022: "Unsupported protocol version",
}
UNKNOWN_TOOL_MESSAGE = "Unknown tool"


def assert_protocol_error(response, code, *, req_id=..., message=None, data=None):
    """Assert a verified 2026-07-28 JSON-RPC error response shape."""
    assert response["jsonrpc"] == "2.0"
    assert "result" not in response
    if req_id is ...:
        pass
    elif req_id is None:
        assert "id" not in response, response
    else:
        assert response["id"] == req_id
        assert type(response["id"]) is type(req_id)
    error = response["error"]
    assert type(error["code"]) is int and error["code"] == code
    assert error["message"] == (message or FIXED_MESSAGES[code])
    if data is None:
        assert set(error) == {"code", "message"}, error
    else:
        assert set(error) == {"code", "message", "data"}, error
        assert error["data"] == data


# --- E28-2: launcher mode (host provisions the parse capability) -------------

PARSE_TOOLS = ("genia_capabilities", "genia_parse")
CAPABILITY_PATH = REPO_ROOT / "hosts" / "python" / "mcp_parse_capability.py"
HOST_BOOTSTRAP_PATH = REPO_ROOT / "hosts" / "python" / "mcp_host.py"


def repository_revision() -> str:
    done = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=True,
    )
    return done.stdout.strip()


def run_launcher_raw(lines, *, timeout=120, env=None):
    """Run the server through the host launcher (parse capability provisioned)."""
    assert HOST_BOOTSTRAP_PATH.is_file(), (
        "E28-2 not implemented: hosts/python/mcp_host.py does not exist"
    )
    stdin = b"".join(line + b"\n" for line in lines)
    return subprocess.run(
        [sys.executable, "-m", "hosts.python.mcp_launch"],
        input=stdin,
        capture_output=True,
        cwd=str(REPO_ROOT),
        env=env if env is not None else server_env(),
        timeout=timeout,
    )


def launcher_call(message, **kwargs):
    out = responses(run_launcher_raw([encode(message)], **kwargs))
    assert len(out) == 1, out
    return out[0]


def parse_request(source, req_id=1, **extra_arguments):
    arguments = {"source": source}
    arguments.update(extra_arguments)
    return request("tools/call", req_id, {"name": "genia_parse", "arguments": arguments})


def error_envelope(kind, phase, message):
    return {
        "schema_version": "genia.mcp.v1",
        "status": "error",
        "result": None,
        "error": {"kind": kind, "message": message, "phase": phase},
    }


# --- E28-3: genia_run over the launcher (host provisions parse and run) ---------

RUN_TOOLS = ("genia_capabilities", "genia_parse", "genia_run")
RUN_CAPABILITY_PATH = REPO_ROOT / "hosts" / "python" / "mcp_run_capability.py"
STDIN_MUX_PATH = REPO_ROOT / "hosts" / "python" / "mcp_stdin.py"
WORKER_PATH = REPO_ROOT / "hosts" / "python" / "mcp_worker.py"
WORKER_PROFILE_PATH = REPO_ROOT / "hosts" / "python" / "mcp_worker_profile.py"

RUN_POLICY_MESSAGE = "source requests a capability unavailable in the MCP v1 profile"
RUN_RUNTIME_MESSAGE = "Genia source failed during evaluation"
RUN_TIMEOUT_MESSAGE = "Execution exceeded the 5000 ms limit"
RUN_CANCELLED_MESSAGE = "Execution was cancelled"
RUN_CHANNEL_LIMIT_MESSAGE = "Result exceeds a 1048576-byte channel limit"
RUN_INTERNAL_MESSAGE = "Internal error while executing"


def run_request(source, req_id=1, **extra_arguments):
    arguments = {"source": source}
    arguments.update(extra_arguments)
    return request("tools/call", req_id, {"name": "genia_run", "arguments": arguments})


def cancel_notification(request_id, reason="client cancelled"):
    return notification(
        "notifications/cancelled", {"requestId": request_id, "reason": reason}
    )


def completed_envelope(rendered, stdout="", stderr=""):
    return {
        "schema_version": "genia.mcp.v1",
        "status": "ok",
        "result": {
            "kind": "completed",
            "value": {"rendered": rendered},
            "stdout": stdout,
            "stderr": stderr,
            "exit_code": 0,
        },
        "error": None,
    }


def structured(response):
    """Return (CallToolResult, envelope) after checking the common wire shape."""
    assert set(response) == {"jsonrpc", "id", "result"}, response
    result = response["result"]
    assert result["resultType"] == "complete"
    (item,) = result["content"]
    assert item["type"] == "text" and "\n" not in item["text"]
    assert json.loads(item["text"]) == result["structuredContent"]
    envelope = result["structuredContent"]
    assert result["isError"] is (envelope["status"] == "error")
    return result, envelope


# --- process inspection: `/proc` on Linux, `ps`/`lsof` where there is no `/proc` (macOS) -----------
#
# The lifecycle conformance suite proves a worker appears, is terminated and reaped, and leaves nothing
# behind. That contract is portable; only the way a test *observes* processes is not (ledger R28-H47).
# `GENIA_R28_PROCESS_BACKEND=proc|ps` forces a backend (the `ps` backend is also tested on Linux).


_TOOL_PATH = "/usr/bin:/bin:/usr/sbin:/sbin"  # `ps` and `lsof` (macOS keeps lsof in /usr/sbin)


def process_backend():
    forced = os.environ.get("GENIA_R28_PROCESS_BACKEND")
    if forced in ("proc", "ps"):
        return forced
    return "proc" if Path("/proc/self/stat").exists() else "ps"


def _proc_snapshot():
    """{pid: (ppid, start token, argv)} from /proc."""
    table = {}
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        try:
            stat = (entry / "stat").read_text()
            raw = (entry / "cmdline").read_bytes()
        except OSError:
            continue
        # the command name may contain spaces/parentheses: split after the last ')'
        fields = stat.rsplit(")", 1)[1].split()
        argv = [part.decode("utf-8", "replace") for part in raw.split(b"\0") if part]
        table[int(entry.name)] = (int(fields[1]), fields[19], argv)
    return table


def _ps_snapshot(pid=None):
    """{pid: (ppid, start token, argv)} from `ps` (POSIX; the start token is the 1 s `lstart` string)."""
    command = ["ps", "-axo", "pid=,ppid=,lstart=,command="]
    if pid is not None:
        command = ["ps", "-o", "pid=,ppid=,lstart=,command=", "-p", str(pid)]
    done = subprocess.run(command, capture_output=True, text=True, check=False, env={"LC_ALL": "C", "PATH": _TOOL_PATH})
    table = {}
    for line in done.stdout.splitlines():
        parts = line.split(None, 7)  # pid ppid <lstart: weekday month day time year> command...
        if len(parts) < 7 or not parts[0].isdigit() or not parts[1].isdigit():
            continue
        argv = parts[7].split() if len(parts) == 8 else []
        table[int(parts[0])] = (int(parts[1]), " ".join(parts[2:7]), argv)
    return table


def process_snapshot(pid=None):
    if process_backend() == "proc":
        table = _proc_snapshot()
        return table if pid is None else {pid: table[pid]} if pid in table else {}
    return _ps_snapshot(pid)


def process_children(pid):
    """Return the set of live descendant pids of `pid`."""
    parents = {p: entry[0] for p, entry in process_snapshot().items()}
    found, frontier = set(), {pid}
    while frontier:
        nxt = {p for p, parent in parents.items() if parent in frontier and p not in found}
        found |= nxt
        frontier = nxt
    return found


def _entry(pid):
    return process_snapshot(pid).get(pid)


def pid_alive(pid):
    """True while the pid is still in the process table. An unreaped zombie counts as alive: a
    killed worker that was never waited for is a reap failure, not a clean exit."""
    return _entry(pid) is not None


def process_identity(pid):
    """(pid, start token): a stable identity that survives pid reuse within a test."""
    entry = _entry(pid)
    return None if entry is None else (pid, entry[1])


def identity_exists(identity):
    entry = _entry(identity[0])
    return entry is not None and entry[1] == identity[1]


def _cmdline(pid):
    entry = _entry(pid)
    return [] if entry is None else list(entry[2])


def is_governed_worker(pid):
    """The governed execution worker: a Python process run as `-m hosts.python.mcp_worker`.

    Deliberately not an `unshare` wrapper (if one were ever a separate process) and not
    the one-time namespace probe: those are not the governed worker. Depth and parentage
    are not part of the contract, so this inspects only the command line.
    """
    argv = _cmdline(pid)
    return (
        len(argv) >= 3
        and Path(argv[0]).name.startswith("python")
        and "-m" in argv
        and argv[argv.index("-m") + 1] == "hosts.python.mcp_worker"
    )


def is_namespace_probe(pid):
    return any("/proc/net/dev" in part for part in _cmdline(pid))


class LauncherSession:
    """A live launcher-mode server with timed writes (for cancellation tests)."""

    def __init__(self, extra_env=None, *, command=None, cwd=None, env=None):
        self.proc = subprocess.Popen(
            command if command is not None else [sys.executable, "-m", "hosts.python.mcp_launch"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(cwd if cwd is not None else REPO_ROOT),
            env=env if env is not None else server_env(extra_env),
        )
        self._buffer = b""
        self.raw_stdout = b""  # every byte the server wrote to stdout, in order

    def send(self, message):
        self.proc.stdin.write(encode(message) + b"\n")
        self.proc.stdin.flush()

    def read(self, timeout=30):
        """Return the next response frame (own buffering: select never misses data)."""
        import select

        deadline = time.monotonic() + timeout
        while b"\n" not in self._buffer:
            remaining = deadline - time.monotonic()
            if remaining <= 0 or not select.select([self.proc.stdout], [], [], remaining)[0]:
                raise AssertionError("no response frame within the timeout")
            chunk = os.read(self.proc.stdout.fileno(), 65536)
            assert chunk != b"", "server closed stdout before the expected frame"
            self.raw_stdout += chunk
            self._buffer += chunk
        line, self._buffer = self._buffer.split(b"\n", 1)
        return json.loads(line.decode("utf-8"))

    def wait_ready(self, timeout=120):
        """Barrier: the server has bootstrapped and answered a request.

        Host initialization (including the one-time isolation probe) completes before the
        server reads its first request, so after this returns no bootstrap or probe work is
        left in the request path (ledger R28-H33).
        """
        self.send(request("server/discover", "ready"))
        response = self.read(timeout)
        assert response["id"] == "ready" and "result" in response, response

    def descendants(self):
        return process_children(self.proc.pid)

    def governed_workers(self):
        """Identities of live governed workers anywhere below the launcher."""
        return {
            process_identity(pid)
            for pid in self.descendants()
            if is_governed_worker(pid) and process_identity(pid) is not None
        }

    def probe_processes(self):
        return {pid for pid in self.descendants() if is_namespace_probe(pid)}

    def wait_for_worker(self, timeout=60):
        """Poll (bounded) until a governed worker exists; return its identities.

        An observable condition with a deadline, not a fixed sleep.
        """
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            found = self.governed_workers()
            if found:
                return found
            time.sleep(0.01)
        raise AssertionError("no governed worker process appeared within the timeout")

    def close(self):
        try:
            self.proc.stdin.close()
        except OSError:
            pass
        try:
            self.proc.wait(timeout=30)
        finally:
            for stream in (self.proc.stdout, self.proc.stderr):
                try:
                    stream.close()
                except OSError:
                    pass

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        if self.proc.poll() is None:
            self.proc.kill()
        self.close()


# --- E28-4: the checked-in client configuration and the stdio lifecycle -------------------

MCP_CONFIG_PATH = REPO_ROOT / ".mcp.json"
VSCODE_MCP_CONFIG_PATH = REPO_ROOT / ".vscode" / "mcp.json"
MCP_SERVER_NAME = "genia"
ACCEPTANCE_HARNESS_DIR = REPO_ROOT / "tools" / "mcp_acceptance"
STDIO_GUIDE_PATH = REPO_ROOT / "docs" / "mcp" / "stdio-development.md"

# What a typical stdio client passes to a child it launches (the official SDK's default
# environment): a handful of basic variables, not the developer's whole environment.
CLIENT_ENV_NAMES = ("HOME", "LOGNAME", "PATH", "SHELL", "TERM", "USER")


def load_mcp_config():
    assert MCP_CONFIG_PATH.is_file(), (
        "E28-4 not implemented: the repository-root .mcp.json does not exist"
    )
    return json.loads(MCP_CONFIG_PATH.read_text(encoding="utf-8"))


def configured_server():
    """The server entry exactly as a client would read it from `.mcp.json`."""
    return load_mcp_config()["mcpServers"][MCP_SERVER_NAME]


def configured_command():
    entry = configured_server()
    return [entry["command"], *entry.get("args", [])]


def client_environment():
    return {name: os.environ[name] for name in CLIENT_ENV_NAMES if name in os.environ}


def require_configured_launcher():
    """The configured command's executable must exist; skip locally, fail in CI."""
    import shutil

    import pytest

    executable = configured_command()[0]
    if shutil.which(executable, path=client_environment().get("PATH")) is None:
        message = f"the configured launcher {executable!r} is not on PATH here"
        if os.environ.get("CI"):
            pytest.fail(message)
        pytest.skip(message)


def configured_session():
    """Start the server the way a client does: the exact configured command, the repository
    root as working directory, a client-style minimal environment."""
    require_configured_launcher()
    return LauncherSession(
        command=configured_command(), cwd=REPO_ROOT, env=client_environment()
    )


def _lsof(args):
    done = subprocess.run(["lsof", "-nP", "-F", "pn", *args], capture_output=True, text=True, check=False,
                          env={"LC_ALL": "C", "PATH": _TOOL_PATH})
    return done.stdout.splitlines()


def _lsof_listening(pid=None):
    """Tokens `pid:address` of TCP sockets in LISTEN state (all processes, or one)."""
    lines = _lsof(["-iTCP", "-sTCP:LISTEN", *(["-a", "-p", str(pid)] if pid is not None else [])])
    tokens, current = set(), None
    for line in lines:
        if line.startswith("p"):
            current = line[1:]
        elif line.startswith("n") and current is not None:
            tokens.add(f"{current}:{line[1:]}")
    return tokens


def listening_inodes():
    """Identifiers of sockets currently in LISTEN state: inodes from /proc (Linux), else `pid:address`."""
    if process_backend() == "ps":
        return _lsof_listening()
    inodes = set()
    for name in ("tcp", "tcp6"):
        try:
            lines = Path(f"/proc/net/{name}").read_text().splitlines()[1:]
        except OSError:
            continue
        for line in lines:
            fields = line.split()
            if fields[3] == "0A":  # TCP_LISTEN
                inodes.add(fields[9])
    return inodes


def socket_inodes(pid):
    """Identifiers (same scheme as `listening_inodes`) of `pid`'s sockets; the `ps` backend reports only
    its listening sockets, which is what the no-listener assertions intersect with."""
    if process_backend() == "ps":
        return _lsof_listening(pid)
    found = set()
    try:
        for fd in Path(f"/proc/{pid}/fd").iterdir():
            try:
                target = os.readlink(fd)
            except OSError:
                continue
            if target.startswith("socket:["):
                found.add(target[len("socket:["):-1])
    except OSError:
        pass
    return found


def worker_workdir(identity):
    """The governed worker's private working directory, read while it is alive."""
    if process_backend() == "ps":
        for line in _lsof(["-a", "-d", "cwd", "-p", str(identity[0])]):
            if line.startswith("n"):
                return Path(line[1:])
        return None
    try:
        return Path(os.readlink(f"/proc/{identity[0]}/cwd"))
    except OSError:
        return None


# --- E28-6 / amendment A5: the 2025-11-25 compatibility era (initialize) ---------------------------

COMPAT_VERSION = "2025-11-25"

# Exactly what VS Code 1.138.0 sent on 2026-10-05 (docs/mcp/acceptance/vscode-copilot-evidence.md, run 1).
VSCODE_INITIALIZE_LINE = (
    b'{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-11-25",'
    b'"capabilities":{"roots":{"listChanged":true},"sampling":{},"elicitation":{"form":{},"url":{}},'
    b'"tasks":{"list":{},"cancel":{},"requests":{"sampling":{"createMessage":{}},'
    b'"elicitation":{"create":{}}}},"extensions":{"io.modelcontextprotocol/ui":'
    b'{"mimeTypes":["text/html;profile=mcp-app"]}}},"clientInfo":{"name":"Visual Studio Code",'
    b'"version":"1.138.0"}}}'
)
VSCODE_INITIALIZE = json.loads(VSCODE_INITIALIZE_LINE)
VSCODE_CAPABILITIES = VSCODE_INITIALIZE["params"]["capabilities"]
VSCODE_CLIENT_INFO = VSCODE_INITIALIZE["params"]["clientInfo"]
INITIALIZED_NOTIFICATION = {"jsonrpc": "2.0", "method": "notifications/initialized"}


def initialize_request(req_id=1, version=COMPAT_VERSION, capabilities=None, client_info=None, **params):
    """A compatibility-era `initialize` request (no per-request `_meta`)."""
    body = {
        "protocolVersion": version,
        "capabilities": VSCODE_CAPABILITIES if capabilities is None else capabilities,
        "clientInfo": VSCODE_CLIENT_INFO if client_info is None else client_info,
    }
    body.update(params)
    return {"jsonrpc": "2.0", "id": req_id, "method": "initialize", "params": body}


def compat_request(method, req_id=1, params=None):
    """A compatibility-era request: no `_meta` (the session, not the request, carries the era)."""
    message = {"jsonrpc": "2.0", "id": req_id, "method": method}
    if params is not None:
        message["params"] = params
    return message


def compat_call(name, arguments=None, req_id=1):
    params = {"name": name}
    if arguments is not None:
        params["arguments"] = arguments
    return compat_request("tools/call", req_id, params)


def compat_run(source, req_id=1):
    return compat_call("genia_run", {"source": source}, req_id)


def compat_parse(source, req_id=1):
    return compat_call("genia_parse", {"source": source}, req_id)


def compat_handshake(init_id="init"):
    return [initialize_request(init_id), INITIALIZED_NOTIFICATION]
