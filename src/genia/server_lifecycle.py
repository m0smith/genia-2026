"""Dedicated R8 server lifecycle core for the Python reference host.

The descriptor data in this module is inert. Lifecycle work begins only when
``run_server_lifecycle`` is called explicitly with injected operations.
This fixed coordinator uses trusted host callbacks and a finite, non-failing
request iterable; it neither resolves plan actions nor owns socket transport.
It is independent of the R14 composable lifecycle runtime.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any

from .lifecycle_plan import normalize_lifecycle_plan
from .values import GeniaMap, OPTION_NONE, symbol


def _record(**fields: object) -> GeniaMap:
    """Build an ordinary map with string keys in keyword insertion order.

    Values are retained unchanged, without copying nested mutable objects or
    validating a record schema. Each put returns a new map.
    """

    record = GeniaMap()
    for key, value in fields.items():
        record = record.put(key, value)
    return record


def _phase(name: str, action: str, scope: str, *, always: bool = False) -> GeniaMap:
    """Build inert phase data with symbol-valued name, action and scope.

    ``always`` is stored unchanged; lifecycle-plan normalization validates the
    resulting descriptor later. An action symbol does not resolve a callback.
    """

    return _record(
        name=symbol(name),
        action=symbol(action),
        scope=symbol(scope),
        always=always,
    )


def server_lifecycle_plan() -> GeniaMap:
    """Return fresh inert startup/request/shutdown plan and policy maps.

    Server/request/server scopes and an always-marked shutdown describe the
    fixed consumer. Construction performs no validation, callback invocation
    or IO; these action identifiers are descriptive data, not an action registry.
    """

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
    """Return a map containing the normalized fixed descriptor under ``plan``.

    Normalizer errors propagate before any operation runs. Validation performs
    no activation or cleanup and does not execute the descriptor's actions.
    """

    return _record(plan=normalize_lifecycle_plan(server_lifecycle_plan()))


def run_server_lifecycle(
    application: Any,
    requests: Iterable[Any],
    *,
    activate: Callable[[Any], Any],
    request: Callable[[Any, Any], Any],
    close: Callable[[Any], Any],
) -> GeniaMap:
    """Coordinate trusted activate/request/close callbacks in the Python host.

    The caller supplies validated application data and a finite ordered request
    iterable whose iteration does not raise. Validate the inert plan first,
    then pass application unchanged to activate. Its return establishes the
    owned handle without further validation. Pass that same handle and each
    request value to request in order, ignoring request return values.

    An activate Exception returns a startup/server failure without close. A
    request Exception stops later requests and becomes the primary failure;
    close is then attempted once, also after normal exhaustion. A close
    Exception is recorded in cleanup_failures and becomes primary only when
    no request failure exists. Neither callback is retried. Success returns
    the close value as server; every error result uses OPTION_NONE instead.

    Only callback Exception instances are caught. Iterator errors and
    BaseException escape and can bypass close; this is not a general finally
    guard. Callers must also supply errors safe to stringify and expose, since
    failure construction retains their text and optional source location
    without sanitization. The callbacks own actual IO and resource mechanics;
    the core has no CLI dispatch, socket operations or action resolution.
    """

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
    """Describe a trusted callback error using string-valued serve context.

    Store str(error) as reason and retain its source_location attribute when
    non-None, without validating or copying it. Exception text is not sanitized;
    stringification and attribute-access errors propagate to the caller.
    """

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
    """Build the failed terminal result from an already-selected primary map.

    Phase and scope come from primary_failure; server is OPTION_NONE even when
    close returned a value. Retain the primary map and cleanup list unchanged,
    without sorting, copying or choosing precedence. A shutdown-only failure
    may therefore be both primary and an entry in cleanup_failures.
    """

    return _record(
        status="error",
        state="failed",
        phase=primary_failure.get("phase"),
        scope=primary_failure.get("scope"),
        server=OPTION_NONE,
        primary_failure=primary_failure,
        cleanup_failures=cleanup_failures,
    )
