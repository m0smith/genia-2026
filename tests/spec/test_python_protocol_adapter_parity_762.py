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

import sys
from pathlib import Path

import pytest

import tools.spec_runner.runner as runner_module

pytestmark = [pytest.mark.spec, pytest.mark.slow]

REPO_ROOT = Path(__file__).resolve().parents[2]
PROTOCOL_ADAPTER_COMMAND = f"{sys.executable} -m hosts.python.protocol_adapter"


def test_full_shared_spec_suite_matches_in_process_path_through_subprocess_protocol(capsys) -> None:
    exit_code = runner_module.main(["--host", PROTOCOL_ADAPTER_COMMAND, "--host-timeout", "30"])
    out = capsys.readouterr().out

    # The in-process default path passes all 644 cases (see
    # `python -m tools.spec_runner`). 18 of those rely on an injected
    # Python-host-only test fixture or --debug-stdio, neither of which is
    # expressible over the generic protocol yet (E16-2); every other case
    # must pass identically through the subprocess protocol path. R17
    # (issue #778) added 3 ordinary eval-category cases (integer-arithmetic
    # and map-order portability evidence); none require an unexpressible
    # fixture, so they pass through the protocol path like any other case.
    assert "Summary: total=644 passed=626 failed=0 unsupported=18 protocol_error=0 crash=0 timeout=0 invalid=0" in out
    assert exit_code == 0
