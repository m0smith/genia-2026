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
    return type(value).__name__


def _require_capability(capability: Any) -> GeniaProcessCapability:
    if not isinstance(capability, GeniaProcessCapability):
        raise TypeError(
            "execution.process expected a process capability, "
            f"received {_runtime_type_name(capability)}"
        )
    return capability


def _require_request_map(request: Any) -> GeniaMap:
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
    if not isinstance(value, GeniaSymbol) or not value.name:
        raise TypeError(
            "execution.process expected executable to be a non-empty symbol, "
            f"received {_runtime_type_name(value)}"
        )
    return value


def _require_args(value: Any) -> list[str]:
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
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(
            f"execution.process expected an integer timeout_ms, received {_runtime_type_name(value)}"
        )
    if not (1 <= value <= 300000):
        raise TypeError("execution.process expected timeout_ms in 1..300000")
    return value


def _to_process_result(outcome: ProcessTransportResult) -> GeniaMap:
    return (
        GeniaMap()
        .put("exit_code", outcome.exit_code)
        .put("stdout", GeniaBytes(outcome.stdout))
        .put("stderr", GeniaBytes(outcome.stderr))
    )


def _normalize_transport_failure(
    failure: ProcessTransportFailure, executable: GeniaSymbol, timeout_ms: int
) -> GeniaOptionErr:
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
    """`execution.process(capability, request)`.

    Validation occurs completely -- capability type, request shape,
    `executable`, `args`, `timeout_ms`, and the recursive protected-value
    scan -- with zero provider effects before resolution or launch
    (contract §5/§13). V1 accepts exactly two arguments; there is no
    authority argument and no declassification sink.
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
