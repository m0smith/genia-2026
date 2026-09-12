"""
E16-3 (issue #760) capability advertisement and per-case requirement tests.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

from tools.spec_runner.capabilities import (
    CapabilityDeclarationError,
    case_is_applicable,
    known_capabilities,
    validate_capability_claims,
    validate_case_requirements,
)
from tools.spec_runner.host_executor import execute_spec_via_host
from tools.spec_runner.loader import load_spec
from tools.spec_runner.protocol import fetch_capabilities, validate_envelope

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_ADAPTER_COMMAND = [sys.executable, "-m", "tools.spec_runner.fixtures.protocol_fixture_adapter"]


def _spec(name: str, category: str = "eval", *, source: str = "hello", requires=()):
    from tools.spec_runner.loader import LoadedSpec

    return LoadedSpec(
        name=name,
        category=category,
        source=source,
        stdin="",
        expected_stdout="fixture-stdout:" + source + "\n",
        expected_stderr="",
        expected_exit_code=0,
        expected_ir=None,
        path=Path("spec/eval") / f"{name}.yaml",
        requires=tuple(requires),
    )


# --- capabilities.py -------------------------------------------------------------------------


def test_known_capabilities_includes_required_and_optional() -> None:
    known = known_capabilities()
    assert "parser" in known  # required
    assert "http_server" in known  # optional
    assert "not-a-real-capability" not in known


def test_validate_capability_claims_accepts_known_names() -> None:
    validate_capability_claims({"parser": "supported", "http_server": "unsupported"})


def test_multi_file_eval_is_a_known_independent_capability() -> None:
    assert "multi_file_eval" in known_capabilities()
    validate_capability_claims({
        "open_functions": "supported",
        "multi_file_eval": "unsupported",
    })


def test_validate_capability_claims_rejects_unknown_names() -> None:
    with pytest.raises(CapabilityDeclarationError):
        validate_capability_claims({"not-a-real-capability": "supported"})


def test_validate_case_requirements_rejects_unknown_names() -> None:
    with pytest.raises(CapabilityDeclarationError):
        validate_case_requirements(("not-a-real-capability",))


def test_case_is_applicable_with_no_requires_is_always_true() -> None:
    applicable, reason = case_is_applicable((), {})
    assert applicable is True
    assert reason is None


def test_case_is_applicable_requires_supported() -> None:
    applicable, reason = case_is_applicable(("http_server",), {"http_server": "supported"})
    assert applicable is True


def test_case_is_applicable_requires_unsupported() -> None:
    applicable, reason = case_is_applicable(("http_server",), {"http_server": "unsupported"})
    assert applicable is False
    assert "http_server" in reason


def test_case_is_applicable_requires_partial_does_not_satisfy() -> None:
    applicable, reason = case_is_applicable(("http_server",), {"http_server": "partial"})
    assert applicable is False


def test_case_is_applicable_requires_undeclared_capability() -> None:
    applicable, reason = case_is_applicable(("http_server",), {})
    assert applicable is False


# --- protocol.py: capabilities operation result shape -----------------------------------------


def test_validate_envelope_accepts_valid_capabilities_response() -> None:
    from tools.spec_runner.protocol import CAPABILITIES_CASE_ID, build_capabilities_response

    response = build_capabilities_response({"parser": "supported"}, ["parse", "eval"], "rev-1")
    outcome = validate_envelope(
        json.dumps(response), expected_case_id=CAPABILITIES_CASE_ID, expected_operation="capabilities"
    )
    assert outcome.kind == "ok"
    assert outcome.result["capabilities"] == {"parser": "supported"}


def test_validate_envelope_rejects_capabilities_response_with_bad_status_value() -> None:
    from tools.spec_runner.protocol import CAPABILITIES_CASE_ID, build_capabilities_response

    response = build_capabilities_response({"parser": "maybe"}, ["parse"], "rev-1")
    outcome = validate_envelope(
        json.dumps(response), expected_case_id=CAPABILITIES_CASE_ID, expected_operation="capabilities"
    )
    assert outcome.kind == "protocol_error"


def test_validate_envelope_rejects_capabilities_response_with_empty_revision() -> None:
    from tools.spec_runner.protocol import CAPABILITIES_CASE_ID, build_capabilities_response

    response = build_capabilities_response({"parser": "supported"}, ["parse"], "")
    outcome = validate_envelope(
        json.dumps(response), expected_case_id=CAPABILITIES_CASE_ID, expected_operation="capabilities"
    )
    assert outcome.kind == "protocol_error"


def test_validate_envelope_rejects_capabilities_response_with_unknown_operation_entry() -> None:
    from tools.spec_runner.protocol import CAPABILITIES_CASE_ID, build_capabilities_response

    response = build_capabilities_response({"parser": "supported"}, ["definitely-not-an-operation"], "rev-1")
    outcome = validate_envelope(
        json.dumps(response), expected_case_id=CAPABILITIES_CASE_ID, expected_operation="capabilities"
    )
    assert outcome.kind == "protocol_error"


# --- loader.py: per-case requires field ----------------------------------------------------------


def _write_spec(tmp_path: Path, name: str, body: dict) -> Path:
    import yaml

    path = tmp_path / f"{name}.yaml"
    path.write_text(yaml.safe_dump(body), encoding="utf-8")
    return path


def test_load_spec_accepts_valid_requires(tmp_path: Path) -> None:
    path = _write_spec(
        tmp_path,
        "requires-ok",
        {
            "name": "requires-ok",
            "category": "eval",
            "input": {"source": "1"},
            "expected": {"stdout": "1\n", "stderr": "", "exit_code": 0},
            "requires": ["http_server"],
        },
    )
    spec = load_spec(path)
    assert spec.requires == ("http_server",)


def test_load_spec_rejects_unknown_capability_in_requires(tmp_path: Path) -> None:
    path = _write_spec(
        tmp_path,
        "requires-bad",
        {
            "name": "requires-bad",
            "category": "eval",
            "input": {"source": "1"},
            "expected": {"stdout": "1\n", "stderr": "", "exit_code": 0},
            "requires": ["not-a-real-capability"],
        },
    )
    with pytest.raises(ValueError, match="unknown capabilities"):
        load_spec(path)


def test_load_spec_rejects_duplicate_requires(tmp_path: Path) -> None:
    path = _write_spec(
        tmp_path,
        "requires-dup",
        {
            "name": "requires-dup",
            "category": "eval",
            "input": {"source": "1"},
            "expected": {"stdout": "1\n", "stderr": "", "exit_code": 0},
            "requires": ["http_server", "http_server"],
        },
    )
    with pytest.raises(ValueError, match="unique list"):
        load_spec(path)


def test_load_spec_defaults_requires_to_empty_tuple(tmp_path: Path) -> None:
    path = _write_spec(
        tmp_path,
        "requires-absent",
        {
            "name": "requires-absent",
            "category": "eval",
            "input": {"source": "1"},
            "expected": {"stdout": "1\n", "stderr": "", "exit_code": 0},
        },
    )
    spec = load_spec(path)
    assert spec.requires == ()


# --- host_executor.py: requires gating before invoking the adapter -----------------------------


def test_execute_spec_via_host_requires_met_runs_normally() -> None:
    spec = _spec("ok", requires=("http_server",))
    result = execute_spec_via_host(
        spec, FIXTURE_ADAPTER_COMMAND, timeout=5.0, host_capabilities={"http_server": "supported"}
    )
    assert result.kind == "pass"


def test_execute_spec_via_host_requires_unmet_is_unsupported_without_invoking_adapter() -> None:
    spec = _spec("crash", requires=("http_server",))  # would crash the fixture if invoked
    result = execute_spec_via_host(
        spec, FIXTURE_ADAPTER_COMMAND, timeout=5.0, host_capabilities={"http_server": "unsupported"}
    )
    assert result.kind == "unsupported"
    assert "http_server" in result.reason


def test_execute_spec_via_host_requires_without_known_capabilities_is_unsupported() -> None:
    spec = _spec("ok", requires=("http_server",))
    result = execute_spec_via_host(spec, FIXTURE_ADAPTER_COMMAND, timeout=5.0, host_capabilities=None)
    assert result.kind == "unsupported"


# --- end-to-end: fetch_capabilities against the fixture, with a configurable claimed set --------


def test_fetch_capabilities_against_fixture_default_declares_everything_supported() -> None:
    from tools.spec_runner.revision import current_revision

    outcome = fetch_capabilities(FIXTURE_ADAPTER_COMMAND, timeout=5.0, cwd=str(REPO_ROOT))
    assert outcome.kind == "ok"
    assert outcome.result["capabilities"]["parser"] == "supported"
    assert outcome.result["contract_revision"] == current_revision()


def test_fetch_capabilities_against_fixture_honors_override(monkeypatch: pytest.MonkeyPatch) -> None:
    env = dict(os.environ)
    env["FIXTURE_CAPABILITIES_OVERRIDE"] = json.dumps({"http_server": "unsupported"})
    outcome = fetch_capabilities(FIXTURE_ADAPTER_COMMAND, timeout=5.0, cwd=str(REPO_ROOT), env=env)
    assert outcome.kind == "ok"
    assert outcome.result["capabilities"] == {"http_server": "unsupported"}
