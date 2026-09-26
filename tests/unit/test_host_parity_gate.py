"""
Host parity CI gate tests (pre-flight issue #1018).

These construct fabricated E16-7 evidence documents directly -- they do not
require a real C++ build, so the gate's own logic is fully verifiable in
this repository.
"""
from __future__ import annotations

import json

import pytest

from tools.spec_runner.host_parity_gate import (
    HostParityGateError,
    KNOWN_GAP,
    PARITY_OK,
    STALE_GAP,
    UNDOCUMENTED_GAP,
    check_parity,
    format_report,
    load_known_gaps,
    main,
    optional_capabilities,
)


def _counts(**overrides) -> dict:
    base = dict(pass_=0, fail=0, unsupported=0, protocol_error=0, crash=0, timeout=0, invalid=0)
    base.update(overrides)
    base["pass"] = base.pop("pass_")
    return base


def _all_supported_except(overrides: dict[str, str] | None = None) -> dict[str, str]:
    """Every optional capability declared 'supported' except the given
    overrides -- keeps a test's fixture focused on the one capability under
    test instead of tripping UNDOCUMENTED_GAP on every other capability."""
    capabilities = {name: "supported" for name in optional_capabilities()}
    capabilities.update(overrides or {})
    return capabilities


def _evidence(*, capabilities: dict[str, str] | None = None, **count_overrides) -> dict:
    return {
        "protocol_version": "1",
        "contract_revision": {"declared": "a" * 40, "checkout": "a" * 40, "classification": "current"},
        "capabilities": capabilities or {},
        "capability_operations": ["parse", "lower", "eval", "cli"],
        "total_cases": 10,
        "applicable_cases": 10,
        "counts": _counts(**count_overrides),
    }


_ONE_GAP_ENTRY = {
    "capability": "cli_pipe_mode",
    "reason": "not implemented yet",
    "tracking_issue": "m0smith/genia-2026#1018",
    "affected_host": "cpp",
    "affected_tests": ["spec/cli/**"],
    "removal_condition": "remove when supported",
}

_ONE_GAP = {
    "cli_pipe_mode": _ONE_GAP_ENTRY,
}


# --- check_parity: capability classification ------------------------------------------------


def test_documented_unsupported_capability_is_known_gap() -> None:
    python_evidence = _evidence(pass_=10)
    cpp_evidence = _evidence(capabilities=_all_supported_except({"cli_pipe_mode": "unsupported"}), pass_=10)
    report = check_parity(python_evidence=python_evidence, cpp_evidence=cpp_evidence, known_gaps=_ONE_GAP)
    result = next(r for r in report.capability_results if r.capability == "cli_pipe_mode")
    assert result.status == KNOWN_GAP
    assert report.ok


def test_undocumented_unsupported_capability_fails_gate() -> None:
    python_evidence = _evidence(pass_=10)
    cpp_evidence = _evidence(capabilities={"cli_pipe_mode": "unsupported"}, pass_=10)
    report = check_parity(python_evidence=python_evidence, cpp_evidence=cpp_evidence, known_gaps={})
    result = next(r for r in report.capability_results if r.capability == "cli_pipe_mode")
    assert result.status == UNDOCUMENTED_GAP
    assert not report.ok


def test_undeclared_capability_defaults_to_unsupported_and_is_gated() -> None:
    # cpp evidence simply omits the capability entirely -- must not be
    # silently treated as parity.
    python_evidence = _evidence(pass_=10)
    cpp_evidence = _evidence(capabilities={}, pass_=10)
    report = check_parity(python_evidence=python_evidence, cpp_evidence=cpp_evidence, known_gaps={})
    result = next(r for r in report.capability_results if r.capability == "cli_pipe_mode")
    assert result.status == UNDOCUMENTED_GAP
    assert not report.ok


def test_closed_gap_now_supported_is_stale_and_fails_gate() -> None:
    python_evidence = _evidence(pass_=10)
    cpp_evidence = _evidence(capabilities={"cli_pipe_mode": "supported"}, pass_=10)
    report = check_parity(python_evidence=python_evidence, cpp_evidence=cpp_evidence, known_gaps=_ONE_GAP)
    result = next(r for r in report.capability_results if r.capability == "cli_pipe_mode")
    assert result.status == STALE_GAP
    assert not report.ok


def test_supported_capability_with_no_manifest_entry_is_parity_ok() -> None:
    python_evidence = _evidence(pass_=10)
    cpp_evidence = _evidence(capabilities=_all_supported_except(), pass_=10)
    report = check_parity(python_evidence=python_evidence, cpp_evidence=cpp_evidence, known_gaps={})
    result = next(r for r in report.capability_results if r.capability == "cli_pipe_mode")
    assert result.status == PARITY_OK
    assert report.ok


def test_partial_capability_treated_like_unsupported_for_gap_matching() -> None:
    python_evidence = _evidence(pass_=10)
    cpp_evidence = _evidence(capabilities=_all_supported_except({"cli_pipe_mode": "partial"}), pass_=10)
    report = check_parity(python_evidence=python_evidence, cpp_evidence=cpp_evidence, known_gaps=_ONE_GAP)
    result = next(r for r in report.capability_results if r.capability == "cli_pipe_mode")
    assert result.status == KNOWN_GAP
    assert report.ok


# --- evidence integrity: never let a real failure hide behind gap logic ---------------------


@pytest.mark.parametrize("field", ["fail", "protocol_error", "crash", "timeout", "invalid"])
def test_nonzero_cpp_failure_count_fails_gate_even_with_full_manifest(field: str) -> None:
    python_evidence = _evidence(pass_=10)
    cpp_evidence = _evidence(capabilities={"cli_pipe_mode": "unsupported"}, pass_=9, **{field: 1})
    report = check_parity(python_evidence=python_evidence, cpp_evidence=cpp_evidence, known_gaps=_ONE_GAP)
    assert not report.ok
    assert any(field in failure for failure in report.evidence_failures)


@pytest.mark.parametrize("field", ["fail", "protocol_error", "crash", "timeout", "invalid"])
def test_nonzero_python_failure_count_fails_gate(field: str) -> None:
    python_evidence = _evidence(pass_=9, **{field: 1})
    cpp_evidence = _evidence(capabilities={}, pass_=10)
    report = check_parity(python_evidence=python_evidence, cpp_evidence=cpp_evidence, known_gaps={})
    assert not report.ok
    assert any(field in failure for failure in report.evidence_failures)


# --- explicit cpp-unavailable path ------------------------------------------------------------


def test_missing_cpp_evidence_without_reason_is_a_tooling_error() -> None:
    with pytest.raises(HostParityGateError, match="cpp_unavailable_reason"):
        check_parity(python_evidence=_evidence(pass_=10), cpp_evidence=None, known_gaps={})


def test_missing_cpp_evidence_with_reason_still_checks_python_side() -> None:
    report = check_parity(
        python_evidence=_evidence(pass_=10),
        cpp_evidence=None,
        known_gaps={},
        cpp_unavailable_reason="no C++ toolchain in this sandbox",
    )
    assert report.ok
    assert report.cpp_unavailable_reason == "no C++ toolchain in this sandbox"
    assert report.capability_results == ()
    assert "C++ PARITY NOT EVALUATED" in format_report(report)


def test_missing_cpp_evidence_with_reason_still_fails_on_python_regression() -> None:
    report = check_parity(
        python_evidence=_evidence(pass_=9, fail=1),
        cpp_evidence=None,
        known_gaps={},
        cpp_unavailable_reason="no C++ toolchain in this sandbox",
    )
    assert not report.ok


# --- known-gaps manifest loading --------------------------------------------------------------


def test_load_known_gaps_rejects_unknown_capability_name(tmp_path) -> None:
    manifest_path = tmp_path / "known_host_gaps.json"
    manifest_path.write_text(
        json.dumps({"gaps": [dict(_ONE_GAP_ENTRY, capability="not_a_real_capability")]}),
        encoding="utf-8",
    )
    with pytest.raises(HostParityGateError, match="unknown optional capability"):
        load_known_gaps(manifest_path)


def test_load_known_gaps_rejects_missing_tracking_issue(tmp_path) -> None:
    manifest_path = tmp_path / "known_host_gaps.json"
    gap = dict(_ONE_GAP_ENTRY)
    del gap["tracking_issue"]
    manifest_path.write_text(json.dumps({"gaps": [gap]}), encoding="utf-8")
    with pytest.raises(HostParityGateError, match="tracking_issue"):
        load_known_gaps(manifest_path)


def test_load_known_gaps_rejects_non_issue_tracking(tmp_path) -> None:
    manifest_path = tmp_path / "known_host_gaps.json"
    manifest_path.write_text(
        json.dumps({"gaps": [dict(_ONE_GAP_ENTRY, tracking_issue="docs/releases/R24.md")]}),
        encoding="utf-8",
    )
    with pytest.raises(HostParityGateError, match="GitHub issue reference"):
        load_known_gaps(manifest_path)


def test_load_known_gaps_rejects_duplicate_capability_entries(tmp_path) -> None:
    manifest_path = tmp_path / "known_host_gaps.json"
    manifest_path.write_text(
        json.dumps(
            {
                "gaps": [
                    _ONE_GAP_ENTRY,
                    dict(_ONE_GAP_ENTRY, reason="x2"),
                ]
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(HostParityGateError, match="twice"):
        load_known_gaps(manifest_path)


def test_load_known_gaps_loads_the_real_checked_in_manifest() -> None:
    gaps = load_known_gaps()
    assert "cli_pipe_mode" in gaps
    assert gaps["cli_pipe_mode"]["reason"]


# --- CLI entry point ---------------------------------------------------------------------------


def test_main_exits_zero_on_full_parity(tmp_path) -> None:
    python_path = tmp_path / "python.json"
    cpp_path = tmp_path / "cpp.json"
    gaps_path = tmp_path / "gaps.json"
    python_path.write_text(json.dumps(_evidence(pass_=10)), encoding="utf-8")
    cpp_path.write_text(
        json.dumps(_evidence(capabilities=_all_supported_except({"cli_pipe_mode": "unsupported"}), pass_=10)),
        encoding="utf-8",
    )
    gaps_path.write_text(json.dumps({"gaps": [_ONE_GAP["cli_pipe_mode"]]}), encoding="utf-8")

    exit_code = main(
        [
            "--python-evidence",
            str(python_path),
            "--cpp-evidence",
            str(cpp_path),
            "--known-gaps",
            str(gaps_path),
        ]
    )
    assert exit_code == 0


def test_main_exits_nonzero_on_undocumented_gap(tmp_path) -> None:
    python_path = tmp_path / "python.json"
    cpp_path = tmp_path / "cpp.json"
    gaps_path = tmp_path / "gaps.json"
    python_path.write_text(json.dumps(_evidence(pass_=10)), encoding="utf-8")
    cpp_path.write_text(
        json.dumps(_evidence(capabilities={"cli_pipe_mode": "unsupported"}, pass_=10)), encoding="utf-8"
    )
    gaps_path.write_text(json.dumps({"gaps": []}), encoding="utf-8")

    exit_code = main(
        [
            "--python-evidence",
            str(python_path),
            "--cpp-evidence",
            str(cpp_path),
            "--known-gaps",
            str(gaps_path),
        ]
    )
    assert exit_code == 1


def test_main_requires_reason_when_cpp_evidence_omitted(tmp_path) -> None:
    python_path = tmp_path / "python.json"
    python_path.write_text(json.dumps(_evidence(pass_=10)), encoding="utf-8")

    exit_code = main(["--python-evidence", str(python_path)])
    assert exit_code == 2


def test_main_accepts_explicit_cpp_unavailable_reason(tmp_path) -> None:
    python_path = tmp_path / "python.json"
    python_path.write_text(json.dumps(_evidence(pass_=10)), encoding="utf-8")

    exit_code = main(
        [
            "--python-evidence",
            str(python_path),
            "--cpp-unavailable-reason",
            "no C++ toolchain in this sandbox",
        ]
    )
    assert exit_code == 0
