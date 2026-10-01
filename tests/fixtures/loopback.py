"""Collision-free local ports for loopback tests.

Asking the OS for port 0, closing the socket, and binding the number later is
racy under ``pytest -n auto``. The released port is in the ephemeral range, so
another worker's outgoing connection (or listener) can take it before the server
under test binds, and the server then fails with ``Address already in use``.

``free_port`` instead hands out ports *below* the ephemeral range (Linux:
32768-60999; macOS/BSD: 49152-65535), from a block reserved for the current
xdist worker. Outgoing connections never auto-assign these ports and no other
worker draws from the same block, so a port stays free between this call and the
server's bind. A bind probe still skips any port an unrelated local service holds.
"""

from __future__ import annotations

import itertools
import os
import socket

PORT_BASE = 20000
PORTS_PER_WORKER = 400
WORKER_SLOTS = 30  # 20000 + 30 * 400 = 32000, still below 32768

_counter = itertools.count()


def _worker_index() -> int:
    worker = os.environ.get("PYTEST_XDIST_WORKER", "gw0")
    digits = worker[2:] if worker.startswith("gw") else ""
    return int(digits) % WORKER_SLOTS if digits.isdigit() else 0


def worker_port_block() -> range:
    start = PORT_BASE + _worker_index() * PORTS_PER_WORKER
    return range(start, start + PORTS_PER_WORKER)


def free_port() -> int:
    """Return a currently bindable 127.0.0.1 port from this worker's block."""
    block = worker_port_block()
    for _ in range(len(block)):
        port = block[next(_counter) % len(block)]
        with socket.socket() as probe:
            try:
                probe.bind(("127.0.0.1", port))
            except OSError:
                continue
        return port
    raise RuntimeError("no free loopback port in this worker's block")
