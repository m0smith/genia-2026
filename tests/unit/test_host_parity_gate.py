from __future__ import annotations

import pytest

from tools.check_host_parity import ParityError, check_parity


def _evidence(host: str, *, unsupported: int = 1) -> dict:
    capabilities = {"parser": "supported", "shared_spec_runner": "partial"}
    if host == "cpp":
        capabilities["flow_phase_1"] = "unsupported"
    return {
        "contract_revision": {
            "checkout": "abc123",
            "declared": "abc123",
            "classification": "current",
        },
        "capabilities": capabilities,
        "total_cases": 10,
        "counts": {
            "pass": 10 - unsupported,
            "fail": 0,
            "unsupported": unsupported,
            "protocol_error": 0,
            "crash": 0,
            "timeout": 0,
            "invalid": 0,
        },
    }


def _policies() -> dict:
    return {
        "python": {
            "expected_non_supported_capabilities": {"shared_spec_runner": "partial"},
            "unsupported_case_policy": "allowed",
            "unsupported_case_reason": "known protocol limitation",
        },
        "cpp": {
            "expected_non_supported_capabilities": {
                "flow_phase_1": "unsupported",
                "shared_spec_runner": "partial",
            },
            "unsupported_case_policy": "allowed",
            "unsupported_case_reason": "bounded host floor",
        },
    }


def test_parity_pass_is_explicit_about_both_hosts_and_known_gaps() -> None:
    lines = check_parity(_evidence("python"), _evidence("cpp"), _policies())

    assert lines[0].startswith("PYTHON PASS")
    assert any(line.startswith("CPP PASS") for line in lines)
    assert any(line.startswith("PYTHON KNOWN GAP") for line in lines)
    assert any(line.startswith("CPP KNOWN GAP") for line in lines)
    assert lines[-1].startswith("PARITY PASS")


@pytest.mark.parametrize("host", ["python", "cpp"])
def test_any_host_failure_fails_parity(host: str) -> None:
    python = _evidence("python")
    cpp = _evidence("cpp")
    selected = python if host == "python" else cpp
    selected["counts"]["pass"] -= 1
    selected["counts"]["fail"] = 1

    with pytest.raises(ParityError, match=f"{host}=FAIL .*conformance failures"):
        check_parity(python, cpp, _policies())


def test_both_host_failures_are_reported_together() -> None:
    python = _evidence("python")
    cpp = _evidence("cpp")
    for evidence in (python, cpp):
        evidence["counts"]["pass"] -= 1
        evidence["counts"]["fail"] = 1

    with pytest.raises(ParityError) as caught:
        check_parity(python, cpp, _policies())

    assert "python=FAIL" in str(caught.value)
    assert "cpp=FAIL" in str(caught.value)


def test_capability_gap_drift_fails_parity() -> None:
    cpp = _evidence("cpp")
    cpp["capabilities"]["new_gap"] = "unsupported"

    with pytest.raises(ParityError, match="capability gaps differ"):
        check_parity(_evidence("python"), cpp, _policies())


def test_different_case_inventory_fails_parity() -> None:
    cpp = _evidence("cpp")
    cpp["total_cases"] = 9

    with pytest.raises(ParityError, match="same shared inventory"):
        check_parity(_evidence("python"), cpp, _policies())


def test_different_contract_checkout_fails_parity() -> None:
    cpp = _evidence("cpp")
    cpp["contract_revision"]["checkout"] = "different"

    with pytest.raises(ParityError, match="same contract revision"):
        check_parity(_evidence("python"), cpp, _policies())
