"""
E16-1 versioned host-adapter protocol.

Implements the wire-level request/response envelope, transport separation,
protocol-version negotiation, and deterministic outcome taxonomy approved in
``docs/design/r16-multi-host-conformance-infrastructure-contract.md``
(issue #757) for issue #758. E16-3 (issue #760) adds the ``capabilities``
operation and its result shape.

This module is host-neutral: it knows nothing about the Python reference
host or any other host implementation. It only knows the wire contract.
It validates the *shape* of a capabilities response only (correct types,
a known status enum, a non-empty revision string); whether a claimed
capability name is one genia-2026 actually defines, and how case
selection uses claims, is E16-3 policy layered on top in
``tools/spec_runner/host_executor.py`` and
``tools/spec_runner/capabilities.py``.

Wiring this module into ``tools/spec_runner``'s case execution is E16-2
(issue #759); this module is usable standalone.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import subprocess
from typing import Any, Mapping, Sequence

PROTOCOL_VERSION = "1"
SUPPORTED_PROTOCOL_VERSIONS = frozenset({PROTOCOL_VERSION})

OPERATIONS = frozenset({"parse", "lower", "eval", "cli", "capabilities"})
CAPABILITY_STATUSES = frozenset({"supported", "partial", "unsupported"})
CAPABILITIES_CASE_ID = "__capabilities__"

_REQUEST_KEYS = frozenset({"protocol_version", "case_id", "operation", "input"})
_RESPONSE_KEYS = frozenset(
    {"protocol_version", "case_id", "operation", "status", "result", "unsupported_reason"}
)
_STATUSES = frozenset({"ok", "unsupported"})

OUTCOME_KINDS = ("ok", "unsupported", "protocol_error", "crash", "timeout")


class ProtocolError(ValueError):
    """Raised only for programmer errors building a request (not adapter output)."""


@dataclass(frozen=True)
class AdapterOutcome:
    """The runner-derived classification of one adapter invocation.

    ``kind`` is exactly one of ``OUTCOME_KINDS``. Only the runner ever
    produces ``protocol_error``, ``crash``, or ``timeout`` — an adapter can
    never self-report those; it can only ever return ``ok`` or
    ``unsupported`` inside a valid envelope (see ``validate_envelope``).
    """

    kind: str
    result: Mapping[str, Any] | None = None
    reason: str | None = None
    stdout_raw: str = ""
    stderr_raw: str = ""

    def __post_init__(self) -> None:
        if self.kind not in OUTCOME_KINDS:
            raise ProtocolError(f"invalid AdapterOutcome kind: {self.kind!r}")


def build_request(case_id: str, operation: str, input_payload: Mapping[str, Any]) -> dict:
    """Build a protocol request envelope (runner side, not adapter side)."""
    if not isinstance(case_id, str) or not case_id:
        raise ProtocolError("case_id must be a non-empty string")
    if operation not in OPERATIONS:
        raise ProtocolError(f"unsupported operation: {operation!r}")
    if not isinstance(input_payload, Mapping):
        raise ProtocolError("input must be a mapping")
    return {
        "protocol_version": PROTOCOL_VERSION,
        "case_id": case_id,
        "operation": operation,
        "input": dict(input_payload),
    }


def encode_request(request: Mapping[str, Any]) -> bytes:
    """Serialize a request envelope as UTF-8 JSON plus a trailing newline."""
    return (json.dumps(request, sort_keys=True) + "\n").encode("utf-8")


def decode_request(raw: bytes) -> dict:
    """Adapter-side helper: parse one request envelope from raw stdin bytes."""
    payload = json.loads(raw.decode("utf-8"))
    if not isinstance(payload, dict) or set(payload.keys()) != _REQUEST_KEYS:
        raise ProtocolError("malformed request envelope")
    return payload


def _result_shape_ok(operation: str, result: Any) -> bool:
    if not isinstance(result, dict):
        return False
    if operation == "parse":
        if set(result.keys()) == {"kind", "ast"} and result.get("kind") == "ok":
            return True
        if set(result.keys()) == {"kind", "type", "message"} and result.get("kind") == "error":
            return isinstance(result.get("type"), str) and isinstance(result.get("message"), str)
        return False
    if operation == "lower":
        return set(result.keys()) == {"ir"}
    if operation in ("eval", "cli"):
        if set(result.keys()) != {"stdout", "stderr", "exit_code"}:
            return False
        return (
            isinstance(result.get("stdout"), str)
            and isinstance(result.get("stderr"), str)
            and isinstance(result.get("exit_code"), int)
            and not isinstance(result.get("exit_code"), bool)
        )
    if operation == "capabilities":
        if set(result.keys()) != {"capabilities", "operations", "contract_revision", "protocol_version"}:
            return False
        capabilities = result.get("capabilities")
        if not isinstance(capabilities, dict) or not all(
            isinstance(name, str) and isinstance(status, str) and status in CAPABILITY_STATUSES
            for name, status in capabilities.items()
        ):
            return False
        operations = result.get("operations")
        non_capabilities_operations = OPERATIONS - {"capabilities"}
        if not isinstance(operations, list) or not all(
            isinstance(op, str) and op in non_capabilities_operations for op in operations
        ):
            return False
        if len(set(operations)) != len(operations):
            return False
        contract_revision = result.get("contract_revision")
        if not isinstance(contract_revision, str) or not contract_revision:
            return False
        return result.get("protocol_version") in SUPPORTED_PROTOCOL_VERSIONS
    return False


def validate_envelope(raw_stdout: str, *, expected_case_id: str, expected_operation: str) -> AdapterOutcome:
    """Classify one adapter response against the E16-1 envelope contract.

    Never returns ``crash`` or ``timeout``; those are process-level facts
    the caller (``run_adapter_request``) determines before this function is
    reached.
    """
    text = raw_stdout.strip()
    try:
        envelope = json.loads(text)
    except json.JSONDecodeError:
        return AdapterOutcome(kind="protocol_error", reason="stdout is not valid JSON", stdout_raw=raw_stdout)

    if not isinstance(envelope, dict):
        return AdapterOutcome(kind="protocol_error", reason="stdout JSON is not an object", stdout_raw=raw_stdout)

    if set(envelope.keys()) != _RESPONSE_KEYS:
        return AdapterOutcome(
            kind="protocol_error",
            reason=f"response envelope has wrong key set: {sorted(envelope.keys())}",
            stdout_raw=raw_stdout,
        )

    protocol_version = envelope.get("protocol_version")
    if protocol_version not in SUPPORTED_PROTOCOL_VERSIONS:
        return AdapterOutcome(
            kind="protocol_error",
            reason=f"unsupported protocol_version: {protocol_version!r}",
            stdout_raw=raw_stdout,
        )

    if envelope.get("case_id") != expected_case_id:
        return AdapterOutcome(
            kind="protocol_error",
            reason=f"case_id mismatch: expected {expected_case_id!r}, got {envelope.get('case_id')!r}",
            stdout_raw=raw_stdout,
        )

    if envelope.get("operation") != expected_operation:
        return AdapterOutcome(
            kind="protocol_error",
            reason=f"operation mismatch: expected {expected_operation!r}, got {envelope.get('operation')!r}",
            stdout_raw=raw_stdout,
        )

    status = envelope.get("status")
    if status not in _STATUSES:
        return AdapterOutcome(kind="protocol_error", reason=f"invalid status: {status!r}", stdout_raw=raw_stdout)

    result = envelope.get("result")
    unsupported_reason = envelope.get("unsupported_reason")

    if status == "ok":
        if unsupported_reason is not None:
            return AdapterOutcome(
                kind="protocol_error",
                reason="unsupported_reason must be null when status is ok",
                stdout_raw=raw_stdout,
            )
        if not _result_shape_ok(expected_operation, result):
            return AdapterOutcome(
                kind="protocol_error",
                reason=f"result does not match the {expected_operation} shape",
                stdout_raw=raw_stdout,
            )
        return AdapterOutcome(kind="ok", result=result, stdout_raw=raw_stdout)

    # status == "unsupported"
    if result is not None:
        return AdapterOutcome(
            kind="protocol_error",
            reason="result must be null when status is unsupported",
            stdout_raw=raw_stdout,
        )
    if not isinstance(unsupported_reason, str) or not unsupported_reason:
        return AdapterOutcome(
            kind="protocol_error",
            reason="unsupported_reason must be a non-empty string when status is unsupported",
            stdout_raw=raw_stdout,
        )
    return AdapterOutcome(kind="unsupported", reason=unsupported_reason, stdout_raw=raw_stdout)


def run_adapter_request(
    command: Sequence[str],
    request: Mapping[str, Any],
    *,
    timeout: float,
    cwd: str | None = None,
    env: Mapping[str, str] | None = None,
) -> AdapterOutcome:
    """Spawn one adapter-process invocation per the E16-1 transport contract.

    Exactly one process is spawned per request. The adapter process's own
    stdout is read in full and classified by ``validate_envelope``; its own
    stderr is captured only for diagnostics (``stderr_raw``) and never
    affects classification. A nonzero exit is ``crash``; exceeding
    ``timeout`` is ``timeout`` (the process is killed).
    """
    payload = encode_request(request)
    try:
        completed = subprocess.run(
            list(command),
            input=payload,
            capture_output=True,
            timeout=timeout,
            cwd=cwd,
            env=dict(env) if env is not None else None,
        )
    except subprocess.TimeoutExpired as exc:
        return AdapterOutcome(
            kind="timeout",
            reason=f"adapter exceeded {timeout}s timeout",
            stdout_raw=(exc.stdout or b"").decode("utf-8", errors="replace"),
            stderr_raw=(exc.stderr or b"").decode("utf-8", errors="replace"),
        )

    stdout_raw = completed.stdout.decode("utf-8", errors="replace")
    stderr_raw = completed.stderr.decode("utf-8", errors="replace")

    if completed.returncode != 0:
        return AdapterOutcome(
            kind="crash",
            reason=f"adapter exited with code {completed.returncode}",
            stdout_raw=stdout_raw,
            stderr_raw=stderr_raw,
        )

    outcome = validate_envelope(
        stdout_raw,
        expected_case_id=request["case_id"],
        expected_operation=request["operation"],
    )
    return AdapterOutcome(
        kind=outcome.kind,
        result=outcome.result,
        reason=outcome.reason,
        stdout_raw=stdout_raw,
        stderr_raw=stderr_raw,
    )


def fetch_capabilities(
    command: Sequence[str],
    *,
    timeout: float,
    cwd: str | None = None,
    env: Mapping[str, str] | None = None,
) -> AdapterOutcome:
    """Send one ``capabilities`` request to an adapter command and classify
    the response. Uses the fixed sentinel ``CAPABILITIES_CASE_ID`` since a
    capabilities query is not tied to any particular spec case."""
    request = build_request(CAPABILITIES_CASE_ID, "capabilities", {})
    return run_adapter_request(command, request, timeout=timeout, cwd=cwd, env=env)


def build_capabilities_response(
    capabilities: Mapping[str, str],
    operations: Sequence[str],
    contract_revision: str,
) -> dict:
    """Adapter-side helper: build a valid ``capabilities`` ok response."""
    return build_ok_response(
        CAPABILITIES_CASE_ID,
        "capabilities",
        {
            "capabilities": dict(capabilities),
            "operations": list(operations),
            "contract_revision": contract_revision,
            "protocol_version": PROTOCOL_VERSION,
        },
    )


def build_ok_response(case_id: str, operation: str, result: Mapping[str, Any]) -> dict:
    """Adapter-side helper: build a valid ``ok`` response envelope."""
    return {
        "protocol_version": PROTOCOL_VERSION,
        "case_id": case_id,
        "operation": operation,
        "status": "ok",
        "result": dict(result),
        "unsupported_reason": None,
    }


def build_unsupported_response(case_id: str, operation: str, reason: str) -> dict:
    """Adapter-side helper: build a valid ``unsupported`` response envelope."""
    return {
        "protocol_version": PROTOCOL_VERSION,
        "case_id": case_id,
        "operation": operation,
        "status": "unsupported",
        "result": None,
        "unsupported_reason": reason,
    }


def encode_response(response: Mapping[str, Any]) -> bytes:
    """Adapter-side helper: serialize a response envelope for stdout."""
    return (json.dumps(response, sort_keys=True) + "\n").encode("utf-8")
