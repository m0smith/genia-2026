"""
E16-1 (issue #758) protocol envelope and outcome-taxonomy tests.

Covers the wire-level request/response envelope, transport separation,
protocol-version negotiation, and the deterministic outcome taxonomy from
docs/design/r16-multi-host-conformance-infrastructure-contract.md, using
the deterministic fixture adapter as the only "host" under test.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

from tools.spec_runner.protocol import (
    AdapterOutcome,
    ProtocolError,
    build_ok_response,
    build_request,
    build_unsupported_response,
    encode_request,
    run_adapter_request,
    validate_envelope,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_ADAPTER_COMMAND = [sys.executable, "-m", "tools.spec_runner.fixtures.protocol_fixture_adapter"]


def _run(case_id: str, operation: str = "eval", input_payload: dict | None = None, timeout: float = 5.0) -> AdapterOutcome:
    request = build_request(case_id, operation, input_payload or {"source": "hello"})
    return run_adapter_request(FIXTURE_ADAPTER_COMMAND, request, timeout=timeout, cwd=str(REPO_ROOT))


# --- build_request / encode_request -----------------------------------------------------------


def test_build_request_rejects_unsupported_operation() -> None:
    with pytest.raises(ProtocolError):
        build_request("c1", "definitely-not-an-operation", {})


def test_build_request_rejects_empty_case_id() -> None:
    with pytest.raises(ProtocolError):
        build_request("", "eval", {})


def test_build_request_shape() -> None:
    request = build_request("c1", "eval", {"source": "1+1"})
    assert request == {
        "protocol_version": "1",
        "case_id": "c1",
        "operation": "eval",
        "input": {"source": "1+1"},
    }


def test_encode_request_is_utf8_json_with_trailing_newline() -> None:
    request = build_request("c1", "eval", {"source": "x"})
    encoded = encode_request(request)
    assert encoded.endswith(b"\n")
    assert encoded.decode("utf-8").strip() != ""


# --- validate_envelope: golden path -------------------------------------------------------------


def test_validate_envelope_accepts_valid_eval_ok_response() -> None:
    response = build_ok_response("c1", "eval", {"stdout": "hi\n", "stderr": "", "exit_code": 0})
    import json

    outcome = validate_envelope(json.dumps(response), expected_case_id="c1", expected_operation="eval")
    assert outcome.kind == "ok"
    assert outcome.result == {"stdout": "hi\n", "stderr": "", "exit_code": 0}


def test_validate_envelope_accepts_valid_unsupported_response() -> None:
    response = build_unsupported_response("c1", "eval", "no refs capability")
    import json

    outcome = validate_envelope(json.dumps(response), expected_case_id="c1", expected_operation="eval")
    assert outcome.kind == "unsupported"
    assert outcome.reason == "no refs capability"


@pytest.mark.parametrize("operation,result", [
    ("parse", {"kind": "ok", "ast": {"n": 1}}),
    ("parse", {"kind": "error", "type": "SyntaxError", "message": "bad token"}),
    ("lower", {"ir": {"n": 1}}),
    ("cli", {"stdout": "", "stderr": "", "exit_code": 1}),
])
def test_validate_envelope_accepts_every_operation_result_shape(operation: str, result: dict) -> None:
    import json

    response = build_ok_response("c1", operation, result)
    outcome = validate_envelope(json.dumps(response), expected_case_id="c1", expected_operation=operation)
    assert outcome.kind == "ok"
    assert outcome.result == result


# --- validate_envelope: malformed/protocol-error paths --------------------------------------------


def test_validate_envelope_rejects_non_json_stdout() -> None:
    outcome = validate_envelope("not json at all", expected_case_id="c1", expected_operation="eval")
    assert outcome.kind == "protocol_error"
    assert "not valid JSON" in outcome.reason


def test_validate_envelope_rejects_json_that_is_not_an_object() -> None:
    outcome = validate_envelope("[1, 2, 3]", expected_case_id="c1", expected_operation="eval")
    assert outcome.kind == "protocol_error"


def test_validate_envelope_rejects_wrong_protocol_version() -> None:
    import json

    response = build_ok_response("c1", "eval", {"stdout": "", "stderr": "", "exit_code": 0})
    response["protocol_version"] = "99"
    outcome = validate_envelope(json.dumps(response), expected_case_id="c1", expected_operation="eval")
    assert outcome.kind == "protocol_error"
    assert "protocol_version" in outcome.reason


def test_validate_envelope_rejects_case_id_mismatch() -> None:
    import json

    response = build_ok_response("wrong-id", "eval", {"stdout": "", "stderr": "", "exit_code": 0})
    outcome = validate_envelope(json.dumps(response), expected_case_id="c1", expected_operation="eval")
    assert outcome.kind == "protocol_error"
    assert "case_id" in outcome.reason


def test_validate_envelope_rejects_operation_mismatch() -> None:
    import json

    response = build_ok_response("c1", "cli", {"stdout": "", "stderr": "", "exit_code": 0})
    outcome = validate_envelope(json.dumps(response), expected_case_id="c1", expected_operation="eval")
    assert outcome.kind == "protocol_error"
    assert "operation" in outcome.reason


def test_validate_envelope_rejects_invalid_status() -> None:
    import json

    response = build_ok_response("c1", "eval", {"stdout": "", "stderr": "", "exit_code": 0})
    response["status"] = "weird"
    outcome = validate_envelope(json.dumps(response), expected_case_id="c1", expected_operation="eval")
    assert outcome.kind == "protocol_error"


def test_validate_envelope_rejects_ok_status_with_null_result() -> None:
    import json

    response = build_ok_response("c1", "eval", {"stdout": "", "stderr": "", "exit_code": 0})
    response["result"] = None
    outcome = validate_envelope(json.dumps(response), expected_case_id="c1", expected_operation="eval")
    assert outcome.kind == "protocol_error"


def test_validate_envelope_rejects_ok_status_with_wrong_result_shape() -> None:
    import json

    response = build_ok_response("c1", "eval", {"unexpected": "shape"})
    outcome = validate_envelope(json.dumps(response), expected_case_id="c1", expected_operation="eval")
    assert outcome.kind == "protocol_error"


def test_validate_envelope_rejects_unsupported_status_with_non_null_result() -> None:
    import json

    response = build_unsupported_response("c1", "eval", "reason")
    response["result"] = {"stdout": "", "stderr": "", "exit_code": 0}
    outcome = validate_envelope(json.dumps(response), expected_case_id="c1", expected_operation="eval")
    assert outcome.kind == "protocol_error"


def test_validate_envelope_rejects_unsupported_status_with_empty_reason() -> None:
    import json

    response = build_unsupported_response("c1", "eval", "reason")
    response["unsupported_reason"] = ""
    outcome = validate_envelope(json.dumps(response), expected_case_id="c1", expected_operation="eval")
    assert outcome.kind == "protocol_error"


def test_validate_envelope_rejects_missing_key() -> None:
    import json

    response = build_ok_response("c1", "eval", {"stdout": "", "stderr": "", "exit_code": 0})
    del response["unsupported_reason"]
    outcome = validate_envelope(json.dumps(response), expected_case_id="c1", expected_operation="eval")
    assert outcome.kind == "protocol_error"


def test_validate_envelope_rejects_extra_key() -> None:
    import json

    response = build_ok_response("c1", "eval", {"stdout": "", "stderr": "", "exit_code": 0})
    response["debug"] = "nope"
    outcome = validate_envelope(json.dumps(response), expected_case_id="c1", expected_operation="eval")
    assert outcome.kind == "protocol_error"


# --- end-to-end via the deterministic fixture adapter subprocess ---------------------------------


def test_fixture_adapter_ok_round_trip() -> None:
    outcome = _run("ok", operation="eval", input_payload={"source": "hello"})
    assert outcome.kind == "ok"
    assert outcome.result == {"stdout": "fixture-stdout:hello\n", "stderr": "", "exit_code": 0}


def test_fixture_adapter_ok_round_trip_for_every_operation() -> None:
    for operation in ("parse", "lower", "eval", "cli"):
        outcome = _run("ok", operation=operation, input_payload={"source": "x"})
        assert outcome.kind == "ok", operation


def test_fixture_adapter_unsupported() -> None:
    outcome = _run("unsupported")
    assert outcome.kind == "unsupported"
    assert outcome.reason == "fixture: operation not supported"


def test_fixture_adapter_malformed_json_is_protocol_error() -> None:
    outcome = _run("malformed-json")
    assert outcome.kind == "protocol_error"


def test_fixture_adapter_wrong_version_is_protocol_error() -> None:
    outcome = _run("wrong-version")
    assert outcome.kind == "protocol_error"


def test_fixture_adapter_wrong_case_id_is_protocol_error() -> None:
    outcome = _run("wrong-case-id")
    assert outcome.kind == "protocol_error"


def test_fixture_adapter_wrong_operation_is_protocol_error() -> None:
    outcome = _run("wrong-operation")
    assert outcome.kind == "protocol_error"


def test_fixture_adapter_bad_status_is_protocol_error() -> None:
    outcome = _run("bad-status")
    assert outcome.kind == "protocol_error"


def test_fixture_adapter_missing_result_is_protocol_error() -> None:
    outcome = _run("missing-result")
    assert outcome.kind == "protocol_error"


def test_fixture_adapter_extra_key_is_protocol_error() -> None:
    outcome = _run("extra-key")
    assert outcome.kind == "protocol_error"


def test_fixture_adapter_crash_is_crash() -> None:
    outcome = _run("crash")
    assert outcome.kind == "crash"
    assert "3" in outcome.reason


def test_fixture_adapter_hang_is_timeout() -> None:
    outcome = _run("hang", timeout=0.5)
    assert outcome.kind == "timeout"


def test_fixture_adapter_stdout_leak_is_protocol_error_not_a_false_pass() -> None:
    """Proves the channel-ownership rule: an adapter that lets evaluated-program
    or any other non-envelope text reach its own stdout is caught as a
    PROTOCOL ERROR by the runner, never silently accepted as ok."""
    outcome = _run("stdout-leak")
    assert outcome.kind == "protocol_error"
    assert "leaked evaluated-program output" in outcome.stdout_raw


def test_adapter_own_stderr_never_affects_classification() -> None:
    """stderr_raw is captured for diagnostics only; it must never change the
    outcome kind. The fixture adapter never writes to its own stderr, so
    this asserts the diagnostic channel stays empty on the golden path."""
    outcome = _run("ok")
    assert outcome.kind == "ok"
    assert outcome.stderr_raw == ""
