"""Worker supervisor for the MCP source-execution tool (R28 E28-3, issue #704).

A narrow host capability (ledger R28-H26, design D2): `RunCapability(...)(source,
is_cancel)` runs one fresh disposable worker (`hosts/python/mcp_worker.py`) for the
call and returns one closed reply line. It exists because `execution.process` cannot
launch the worker (child stdin is unavailable and argv cannot carry the allowed source
size); `execution.process` is unchanged and no Genia builtin is added.

Floor, every call: a fresh process in its own session/process group; a fixed minimal
environment (no PATH, no HOME, no user variables); a private empty working directory
removed after the worker is reaped; only the three standard pipes inherited; the source
sent over the stdin pipe; a monotonic 5,000 ms deadline; incremental reply-size cap;
forceful kill of the process group and reap on timeout, cancellation, overflow, or any
failure; worker stderr drained and discarded. Where a user+network namespace is
*verified* to work here it is added (best effort, never claimed otherwise). That
verification happens once, when the capability is constructed during host
initialization and before the server reads any request; the request path only consumes
the already-determined isolation profile, so first-request behavior does not depend on
a capability probe (ledger R28-H33). This is a defense-in-depth profile, not a security
sandbox.

It checks only the reply's shape (one ASCII line with a known status); native
`mcp.genia` decodes and interprets it. Cancellation is observed by handing each raw
line that arrives on the stdin multiplexer to the native predicate `is_cancel`; this
module does no JSON, method, or request-id interpretation.
"""

from __future__ import annotations

import os
import re
import select
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

DEADLINE_MS = 5000
# The one-time namespace probe runs at host initialization. It is bounded so a hung
# `unshare` can delay server start by at most this long, never a request.
PROBE_TIMEOUT_S = 5
REPLY_CAP_BYTES = 20 * 1024 * 1024  # 3 channels at 1 MiB, worst-case ASCII escaping
_READ_SIZE = 65536
_WRITE_SIZE = 65536

REPO_ROOT = Path(__file__).resolve().parents[2]
# Launch plumbing only. No PATH, HOME, or user variable is passed to the worker.
ENV_ALLOWLIST = (
    "LD_LIBRARY_PATH",
    "DYLD_LIBRARY_PATH",
    "PYTHONIOENCODING",
    "LANG",
    "LC_ALL",
)
DEFAULT_WORKER_ARGV = [sys.executable, "-B", "-m", "hosts.python.mcp_worker"]

_TIMEOUT = '{"status": "timeout"}'
_CANCELLED = '{"status": "cancelled"}'
_INTERNAL = '{"status": "internal_error"}'
_REPLY_SHAPE = re.compile(
    r'\{"status": "(completed|parse_error|policy_denied|runtime_error|result_limit|internal_error)"[,}]'
)

_namespace_probe = None
_unshare_path = None  # resolved once, by the successful probe


def _probe_code() -> str:
    return (
        "print(','.join(l.split(':')[0].strip() "
        "for l in open('/proc/net/dev').read().splitlines()[2:]))"
    )


def network_isolation_available() -> bool:
    """True only if a user+network namespace was *verified* to work (cached).

    `RunCapability` forces this at construction, so it is already determined before the
    first request; later calls are a cached read.
    """
    global _namespace_probe
    if _namespace_probe is None:
        _namespace_probe = _run_probe()
    return _namespace_probe


def _run_probe() -> bool:
    global _unshare_path
    unshare = shutil.which("unshare")
    if unshare is None or not sys.platform.startswith("linux"):
        return False
    try:
        done = subprocess.run(
            [unshare, "--user", "--map-root-user", "--net", "--", sys.executable, "-S", "-c", _probe_code()],
            capture_output=True,
            text=True,
            timeout=PROBE_TIMEOUT_S,
            stdin=subprocess.DEVNULL,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    verified = done.returncode == 0 and done.stdout.strip() == "lo"
    if verified:
        _unshare_path = unshare
    return verified


def worker_command(argv, isolated=None):
    """The worker argv, wrapped in a verified user+network namespace when `isolated`.

    `isolated=None` consults the cached probe result (used by tests and tools).
    """
    if network_isolation_available() if isolated is None else isolated:
        return [_unshare_path or shutil.which("unshare"), "--user", "--map-root-user", "--net", "--", *argv]
    return list(argv)


def _worker_environment() -> dict:
    env = {key: os.environ[key] for key in ENV_ALLOWLIST if key in os.environ}
    env["PYTHONPATH"] = os.pathsep.join([str(REPO_ROOT), str(REPO_ROOT / "src")])
    env["PYTHONUTF8"] = "1"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


class RunCapability:
    def __init__(self, mux=None, *, worker_argv=None, deadline_ms: int = DEADLINE_MS):
        self._mux = mux
        self._argv = list(worker_argv) if worker_argv is not None else list(DEFAULT_WORKER_ARGV)
        self._deadline_s = deadline_ms / 1000.0
        # Determined here, during host initialization, never inside a request.
        self._isolated = network_isolation_available()

    @property
    def isolation_profile(self) -> dict:
        """The best-effort isolation actually in force (honest reporting; not a sandbox)."""
        return {"network_namespace": self._isolated}

    def run(self, source: str, is_cancel) -> str:
        try:
            return self._run(source, is_cancel)
        except Exception:
            return _INTERNAL

    __call__ = run

    def _run(self, source: str, is_cancel) -> str:
        mux = self._mux
        if mux is not None and mux.scan(is_cancel):
            return _CANCELLED  # claimed before any worker existed
        data = source.encode("utf-8")
        command = worker_command(self._argv, self._isolated)
        workdir = tempfile.mkdtemp(prefix="genia-worker-")
        deadline = time.monotonic() + self._deadline_s
        proc = None
        try:
            proc = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=workdir,
                env=_worker_environment(),
                close_fds=True,
                start_new_session=True,
                bufsize=0,
            )
            return self._supervise(proc, data, deadline, is_cancel)
        finally:
            if proc is not None:
                _kill_and_reap(proc)
            shutil.rmtree(workdir, ignore_errors=True)

    def _supervise(self, proc, data: bytes, deadline: float, is_cancel) -> str:
        mux = self._mux
        stdin_fd, out_fd, err_fd = proc.stdin.fileno(), proc.stdout.fileno(), proc.stderr.fileno()
        for fd in (stdin_fd, out_fd, err_fd):
            os.set_blocking(fd, False)
        sent = 0
        stdin_open = True
        out_open = err_open = True
        reply = bytearray()
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return _TIMEOUT
            readers = []
            if out_open:
                readers.append(out_fd)
            if err_open:
                readers.append(err_fd)
            watch_mux = mux is not None and mux.wants_read()
            if watch_mux:
                readers.append(mux.fileno())
            writers = [stdin_fd] if stdin_open else []
            if not readers and not writers:
                # Both worker pipes closed: wait for exit while still honoring cancel.
                if proc.poll() is not None:
                    return _finish(proc, bytes(reply))
                if mux is not None and mux.pump(min(remaining, 0.05), is_cancel):
                    return _CANCELLED
                if mux is None:
                    time.sleep(min(remaining, 0.02))
                continue
            ready_r, ready_w, _ = select.select(readers, writers, [], min(remaining, 0.25))
            if out_fd in ready_r:
                chunk = os.read(out_fd, _READ_SIZE)
                if chunk == b"":
                    out_open = False
                else:
                    reply.extend(chunk)
                    if len(reply) > REPLY_CAP_BYTES:
                        return _INTERNAL
            if err_fd in ready_r:
                if os.read(err_fd, _READ_SIZE) == b"":  # drained and discarded
                    err_open = False
            if stdin_open and stdin_fd in ready_w:
                try:
                    sent += os.write(stdin_fd, data[sent : sent + _WRITE_SIZE])
                except BlockingIOError:
                    pass
                except BrokenPipeError:  # the worker stopped reading: stop writing
                    sent = len(data)
                if sent >= len(data):
                    proc.stdin.close()
                    stdin_open = False
            if watch_mux and mux.fileno() in ready_r:
                if mux.pump(0, is_cancel):
                    return _CANCELLED
            if not out_open and not err_open and not stdin_open and proc.poll() is not None:
                return _finish(proc, bytes(reply))


def _finish(proc, reply: bytes) -> str:
    """Validate the worker's reply shape; anything else is `internal_error`."""
    if proc.returncode != 0:
        return _INTERNAL
    try:
        text = reply.decode("ascii")
    except UnicodeDecodeError:
        return _INTERNAL
    if text.count("\n") != 1 or not text.endswith("}\n"):
        return _INTERNAL
    text = text[:-1]
    if _REPLY_SHAPE.match(text) is None:
        return _INTERNAL
    return text


def _kill_and_reap(proc) -> None:
    """Kill the worker's whole process group and reap it (idempotent)."""
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        pass
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()
    for stream in (proc.stdin, proc.stdout, proc.stderr):
        try:
            if stream is not None:
                stream.close()
        except OSError:
            pass
