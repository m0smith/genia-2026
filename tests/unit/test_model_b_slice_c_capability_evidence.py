"""Slice C RED host-local capability evidence (issue #1269; test plan R6.E HL-13).

PYTHON REFERENCE HOST ONLY: the Python protocol adapter's capability
advertisement and the generic external-host applicability gate. At RED the
adapter advertises `default_open_functions` as `unsupported`, so every gated
Slice C case is reported `unsupported` *before* any host is invoked. That is
staging evidence only: an `unsupported` case is never a pass and nothing here
claims Model B behavior is implemented.

The immutable external parity assertion
(`tests/spec/test_python_protocol_adapter_parity_762.py`, `unsupported == 18`)
is intentionally not touched; at RED it fails because the gated cases add 82
unsupported results.
"""

from __future__ import annotations

import sys
from pathlib import Path

from hosts.python.protocol_adapter import _python_claimed_capabilities
from tools.spec_runner.capabilities import case_is_applicable
from tools.spec_runner.host_executor import execute_spec_via_host
from tools.spec_runner.loader import discover_specs
from tests.spec.test_model_b_slice_c_red import SLICE_C_GATED_IDS, SLICE_C_GUARD_IDS

# New RED-phase constant: the historical 35-name pre-C0 map is kept in the C0 test file.
RED_CAPABILITY_MAP_NAMES = 36


def _specs():
    return {s.name: s for s in discover_specs()[0] if s.name.startswith("model-b-c-")}


def test_red_capability_map_advertises_exactly_one_unsupported_new_name():
    claimed = _python_claimed_capabilities()
    assert len(claimed) == RED_CAPABILITY_MAP_NAMES
    assert claimed["default_open_functions"] == "unsupported"
    assert [k for k, v in claimed.items() if v == "unsupported"] == ["default_open_functions"]
    assert claimed["open_functions"] == "supported" and claimed["multi_file_eval"] == "supported"


def test_every_gated_case_is_unsupported_without_invoking_the_host(tmp_path: Path):
    marker_dir = tmp_path / "invocations"
    marker_dir.mkdir()
    host = tmp_path / "witness_host.py"
    host.write_text(
        "import pathlib, sys, uuid\n"
        f"pathlib.Path({str(marker_dir)!r}, uuid.uuid4().hex).write_text('invoked')\n"
        "sys.exit(1)\n",
        encoding="utf-8",
    )
    claimed = _python_claimed_capabilities()
    specs = _specs()
    kinds = []
    for name in SLICE_C_GATED_IDS:
        result = execute_spec_via_host(
            specs[name], [sys.executable, str(host)], timeout=5.0, host_capabilities=claimed
        )
        kinds.append(result.kind)
        assert "default_open_functions" in result.reason, name
    assert len(kinds) == 82 and set(kinds) == {"unsupported"}
    assert list(marker_dir.iterdir()) == []


def test_gated_and_guard_applicability_matches_the_frozen_split():
    claimed = _python_claimed_capabilities()
    specs = _specs()
    gated_unapplicable = [n for n in SLICE_C_GATED_IDS if case_is_applicable(tuple(specs[n].requires), claimed)[0]]
    guards_applicable = [n for n in SLICE_C_GUARD_IDS if case_is_applicable(tuple(specs[n].requires), claimed)[0]]
    assert gated_unapplicable == []
    assert len(guards_applicable) == 55
