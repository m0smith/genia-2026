"""Tests for the collision-free loopback port allocator (tests/fixtures/loopback.py)."""

import socket

import pytest

from tests.fixtures import loopback

pytestmark = pytest.mark.loopback

EPHEMERAL_FLOOR = 32768  # Linux default ip_local_port_range start; BSD/macOS is 49152


def test_ports_are_below_the_ephemeral_range():
    for _ in range(20):
        assert loopback.free_port() < EPHEMERAL_FLOOR


def test_worker_blocks_are_disjoint_and_below_the_ephemeral_range(monkeypatch):
    blocks = []
    for index in range(loopback.WORKER_SLOTS):
        monkeypatch.setenv("PYTEST_XDIST_WORKER", f"gw{index}")
        blocks.append(set(loopback.worker_port_block()))
    seen = set()
    for block in blocks:
        assert not (block & seen)
        assert max(block) < EPHEMERAL_FLOOR
        seen |= block


def test_consecutive_ports_differ_so_a_test_can_take_several():
    ports = [loopback.free_port() for _ in range(10)]
    assert len(set(ports)) == 10


def _bindable(port):
    with socket.socket() as probe:
        try:
            probe.bind(("127.0.0.1", port))
        except OSError:
            return False
    return True


def test_a_port_held_by_another_socket_is_skipped(monkeypatch):
    # Do not assume the block's first port is free: on a shared host (a CI runner)
    # an unrelated service may already hold it. Hold the first bindable port, then
    # expect the allocator to return the next bindable one.
    monkeypatch.setattr(loopback, "_counter", iter(range(1000)))
    free = [port for port in loopback.worker_port_block() if _bindable(port)]
    assert len(free) >= 2, "worker port block has fewer than two bindable ports"
    with socket.socket() as holder:
        holder.bind(("127.0.0.1", free[0]))
        assert loopback.free_port() == free[1]


def test_non_xdist_runs_use_the_first_block(monkeypatch):
    monkeypatch.delenv("PYTEST_XDIST_WORKER", raising=False)
    assert loopback.worker_port_block()[0] == loopback.PORT_BASE
