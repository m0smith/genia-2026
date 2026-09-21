"""Experimental Python-host direct process transport for `execution.process`.

This module has no Genia-visible surface: it is a private host capability
consumed by `genia.process_execution.perform_process_execution` (and,
through a capability's launcher, by whatever the deferred provisioning
boundary eventually constructs). It accepts an already-resolved native
target, an exact argv list, and a bounded timeout, and makes exactly one
direct launch attempt -- never a shell, never a PATH search of its own,
never more than one attempt.

Mechanism note (`docs/design/execution-process-design.md` §3): everything
below is Python-reference-host mechanism, not portable semantics. A future
C++ host must reach the same *observations* (bounded timeout, independent
1,048,576-byte stdout/stderr limits, concurrent non-blocking drain,
guaranteed child cleanup, nonzero exit as ordinary data, closed failure
`kind`s) through unrelated native mechanisms.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable
import subprocess
import threading
import time

OUTPUT_LIMIT_BYTES = 1_048_576

_READ_CHUNK_SIZE = 65536
_POLL_INTERVAL_SECONDS = 0.01
_CLEANUP_JOIN_SECONDS = 5.0


@dataclass(frozen=True)
class ProcessTransportResult:
    """Private normalized successful direct-execution attempt."""

    exit_code: int
    stdout: bytes
    stderr: bytes


@dataclass(frozen=True)
class ProcessTransportFailure:
    """Private normalized transport failure with a closed `kind`.

    `kind` is one of `{"launch", "timeout", "output-limit", "provider"}`.
    `timeout_ms` is populated only for `kind == "timeout"`. No field ever
    carries a native path, raw exception text, or partial output -- the
    normalization boundary (`genia.process_execution`) has nothing more to
    leak even if it tried.
    """

    kind: str
    timeout_ms: int | None = None


SpawnHook = Callable[[int], None]


class _StreamDrain:
    """Reads one child output stream in its own thread, incrementally
    bounding the total at `limit` bytes without ever buffering more.
    """

    def __init__(self, stream: object, limit: int = OUTPUT_LIMIT_BYTES):
        self._stream = stream
        self._limit = limit
        self.buffer = bytearray()
        self.overflowed = False

    def run(self) -> None:
        total = 0
        try:
            while True:
                chunk = self._stream.read(_READ_CHUNK_SIZE)  # type: ignore[attr-defined]
                if not chunk:
                    return
                total += len(chunk)
                if total > self._limit:
                    # Overflow: stop draining immediately. The chunk that
                    # crossed the bound is discarded, not appended -- the
                    # buffer is discarded wholesale on overflow regardless,
                    # but there is no reason to grow it further.
                    self.overflowed = True
                    return
                self.buffer.extend(chunk)
        except (OSError, ValueError):
            # The pipe was closed out from under us (the child was killed
            # during cleanup elsewhere) -- not a drain error to report.
            return


def _close_quietly(stream: object | None) -> None:
    if stream is None:
        return
    try:
        stream.close()  # type: ignore[attr-defined]
    except Exception:  # noqa: BLE001 - best-effort cleanup only
        pass


def _kill_and_reap(proc: subprocess.Popen) -> None:
    """Unconditionally ensure the owned child is terminated and reaped.

    Uses `Popen.kill()`, which sends `SIGKILL` on POSIX -- unblockable and
    unignorable, so a child that deliberately ignores `SIGTERM` still dies
    (contract §8/§12: "no owned child may remain running indefinitely").
    """

    if proc.poll() is None:
        try:
            proc.kill()
        except ProcessLookupError:
            pass
    for _attempt in range(2):
        try:
            proc.wait(timeout=_CLEANUP_JOIN_SECONDS)
            return
        except subprocess.TimeoutExpired:
            continue


def launch_process(
    executable: str,
    args: list[str],
    timeout_ms: int,
    *,
    spawn_hook: SpawnHook | None = None,
) -> ProcessTransportResult | ProcessTransportFailure:
    """Make exactly one direct launch attempt.

    `executable` is the already-resolved native target, never a portable
    symbol: this function performs no symbol lookup and no alias/extension
    search of its own. `args` become exact child argv elements after
    `executable` -- no shell, no shell parsing, no expansion: this is a
    structured `subprocess.Popen(argv, ...)` call with `shell=False`.

    This function does not itself perform a PATH search: it hands
    `executable` to `Popen` exactly as given. Choosing an `executable`
    value that is independent of PATH (e.g. an absolute path) is the
    responsibility of whatever privileged provisioning code decides a
    capability's symbol -> native-target bindings
    (`docs/design/execution-process-design.md` §5/§22); a portable Genia
    caller can never supply this value directly, so it cannot itself
    obtain PATH-based execution authority.
    """

    argv = [executable, *args]
    deadline = time.monotonic() + (timeout_ms / 1000.0)

    try:
        proc = subprocess.Popen(  # noqa: S603 - argv only, shell=False, no PATH text parsing
            argv,
            shell=False,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            close_fds=True,
        )
    except OSError:
        return ProcessTransportFailure(kind="launch")

    if spawn_hook is not None:
        try:
            spawn_hook(proc.pid)
        except Exception:  # noqa: BLE001 - a test-only hook must never affect the attempt
            pass

    stdout_drain = _StreamDrain(proc.stdout)
    stderr_drain = _StreamDrain(proc.stderr)
    stdout_thread = threading.Thread(target=stdout_drain.run, daemon=True)
    stderr_thread = threading.Thread(target=stderr_drain.run, daemon=True)
    stdout_thread.start()
    stderr_thread.start()

    failure_kind: str | None = None
    try:
        while True:
            if stdout_drain.overflowed or stderr_drain.overflowed:
                failure_kind = "output-limit"
                break
            child_exited = proc.poll() is not None
            if child_exited and not stdout_thread.is_alive() and not stderr_thread.is_alive():
                break
            if time.monotonic() >= deadline:
                failure_kind = "timeout"
                break
            time.sleep(_POLL_INTERVAL_SECONDS)
    except Exception:  # noqa: BLE001 - normalized boundary, never re-raised
        failure_kind = "provider"

    if failure_kind is not None:
        _kill_and_reap(proc)
        stdout_thread.join(timeout=_CLEANUP_JOIN_SECONDS)
        stderr_thread.join(timeout=_CLEANUP_JOIN_SECONDS)
        _close_quietly(proc.stdout)
        _close_quietly(proc.stderr)
        if failure_kind == "timeout":
            return ProcessTransportFailure(kind="timeout", timeout_ms=timeout_ms)
        return ProcessTransportFailure(kind=failure_kind)

    stdout_thread.join(timeout=_CLEANUP_JOIN_SECONDS)
    stderr_thread.join(timeout=_CLEANUP_JOIN_SECONDS)
    exit_status = proc.wait()
    _close_quietly(proc.stdout)
    _close_quietly(proc.stderr)

    if stdout_drain.overflowed or stderr_drain.overflowed:
        # Overflow detected exactly as the child was also exiting on its
        # own; still a bounds violation, never a successful result.
        _kill_and_reap(proc)
        return ProcessTransportFailure(kind="output-limit")

    if exit_status < 0:
        # Terminated by a signal we did not send -- not a portable normal-
        # exit status (contract §11); this slice has no signal identity to
        # expose, so normalize rather than fabricate an exit code.
        return ProcessTransportFailure(kind="provider")

    return ProcessTransportResult(
        exit_code=exit_status,
        stdout=bytes(stdout_drain.buffer),
        stderr=bytes(stderr_drain.buffer),
    )
