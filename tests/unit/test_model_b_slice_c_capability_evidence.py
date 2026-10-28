"""Slice C host-local capability evidence (issue #1269; test plan R6.E HL-13).

PYTHON REFERENCE HOST ONLY: the Python protocol adapter's capability
advertisement and the generic external-host applicability gate. At RED the
adapter advertised `default_open_functions` as `unsupported`, so every gated
Slice C case was reported `unsupported` *before* any host was invoked (staging
evidence only; an `unsupported` case is never a pass). At GREEN (B9) the staging
is removed: the adapter advertises `default_open_functions` as `supported`
because every one of the 143 Slice C shared cases (55 guards plus 88 gated)
passes through the real adapter, asserted per id below.

The immutable external parity assertion
(`tests/spec/test_python_protocol_adapter_parity_762.py`, `unsupported == 18`)
is intentionally not touched; with the capability supported the gated cases pass
and the unsupported count returns to the 18 Python-host-only fixture/debug cases.
"""

from __future__ import annotations

import sys

import pytest

from hosts.python.protocol_adapter import _python_claimed_capabilities
from tools.spec_runner.capabilities import case_is_applicable
from tools.spec_runner.host_executor import execute_spec_via_host
from tools.spec_runner.loader import discover_specs
from tests.spec.test_model_b_slice_c_red import (
    SLICE_C_ALL_GATED_IDS,
    SLICE_C_CASE_IDS,
    SLICE_C_GUARD_IDS,
)

# The historical 35-name pre-C0 map is kept in the C0 test file; GREEN adds one supported name.
GREEN_CAPABILITY_MAP_NAMES = 36


def _specs():
    """Map every shared spec whose name starts with `model-b-c-` to its loaded spec object, keyed by name."""
    return {s.name: s for s in discover_specs()[0] if s.name.startswith("model-b-c-")}


def test_green_capability_map_advertises_default_open_functions_supported():
    claimed = _python_claimed_capabilities()
    assert len(claimed) == GREEN_CAPABILITY_MAP_NAMES
    assert claimed["default_open_functions"] == "supported"
    assert [k for k, v in claimed.items() if v == "unsupported"] == []
    assert claimed["open_functions"] == "supported" and claimed["multi_file_eval"] == "supported"


def test_every_slice_c_case_is_applicable_to_the_python_host():
    claimed = _python_claimed_capabilities()
    specs = _specs()
    assert len(SLICE_C_CASE_IDS) == 143 and set(SLICE_C_CASE_IDS) == set(specs)
    assert [n for n in SLICE_C_CASE_IDS if not case_is_applicable(tuple(specs[n].requires), claimed)[0]] == []
    gated = [n for n in SLICE_C_ALL_GATED_IDS if "default_open_functions" in specs[n].requires]
    guards = [n for n in SLICE_C_GUARD_IDS if "default_open_functions" in specs[n].requires]
    assert len(gated) == 88 and guards == []


@pytest.mark.slow
@pytest.mark.parametrize("name", SLICE_C_CASE_IDS)
def test_every_slice_c_case_passes_through_the_real_protocol_adapter(name):
    """Per-id GREEN evidence: kind == 'pass' via the real subprocess adapter (never unsupported)."""
    result = execute_spec_via_host(
        _specs()[name],
        [sys.executable, "-m", "hosts.python.protocol_adapter"],
        timeout=120.0,
        host_capabilities=_python_claimed_capabilities(),
    )
    assert result.kind == "pass", (name, result.kind, result.reason)
