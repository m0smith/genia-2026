"""R14 E14-7 outbound HTTP client lifecycle core.

Implements ``web.http_send(operation, authority, timeout_ms)`` per the
approved R14 contract's "Outbound HTTP client lifecycle" section
(``docs/design/r14-composable-lifecycle-contract.md``, issue #624). Composes
four already-implemented, unchanged mechanisms: the E14-1 lifecycle core
(``lifecycle_runtime.py``), the inert ``HttpOperation`` representation
(``http_operation.py``, issue #622), the host transport capability
(``http_transport.py``, issue #623), and R10's ``declassify`` boundary
(``configuration.py``). This module adds no new lifecycle primitive, no new
protected-value mechanism, and no host transport mechanics of its own.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any
import urllib.parse

from .configuration import declassify
from .http_transport import (
    HttpTransport,
    HttpTransportFailure,
    HttpTransportRequest,
    HttpTransportResponse,
    send_http_request,
)
from .lifecycle_runtime import Invoke, lookup_lifecycle_context, run_lifecycle_scope
from .values import (
    GeniaBytes,
    GeniaDeclassificationAuthority,
    GeniaMap,
    GeniaOptionErr,
    GeniaOptionNone,
    GeniaOptionSome,
    GeniaProtected,
    symbol,
)

_OPERATION_FIELDS = {"method", "base_url", "path", "headers", "query", "body"}
_PEER_NAME = "http"


def _require_operation(operation: Any) -> GeniaMap:
    if not isinstance(operation, GeniaMap):
        raise TypeError(
            f"http_send expected an HttpOperation map, received {type(operation).__name__}"
        )
    fields = {key for key, _value in operation.items() if isinstance(key, str)}
    if fields != _OPERATION_FIELDS:
        raise TypeError(
            "http_send expected an HttpOperation with exactly "
            "'method', 'base_url', 'path', 'headers', 'query', and 'body' fields"
        )
    return operation


def _require_authority(authority: Any) -> GeniaDeclassificationAuthority | None:
    if isinstance(authority, GeniaOptionNone):
        return None
    if isinstance(authority, GeniaOptionSome) and isinstance(
        authority.value, GeniaDeclassificationAuthority
    ):
        return authority.value
    raise TypeError(
        "http_send expected authority to be none(...) or some(<declassification "
        f"authority>), received {type(authority).__name__}"
    )


def _require_timeout_ms(timeout_ms: Any) -> int:
    if isinstance(timeout_ms, bool) or not isinstance(timeout_ms, int):
        raise TypeError(
            f"http_send expected an integer timeout_ms, received {type(timeout_ms).__name__}"
        )
    if not (1 <= timeout_ms <= 300000):
        raise TypeError("http_send expected timeout_ms in 1..300000")
    return timeout_ms


def _resolve_headers(
    headers: GeniaMap, authority: GeniaDeclassificationAuthority | None
) -> dict[str, str]:
    resolved: dict[str, str] = {}
    for key, value in headers.items():
        if isinstance(value, GeniaProtected):
            if authority is None:
                raise TypeError(
                    "http_send received a protected header with no authority; "
                    "declassification requires some(authority)"
                )
            resolved[key] = declassify(authority, value)
        else:
            resolved[key] = value
    return resolved


def _quote(value: str) -> str:
    return urllib.parse.quote(value, safe="")


def _build_url(base_url: str, path: str, query: GeniaMap) -> str:
    pairs = sorted(query.items(), key=lambda item: item[0])
    if not pairs:
        return f"{base_url}{path}"
    query_string = "&".join(f"{_quote(key)}={_quote(value)}" for key, value in pairs)
    return f"{base_url}{path}?{query_string}"


def _resolve_body(body: Any, json_encode: Callable[[Any], Any]) -> bytes:
    if isinstance(body, GeniaMap):
        kind = body.get("kind")
        if kind == symbol("text"):
            return body.get("text").encode("utf-8")
        if kind == symbol("json"):
            encoded = json_encode(body.get("value"))
            return encoded.value.encode("utf-8")
    return b""


def _failure_reason(kind: str, timeout_ms: int) -> tuple[str, GeniaMap]:
    if kind == "timeout":
        return "http-timeout", GeniaMap().put("timeout_ms", timeout_ms)
    return "http-transport-failure", GeniaMap().put("kind", symbol(kind))


def _to_http_response_map(response: HttpTransportResponse) -> GeniaMap:
    headers = GeniaMap()
    for key, value in response.headers.items():
        headers = headers.put(key.lower(), value)
    return (
        GeniaMap()
        .put("status", response.status)
        .put("headers", headers)
        .put("body", GeniaBytes(response.body))
    )


def perform_http_send(
    operation: Any,
    authority: Any,
    timeout_ms: Any,
    *,
    json_encode: Callable[[Any], Any],
    invoke: Invoke,
    transport: HttpTransport | None = None,
) -> Any:
    """``web.http_send(operation, authority, timeout_ms)``.

    All misuse validation (operation/authority/timeout_ms shape, and any
    protected-header declassification via the existing ``declassify``) runs
    before any lifecycle scope opens, so a raised ``TypeError`` propagates
    directly to the caller rather than being normalized into an ordinary
    recoverable failure by the internal scope machinery. Only the one
    transport attempt runs inside the internal lifecycle scope; a transport
    failure there is an ordinary recoverable Outcome, never a raise.
    """

    operation = _require_operation(operation)
    resolved_authority = _require_authority(authority)
    timeout_ms = _require_timeout_ms(timeout_ms)

    resolved_headers = _resolve_headers(operation.get("headers"), resolved_authority)
    url = _build_url(operation.get("base_url"), operation.get("path"), operation.get("query"))
    body_bytes = _resolve_body(operation.get("body"), json_encode)
    method_name = operation.get("method").name.upper()

    def _enter(scope: Any) -> Any:
        request = HttpTransportRequest(
            method=method_name,
            url=url,
            headers=resolved_headers,
            body=body_bytes,
            timeout_seconds=timeout_ms / 1000,
        )
        result = send_http_request(request, transport=transport)
        if isinstance(result, HttpTransportResponse):
            return GeniaOptionSome(_to_http_response_map(result))
        assert isinstance(result, HttpTransportFailure)
        reason, context = _failure_reason(result.kind, timeout_ms)
        return GeniaOptionErr(reason, context)

    def _work(scope: Any) -> Any:
        return lookup_lifecycle_context(scope, symbol(_PEER_NAME)).value

    def _exit(scope: Any, summary: Any) -> Any:
        return GeniaOptionSome("nil")

    peers = [GeniaMap().put("name", symbol(_PEER_NAME)).put("enter", _enter).put("exit", _exit)]
    lifecycle_result = run_lifecycle_scope(peers, _work, invoke)

    if lifecycle_result.get("status") == symbol("ok"):
        return GeniaOptionSome(lifecycle_result.get("result").value)
    primary = lifecycle_result.get("primary_failure")
    return GeniaOptionErr(primary.get("reason"), primary.get("context"))
