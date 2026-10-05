"""Disposable worker for the MCP source-execution tool (R28 E28-3, issue #704).

One fresh process per call (started by `mcp_run_capability`). It reads the source from
stdin, applies process limits, parses with the real parser, runs the pre-execution
policy over the raw parser AST (contract Clarification A4), evaluates with
command-source semantics in a pruned, default-deny Genia environment, renders the
value with the canonical debug renderer, and writes exactly one ASCII JSON line.

It builds no MCP envelope, tool name, or message: the closed reply statuses are
`completed`, `parse_error`, `policy_denied`, `runtime_error`, `result_limit`, and
`internal_error`; native `mcp.genia` maps them. Not a security sandbox: this is a
defense-in-depth profile (docs/design/r28-e28-3-genia-run-design.md, section 5).
"""

from __future__ import annotations

import contextlib
import json
import os
import re
import signal
import socket
import subprocess
import sys

import genia
import genia.interpreter  # noqa: F401 - registers the interpreter runtime
from genia.configuration import contains_protected
from genia.environment import Env
from genia.utf8 import format_debug
from genia.interpreter import Parser, lex

from hosts.python.mcp_worker_profile import policy_violation, prune_environment

# Written to the worker's real stderr once bootstrap (interpreter, imports, limits) is done
# and before any source is read or evaluated: the supervisor starts the execution deadline
# here, so the 5,000 ms bounds parse/policy/evaluation/render, not process launch (contract
# section 5). Trusted bootstrap runs no user code. Keep in sync with the supervisor.
READY_MARKER = b"GENIA-WORKER-READY\n"
# Orphan backstop (E28-4): not a second deadline. The supervisor kills the worker at its
# deadline, so a healthy run never reaches this; it bounds only a worker whose host died
# without cleaning up (SIGKILL). SIGALRM's default action terminates the process.
ORPHAN_BACKSTOP_SECONDS = 8
SOURCE_MAX_BYTES = 262144
CHANNEL_MAX_BYTES = 1048576
ADDRESS_SPACE_BYTES = 2 * 1024 * 1024 * 1024
CPU_SECONDS = 10
OPEN_FILES = 64

_TRAILING_OFFSET = re.compile(r" at (\d+)$")


class ChannelLimitExceeded(Exception):
    """A program output channel crossed its byte limit."""


class BoundedStream:
    """In-memory text sink that stops the program when its byte limit is crossed."""

    def __init__(self, limit: int):
        self._limit = limit
        self._parts: list[str] = []
        self._bytes = 0
        self.overflowed = False

    def write(self, text: str) -> int:
        self._bytes += len(text.encode("utf-8", "surrogatepass"))
        if self._bytes > self._limit:
            self.overflowed = True
            self._parts.clear()  # discard partial data immediately
            raise ChannelLimitExceeded()
        self._parts.append(text)
        return len(text)

    def flush(self) -> None:
        return None

    def getvalue(self) -> str:
        return "".join(self._parts)


def apply_limits() -> None:
    """Self-imposed process limits (a runtime layer beneath policy and pruning)."""
    import resource

    resource.setrlimit(resource.RLIMIT_FSIZE, (0, 0))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_CPU, (CPU_SECONDS, CPU_SECONDS))
    resource.setrlimit(resource.RLIMIT_NOFILE, (OPEN_FILES, OPEN_FILES))
    resource.setrlimit(resource.RLIMIT_AS, (ADDRESS_SPACE_BYTES, ADDRESS_SPACE_BYTES))


def _development_diagnostic(exc: BaseException) -> None:
    """Name an internal worker failure on the worker's own stderr, only when asked.

    Development/test aid (ledger R28-H47). The supervisor drains and discards worker stderr
    (apart from the readiness marker), so this never reaches an MCP client; the reply is
    still the fixed `internal_error`. Off unless GENIA_MCP_WORKER_DIAG=1, which the supervisor
    never forwards: only a developer who launches the worker directly can set it.
    """
    if os.environ.get("GENIA_MCP_WORKER_DIAG") != "1":
        return
    detail = f"{type(exc).__name__}: errno={getattr(exc, 'errno', None)} args={exc.args!r}"
    sys.stderr.write(f"GENIA-WORKER-DIAG {detail}\n")
    sys.stderr.flush()


def _deny(*_args, **_kwargs):
    raise PermissionError("not permitted in the MCP execution profile")


@contextlib.contextmanager
def _restricted_runtime():
    """Scoped runtime layer: no imports, no process creation, no network use.

    Shell stages call `subprocess` directly from the evaluator and `import` loads
    modules through `Env.load_module`; neither goes through a removable binding
    (ledger R28-H28), so they are stubbed here in addition to policy and pruning.
    """
    patches = [
        (Env, "load_module", _deny),
        (subprocess, "Popen", _deny),
        (subprocess, "run", _deny),
        (subprocess, "call", _deny),
        (subprocess, "check_call", _deny),
        (subprocess, "check_output", _deny),
        (os, "system", _deny),
        (os, "popen", _deny),
        (os, "fork", _deny),
        (os, "forkpty", _deny),
        (os, "posix_spawn", _deny),
        (os, "posix_spawnp", _deny),
        (socket.socket, "connect", _deny),
        (socket.socket, "connect_ex", _deny),
        (socket.socket, "bind", _deny),
        (socket.socket, "listen", _deny),
        (socket.socket, "sendto", _deny),
        (socket, "create_connection", _deny),
    ]
    for name in dir(os):
        if name.startswith(("exec", "spawn")) and callable(getattr(os, name)):
            patches.append((os, name, _deny))
    saved = [(owner, name, getattr(owner, name)) for owner, name, _ in patches]
    try:
        for owner, name, replacement in patches:
            setattr(owner, name, replacement)
        yield
    finally:
        for owner, name, original in saved:
            setattr(owner, name, original)


def build_reply(value, stdout: str, stderr: str) -> dict:
    """Turn a finished evaluation into the closed reply (never partial on failure)."""
    try:
        if contains_protected(value):
            return {"status": "policy_denied"}
        rendered = format_debug(value)
    except Exception:
        return {"status": "internal_error"}
    for text in (rendered, stdout, stderr):
        if len(text.encode("utf-8", "surrogatepass")) > CHANNEL_MAX_BYTES:
            return {"status": "result_limit"}
    return {"status": "completed", "value": rendered, "stdout": stdout, "stderr": stderr}


# NOTE: `run_source` must not be bound in this module's namespace: when started with
# `-m`, this module is `__main__`, and Genia's interpreter-runtime lookup would pick it.


def execute_source(source: str, *, enforce_policy: bool = True) -> dict:
    """Evaluate `source` once and return the closed reply dictionary.

    Does not apply process limits (that is `main`'s job); the restricted-runtime
    stubs are scoped to this call.
    """
    try:
        nodes = Parser(lex(source), source=source, filename="<command>").parse_program()
    except SyntaxError as error:
        match = _TRAILING_OFFSET.search(str(error))
        return {"status": "parse_error", "offset": int(match.group(1)) if match else None}
    except Exception:
        return {"status": "internal_error"}
    try:
        if enforce_policy and policy_violation(nodes):
            return {"status": "policy_denied"}
    except Exception:
        return {"status": "internal_error"}

    stdout, stderr = BoundedStream(CHANNEL_MAX_BYTES), BoundedStream(CHANNEL_MAX_BYTES)
    try:
        env = genia.make_global_env(
            cli_args=[],
            stdin_provider=lambda: iter(()),
            stdout_stream=stdout,
            stderr_stream=stderr,
            environment_snapshot_provider=dict,
            dotenv_snapshot_provider=_deny,
        )
        prune_environment(env)
    except Exception:
        return {"status": "internal_error"}

    failed = False
    value = None
    with _restricted_runtime():
        try:
            value = genia.run_source(source, env, filename="<command>")
        except BaseException:  # noqa: BLE001 - every program failure is runtime_error
            failed = True
    if stdout.overflowed or stderr.overflowed:
        return {"status": "result_limit"}
    if failed:
        return {"status": "runtime_error"}
    return build_reply(value, stdout.getvalue(), stderr.getvalue())


def _serialize(reply: dict) -> bytes:
    return (json.dumps(reply, ensure_ascii=True, allow_nan=False) + "\n").encode("ascii")


def main() -> int:
    # The runtime stubs stay installed until the process exits, so threads an evaluated
    # program leaves behind cannot create processes or use sockets after evaluation.
    with _restricted_runtime():
        try:
            apply_limits()
            sys.stderr.buffer.write(READY_MARKER)
            sys.stderr.buffer.flush()
            signal.setitimer(signal.ITIMER_REAL, ORPHAN_BACKSTOP_SECONDS)
            data = sys.stdin.buffer.read(SOURCE_MAX_BYTES + 1)
            if len(data) > SOURCE_MAX_BYTES:
                reply = {"status": "internal_error"}
            else:
                reply = execute_source(data.decode("utf-8"))
        except BaseException as exc:  # noqa: BLE001
            _development_diagnostic(exc)
            reply = {"status": "internal_error"}
        try:
            sys.stdout.buffer.write(_serialize(reply))
            sys.stdout.buffer.flush()
        finally:
            # Evaluated programs may leave non-daemon threads behind; never wait for them.
            os._exit(0)


if __name__ == "__main__":
    raise SystemExit(main())
