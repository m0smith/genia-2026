"""Raw stdin line multiplexer for the native Genia MCP server (R28 E28-3, issue #704).

Transport framing only (ledger R28-H27, design D3): it reads raw bytes from one
descriptor, splits on ``\\n`` only (never ``str.splitlines``), decodes UTF-8 with
``surrogateescape`` (the decoding the ordinary stdin source yields), and supplies the
line iterator that native ``mcp.genia`` consumes unchanged (``stdin |> lines``).

While a source-execution call is in flight the supervisor uses ``pump`` to read lines
that arrive and hands each raw line to a *native* predicate. This module performs no
JSON decoding, method matching, or request-id comparison: protocol interpretation stays
in ``mcp.genia``. Lines the predicate does not claim stay queued, in order, for the
native loop.
"""

from __future__ import annotations

import os
import select
from collections import deque

# Back-pressure: stop reading while this much input is waiting unread by the native
# loop, so a flooding client cannot grow server memory without bound.
MAX_PENDING_BYTES = 8 * 1024 * 1024
_READ_SIZE = 65536


class LineMux:
    def __init__(self, fd: int):
        self._fd = fd
        self._buffer = b""
        self.pending: deque[str] = deque()
        self.pending_bytes = 0
        self.eof = False

    def fileno(self) -> int:
        return self._fd

    def wants_read(self) -> bool:
        return not self.eof and self.pending_bytes + len(self._buffer) <= MAX_PENDING_BYTES

    @staticmethod
    def _enqueue(raw: bytes) -> str:
        return raw.decode("utf-8", "surrogateescape")

    def _read_available(self) -> list[str]:
        """Read one chunk; return the complete lines it finished (EOF flushes the rest)."""
        chunk = os.read(self._fd, _READ_SIZE)
        lines: list[str] = []
        if chunk == b"":
            self.eof = True
            if self._buffer:
                lines.append(self._enqueue(self._buffer))
                self._buffer = b""
            return lines
        self._buffer += chunk
        *complete, self._buffer = self._buffer.split(b"\n")
        lines.extend(self._enqueue(raw) for raw in complete)
        return lines

    def _accept(self, line: str) -> None:
        self.pending.append(line)
        self.pending_bytes += len(line.encode("utf-8", "surrogateescape"))

    def pump(self, timeout, is_cancel=None) -> bool:
        """Read what is available (waiting up to `timeout` seconds; None blocks).

        Returns True when `is_cancel` claimed a newly arrived line, which is dropped.
        Every other line, including those after the claimed one, is queued in order.
        """
        if not self.wants_read():
            return False
        ready, _, _ = select.select([self._fd], [], [], timeout)
        if not ready:
            return False
        claimed = False
        for line in self._read_available():
            if not claimed and is_cancel is not None and _claims(is_cancel, line):
                claimed = True
                continue
            self._accept(line)
        return claimed

    def scan(self, is_cancel) -> bool:
        """Drop and report the first already-queued line `is_cancel` claims."""
        for line in list(self.pending):
            if _claims(is_cancel, line):
                self.pending.remove(line)
                self.pending_bytes -= len(line.encode("utf-8", "surrogateescape"))
                return True
        return False

    def provider(self):
        """Yield queued and newly read lines until EOF (the native loop's stdin source)."""
        while True:
            if self.pending:
                line = self.pending.popleft()
                self.pending_bytes -= len(line.encode("utf-8", "surrogateescape"))
                yield line
                continue
            if self.eof:
                return
            for line in self._read_available():
                self._accept(line)


def _claims(is_cancel, line: str) -> bool:
    try:
        return bool(is_cancel(line))
    except Exception:  # a failing predicate is never a cancellation
        return False
