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

    # The in-process default path passes all 703 cases (see
    # `python -m tools.spec_runner`). 18 of those rely on an injected
    # Python-host-only test fixture or --debug-stdio, neither of which is
    # expressible over the generic protocol yet (E16-2); every other case
    # must pass identically through the subprocess protocol path. R17
    # (issue #778) added 3 ordinary eval-category cases (integer-arithmetic
    # and map-order portability evidence). R18 added 7 ordinary eval-category
    # cases (issue #791, portable value-equality evidence), 6 more
    # (issue #792, map equality and legal-key evidence: 3 eval, 3 error),
    # 3 more (issue #793, identity and protected equality evidence),
    # 4 more (issue #794, equality-like surface agreement: 3 eval, 1 error),
    # and 4 more (issue #795, multi-host conformance hardening). R19 E19-1
    # (issue #820) added 6 more ordinary eval-category cases (Unicode/UTF-8
    # portability evidence: byte-length widths, encode/decode roundtrip, and
    # deterministic debug escaping). R20 (E20-2/E20-4) added 21 more cases
    # (9 parse, 5 ir, 4 eval, 3 error) covering open-function syntax, Core
    # IR, local dispatch, and diagnostics, each declaring `requires:
    # [open_functions]`; the Python reference host declares that capability
    # supported, so all 21 run and pass through the protocol path too.
    # None require an unexpressible fixture, so they pass through the protocol
    # path like any other case. `test_r18_conformance_protocol_evidence_795.py`
    # additionally asserts that every R18 case specifically is executed rather
    # than reported unsupported.
    # Issue #836 adds 8 portable R20 multi-file eval/error cases. They are
    # expressible over the protocol and require the supported open_functions
    # capability, so both total and passed increase by exactly 8.
    assert "Summary: total=703 passed=685 failed=0 unsupported=18 protocol_error=0 crash=0 timeout=0 invalid=0" in out
    assert exit_code == 0
