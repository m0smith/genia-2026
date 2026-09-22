"""
E16-5 (issue #762) proof: the Python reference host, run through the
generic E16-1 subprocess protocol via hosts/python/protocol_adapter.py,
produces the same normalized pass/fail outcomes as the existing in-process
path for every currently applicable shared spec case. This is the real
acceptance proof (not the deterministic fixture): actual Genia evaluation,
through two full subprocess hops per eval/cli case (the protocol adapter,
which itself spawns the interpreter subprocess exactly as the in-process
path already does), so it is marked slow.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

import tools.spec_runner.runner as runner_module

pytestmark = [pytest.mark.spec, pytest.mark.slow, pytest.mark.full_conformance]

REPO_ROOT = Path(__file__).resolve().parents[2]
PROTOCOL_ADAPTER_COMMAND = f"{sys.executable} -m hosts.python.protocol_adapter"


def test_full_shared_spec_suite_matches_in_process_path_through_subprocess_protocol(capsys) -> None:
    exit_code = runner_module.main(["--host", PROTOCOL_ADAPTER_COMMAND, "--host-timeout", "30"])
    out = capsys.readouterr().out

    # E16-2 leaves 18 Python-host-only fixture/debug cases unsupported over
    # the generic protocol; every other discovered case must pass.
    summary = re.search(
        r"Summary: total=(?P<total>\d+) passed=(?P<passed>\d+) "
        r"failed=(?P<failed>\d+) unsupported=(?P<unsupported>\d+) "
        r"protocol_error=(?P<protocol_error>\d+) crash=(?P<crash>\d+) "
        r"timeout=(?P<timeout>\d+) invalid=(?P<invalid>\d+)",
        out,
    )
    assert summary is not None
    counts = {name: int(value) for name, value in summary.groupdict().items()}
    assert counts["unsupported"] == 18
    assert counts["passed"] == counts["total"] - counts["unsupported"]
    assert counts["failed"] == 0
    assert counts["protocol_error"] == 0
    assert counts["crash"] == 0
    assert counts["timeout"] == 0
    assert counts["invalid"] == 0
    assert exit_code == 0
