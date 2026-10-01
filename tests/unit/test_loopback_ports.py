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


def test_a_port_held_by_another_socket_is_skipped(monkeypatch):
    monkeypatch.setattr(loopback, "_counter", iter(range(1000)))
    block = loopback.worker_port_block()
    with socket.socket() as holder:
        holder.bind(("127.0.0.1", block[0]))
        assert loopback.free_port() == block[1]


def test_non_xdist_runs_use_the_first_block(monkeypatch):
    monkeypatch.delenv("PYTEST_XDIST_WORKER", raising=False)
    assert loopback.worker_port_block()[0] == loopback.PORT_BASE
