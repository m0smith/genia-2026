"""Dedicated R8 server lifecycle core for the Python reference host.

The descriptor data in this module is inert. Lifecycle work begins only when
``run_server_lifecycle`` is called explicitly with injected operations.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any

from .lifecycle_plan import normalize_lifecycle_plan
from .values import GeniaMap, OPTION_NONE, symbol


def _record(**fields: object) -> GeniaMap:
    record = GeniaMap()
    for key, value in fields.items():
        record = record.put(key, value)
    return record


def _phase(name: str, action: str, scope: str, *, always: bool = False) -> GeniaMap:
    return _record(
        name=symbol(name),
        action=symbol(action),
        scope=symbol(scope),
        always=always,
    )


def server_lifecycle_plan() -> GeniaMap:
    """Return the inert descriptor for the dedicated server lifecycle."""

    return _record(
        name=symbol("server_lifecycle"),
        phases=[
            _phase("startup", "activate_server", "server"),
            _phase("request", "handle_request", "request"),
            _phase("shutdown", "close_server", "server", always=True),
        ],
        cleanup=_record(
            entered_scope_cleanup=True,
            unentered_scope_cleanup=False,
            nested_order=symbol("inner_to_outer"),
            same_scope_order=symbol("reverse_source_order"),
            continue_after_cleanup_failure=True,
            record_multiple_failures=True,
        ),
        failure_policy=_record(
            primary_failure=symbol("first_non_cleanup"),
            cleanup_failure=symbol("recorded_secondary"),
            cleanup_only_status=symbol("failed"),
            normal_failure_continuation=symbol("abort_to_cleanup"),
            preserve_primary_failure=True,
            preserve_cleanup_failures=True,
        ),
        result_policy=_record(
            failure_order=symbol("observed_order"),
            include_phase=True,
            include_scope=True,
            include_role=True,
            include_source_location=True,
        ),
    )


def validate_server_lifecycle() -> GeniaMap:
    """Validate and return the normalized inert server lifecycle descriptor."""

    return _record(plan=normalize_lifecycle_plan(server_lifecycle_plan()))


def run_server_lifecycle(
    application: Any,
    requests: Iterable[Any],
    *,
    activate: Callable[[Any], Any],
    request: Callable[[Any, Any], Any],
    close: Callable[[Any], Any],
) -> GeniaMap:
    """Run the fixed server lifecycle through explicitly injected operations."""

    validate_server_lifecycle()

    try:
        owned_handle = activate(application)
    except Exception as error:
        primary = _failure(error, phase="startup", scope="server")
        return _error_result(primary, cleanup_failures=[])

    primary_failure: GeniaMap | None = None
    cleanup_failures: list[GeniaMap] = []

    for request_value in requests:
        try:
            request(owned_handle, request_value)
        except Exception as error:
            primary_failure = _failure(error, phase="request", scope="request")
            break

    try:
        server_result = close(owned_handle)
    except Exception as error:
        cleanup_failure = _failure(error, phase="shutdown", scope="server")
        cleanup_failures.append(cleanup_failure)
        if primary_failure is None:
            primary_failure = cleanup_failure
        server_result = OPTION_NONE

    if primary_failure is not None:
        return _error_result(primary_failure, cleanup_failures=cleanup_failures)

    return _record(
        status="ok",
        state="stopped",
        phase="shutdown",
        scope="server",
        server=server_result,
        primary_failure=OPTION_NONE,
        cleanup_failures=[],
    )


def _failure(error: Exception, *, phase: str, scope: str) -> GeniaMap:
    failure = _record(
        mode="serve",
        phase=phase,
        scope=scope,
        reason=str(error),
    )
    source_location = getattr(error, "source_location", None)
    if source_location is not None:
        failure = failure.put("source_location", source_location)
    return failure


def _error_result(
    primary_failure: GeniaMap,
    *,
    cleanup_failures: list[GeniaMap],
) -> GeniaMap:
    return _record(
        status="error",
        state="failed",
        phase=primary_failure.get("phase"),
        scope=primary_failure.get("scope"),
        server=OPTION_NONE,
        primary_failure=primary_failure,
        cleanup_failures=cleanup_failures,
    )
