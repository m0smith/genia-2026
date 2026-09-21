"""Test-only deterministic child-process fixtures for `execution.process` tests.

These helpers build small, deterministic argv lists that run a tiny inline
Python script via ``sys.executable -c <script>``. They exist purely to drive
the *Python reference-host* implementation once it exists.

They are explicitly NOT part of the portable `execution.process` contract
(`docs/design/execution-process-contract.md`) or design
(`docs/design/execution-process-design.md` §20, "Fixture design"): a future
non-Python host's own conformance fixtures need not reproduce anything in
this file, and nothing here defines observable Genia behavior.

No production `genia.process_*` module is imported or referenced here. This
file only produces argv lists (and occasionally raw byte payloads to compare
against); it never invokes `execution.process` itself.
"""

from __future__ import annotations

import base64
import sys

OUTPUT_LIMIT_BYTES = 1_048_576


def python_argv(script: str) -> list[str]:
    """Build argv for running ``script`` as inline Python source.

    ``sys.executable`` is test-setup-only (per the RED-phase reliability
    rules, "use sys.executable ... only where host-specific test setup
    requires it") — it is the target OS executable a future
    `execution.process` launcher would resolve a bound symbol to, not a
    portable Genia concept.
    """
    return [sys.executable, "-c", script]


def exit_with(code: int) -> list[str]:
    """Child exits immediately with ``code`` and produces no output."""
    return python_argv(f"import sys as _s; _s.exit({code})")


def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def write_stdout_exact(data: bytes) -> list[str]:
    """Child writes exactly ``data`` to stdout (no trailing newline) and exits 0."""
    script = (
        "import sys, base64 as _b\n"
        f"sys.stdout.buffer.write(_b.b64decode({_b64(data)!r}))\n"
        "sys.stdout.buffer.flush()\n"
    )
    return python_argv(script)


def write_stderr_exact(data: bytes) -> list[str]:
    """Child writes exactly ``data`` to stderr (no trailing newline) and exits 0."""
    script = (
        "import sys, base64 as _b\n"
        f"sys.stderr.buffer.write(_b.b64decode({_b64(data)!r}))\n"
        "sys.stderr.buffer.flush()\n"
    )
    return python_argv(script)


def write_both_exact(stdout_data: bytes, stderr_data: bytes) -> list[str]:
    """Child writes exact bytes to both stdout and stderr, then exits 0."""
    script = (
        "import sys, base64 as _b\n"
        f"sys.stdout.buffer.write(_b.b64decode({_b64(stdout_data)!r}))\n"
        "sys.stdout.buffer.flush()\n"
        f"sys.stderr.buffer.write(_b.b64decode({_b64(stderr_data)!r}))\n"
        "sys.stderr.buffer.flush()\n"
    )
    return python_argv(script)


def write_n_bytes(stream: str, n: int, *, fill: bytes = b"A") -> list[str]:
    """Child writes exactly ``n`` bytes (repeating ``fill``) to ``stream`` ("stdout"/"stderr").

    Generates the payload inside the child rather than embedding ``n`` bytes
    of literal text in the script, so this stays cheap even for
    multi-megabyte payloads (e.g. testing the 1,048,576-byte output limit).
    """
    if stream not in ("stdout", "stderr"):
        raise ValueError("stream must be 'stdout' or 'stderr'")
    script = (
        "import sys\n"
        f"_stream = sys.{stream}.buffer\n"
        f"_n = {n}\n"
        f"_fill = {fill!r}\n"
        "_chunk = (_fill * (65536 // len(_fill) + 1))[:65536]\n"
        "_written = 0\n"
        "while _written < _n:\n"
        "    _piece = _chunk[: min(65536, _n - _written)]\n"
        "    _stream.write(_piece)\n"
        "    _written += len(_piece)\n"
        "_stream.flush()\n"
    )
    return python_argv(script)


def write_forever(stream: str) -> list[str]:
    """Child writes an endless stream of bytes to `stream` until killed.

    Never stops on its own. Used to prove output-limit enforcement is
    checked incrementally during draining rather than by buffering an
    entire (here, effectively unbounded) write before checking its length:
    a "buffer fully, then check" implementation would hang trying to reach
    EOF against a child that never provides one, while a correct
    incremental-check implementation detects the overflow and kills the
    child promptly, well before any large amount of memory could
    accumulate.
    """
    if stream not in ("stdout", "stderr"):
        raise ValueError("stream must be 'stdout' or 'stderr'")
    script = (
        "import sys\n"
        f"_stream = sys.{stream}.buffer\n"
        "_chunk = b'Z' * 65536\n"
        "while True:\n"
        "    _stream.write(_chunk)\n"
        "    _stream.flush()\n"
    )
    return python_argv(script)


def interleave_stdout_stderr(chunk_size: int, chunk_count: int) -> list[str]:
    """Child alternately writes ``chunk_count`` chunks of ``chunk_size`` bytes
    to stdout and stderr, flushing after every write.

    Designed to pressure a naive sequential-drain implementation: total
    bytes per channel is ``chunk_size * chunk_count``, which should exceed a
    single OS pipe buffer (typically 64 KiB) so a reader that fully drains
    stdout before ever touching stderr (or vice versa) will stall once the
    child blocks writing to the unread channel.
    """
    script = (
        "import sys\n"
        f"_chunk_size = {chunk_size}\n"
        f"_chunk_count = {chunk_count}\n"
        "_out = sys.stdout.buffer\n"
        "_err = sys.stderr.buffer\n"
        "_payload_out = b'O' * _chunk_size\n"
        "_payload_err = b'E' * _chunk_size\n"
        "for _i in range(_chunk_count):\n"
        "    _out.write(_payload_out); _out.flush()\n"
        "    _err.write(_payload_err); _err.flush()\n"
    )
    return python_argv(script)


def sleep_ms(ms: int) -> list[str]:
    """Child sleeps for ``ms`` milliseconds then exits 0 with no output."""
    return python_argv(f"import time as _t; _t.sleep({ms} / 1000)")


def sleep_forever_ignoring_term() -> list[str]:
    """Child ignores SIGTERM and sleeps indefinitely; only SIGKILL stops it.

    Used to prove cleanup uses a mechanism strong enough to guarantee no
    owned child survives (contract §8/§12: "no owned child may remain
    running indefinitely after the call returns").
    """
    script = (
        "import signal, time\n"
        "signal.signal(signal.SIGTERM, signal.SIG_IGN)\n"
        "while True:\n"
        "    time.sleep(1)\n"
    )
    return python_argv(script)


def echo_argv_nul_joined() -> list[str]:
    """Child writes every argv element after the script (``sys.argv[1:]``),
    NUL-joined, to stdout verbatim.

    Used to prove exact literal argv preservation (contract §7): each
    element the caller supplies becomes exactly one child argument, with no
    shell parsing, quoting, or expansion.
    """
    script = (
        "import sys\n"
        "sys.stdout.buffer.write(\n"
        "    b'\\x00'.join(a.encode('utf-8', 'surrogateescape') for a in sys.argv[1:])\n"
        ")\n"
    )
    return python_argv(script)


def nonexistent_target_path() -> str:
    """A path guaranteed not to exist and not resolvable via PATH, for launch-failure tests."""
    return "/nonexistent/genia-execution-process-fixture-target/does-not-exist"
