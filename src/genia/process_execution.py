"""Experimental `execution.process(capability, request)` composition boundary.

Implements the approved contract's public operation
(`docs/design/execution-process-contract.md`) by composing the opaque
capability (`genia.process_capability`) with the narrow Python transport
(`genia.process_transport`): validation and misuse detection, protected-
value rejection (reusing R10's existing machinery -- no new taint logic),
symbolic resolution, and failure normalization into the closed contract
taxonomy. This is the only place a `ProcessTransportFailure` becomes a
Genia-visible `err(...)` Outcome.
"""

from __future__ import annotations

from typing import Any

from .configuration import reject_protected
from .process_capability import GeniaProcessCapability
from .process_transport import OUTPUT_LIMIT_BYTES, ProcessTransportFailure, ProcessTransportResult
from .values import GeniaBytes, GeniaMap, GeniaOptionErr, GeniaOptionSome, GeniaSymbol, symbol

_REQUEST_FIELDS = {"executable", "args", "timeout_ms"}


def _runtime_type_name(value: Any) -> str:
    """Return the Python type name used by local misuse diagnostics, not a value rendering."""

    return type(value).__name__


def _require_capability(capability: Any) -> GeniaProcessCapability:
    """Return the opaque host capability unchanged, or raise TypeError without provider effects."""

    if not isinstance(capability, GeniaProcessCapability):
        raise TypeError(
            "execution.process expected a process capability, "
            f"received {_runtime_type_name(capability)}"
        )
    return capability


def _require_request_map(request: Any) -> GeniaMap:
    """Check that the request is a GeniaMap with the required string-field set.

    Raise TypeError for the wrong map type or string-field set; return the same
    map without validating values. This helper compares string keys only;
    non-string keys do not participate in its field-set check.
    """

    if not isinstance(request, GeniaMap):
        raise TypeError(
            f"execution.process expected a request map, received {_runtime_type_name(request)}"
        )
    fields = {key for key, _value in request.items() if isinstance(key, str)}
    if fields != _REQUEST_FIELDS:
        raise TypeError(
            "execution.process expected a closed request with exactly "
            "'executable', 'args', and 'timeout_ms' keys"
        )
    return request


def _require_executable(value: Any) -> GeniaSymbol:
    """Require a non-empty GeniaSymbol; raise TypeError rather than accept a native path."""

    if not isinstance(value, GeniaSymbol) or not value.name:
        raise TypeError(
            "execution.process expected executable to be a non-empty symbol, "
            f"received {_runtime_type_name(value)}"
        )
    return value


def _require_args(value: Any) -> list[str]:
    """Copy a list of exact strings for argv, rejecting non-strings and NULs.

    TypeError is misuse; empty strings and shell metacharacters remain unchanged.
    No splitting, expansion, encoding, or provider invocation occurs here.
    """

    if not isinstance(value, list):
        raise TypeError(
            f"execution.process expected args to be a list, received {_runtime_type_name(value)}"
        )
    result: list[str] = []
    for element in value:
        if not isinstance(element, str):
            raise TypeError(
                "execution.process expected each args element to be a string, "
                f"received {_runtime_type_name(element)}"
            )
        if "\x00" in element:
            raise TypeError("execution.process expected args elements without NUL bytes")
        result.append(element)
    return result


def _require_timeout_ms(value: Any) -> int:
    """Require an integer in 1..300000 milliseconds; reject booleans with TypeError."""

    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(
            f"execution.process expected an integer timeout_ms, received {_runtime_type_name(value)}"
        )
    if not (1 <= value <= 300000):
        raise TypeError("execution.process expected timeout_ms in 1..300000")
    return value


def _to_process_result(outcome: ProcessTransportResult) -> GeniaMap:
    """Build the closed result map with exit_code and GeniaBytes stdout/stderr.

    Preserve captured bytes without text decoding; a nonzero normal exit is data.
    The transport has already enforced capture limits and normalized failures.
    """

    return (
        GeniaMap()
        .put("exit_code", outcome.exit_code)
        .put("stdout", GeniaBytes(outcome.stdout))
        .put("stderr", GeniaBytes(outcome.stderr))
    )


def _normalize_transport_failure(
    failure: ProcessTransportFailure, executable: GeniaSymbol, timeout_ms: int
) -> GeniaOptionErr:
    """Translate transport kinds to closed err reasons and context maps.

    Launch exposes only the requested symbol, timeout only the validated timeout,
    and output-limit only the fixed byte limit. Provider and unknown kinds use
    the execute-operation catch-all; native details and partial output are omitted.
    """

    if failure.kind == "launch":
        return GeniaOptionErr("process-launch-failure", GeniaMap().put("executable", executable))
    if failure.kind == "timeout":
        return GeniaOptionErr("process-timeout", GeniaMap().put("timeout_ms", timeout_ms))
    if failure.kind == "output-limit":
        return GeniaOptionErr(
            "process-output-limit", GeniaMap().put("limit_bytes", OUTPUT_LIMIT_BYTES)
        )
    # "provider" and anything unrecognized share the approved catch-all row
    # (contract §12): no new reason is invented for a native condition that
    # does not fit an existing one.
    return GeniaOptionErr("process-provider-failure", GeniaMap().put("operation", symbol("execute")))


def perform_process_execution(capability: Any, request: Any, *extra: Any) -> Any:
    """Validate, resolve, authorize, and launch one symbolic process request.

    Reject extra arguments, then validate capability and request shape, scan the
    request recursively for protected values, and validate executable, args,
    timeout_ms in that order. Misuse raises before resolution or provider effects;
    there is no authority argument or declassification sink.

    Unbound symbols return process-executable-unavailable without authorization;
    denied bound symbols return process-unauthorized without launch. Authorized
    targets stay host-private. A transport result becomes some(closed result map),
    including nonzero normal exits; transport failures, launcher exceptions and
    unexpected launcher results become closed err Outcomes without native details.
    Authorization callback exceptions are outside the launcher catch boundary.
    """

    if extra:
        raise TypeError(
            "execution.process takes exactly two arguments: capability and request"
        )

    capability = _require_capability(capability)
    request = _require_request_map(request)
    reject_protected(request, "execution.process")
    executable = _require_executable(request.get("executable"))
    args = _require_args(request.get("args"))
    timeout_ms = _require_timeout_ms(request.get("timeout_ms"))

    symbol_name = executable.name
    if not capability.is_bound(symbol_name):
        return GeniaOptionErr(
            "process-executable-unavailable", GeniaMap().put("executable", executable)
        )
    if not capability.is_authorized(symbol_name):
        return GeniaOptionErr(
            "process-unauthorized",
            GeniaMap().put("operation", symbol("execute")).put("executable", executable),
        )

    target = capability.target_for(symbol_name)

    try:
        outcome = capability.launch(target, args, timeout_ms)
    except Exception:  # noqa: BLE001 - normalized boundary, never re-raised
        return GeniaOptionErr(
            "process-provider-failure", GeniaMap().put("operation", symbol("execute"))
        )

    if isinstance(outcome, ProcessTransportResult):
        return GeniaOptionSome(_to_process_result(outcome))
    if isinstance(outcome, ProcessTransportFailure):
        return _normalize_transport_failure(outcome, executable, timeout_ms)

    # A launcher that returns something outside the closed transport
    # vocabulary is itself a provider-level defect; normalize rather than
    # let an unrecognized shape leak through.
    return GeniaOptionErr(
        "process-provider-failure", GeniaMap().put("operation", symbol("execute"))
    )
