"""Experimental Python-host outbound HTTP transport capability for R14.

This module has no Genia-visible surface: it is a private host capability
consumed by a later ticket (`web.http_send`, E14-7), not registered as a
Genia builtin. It accepts an already-normalized request (method, absolute
URL, string headers, byte body) and makes exactly one synchronous transport
attempt, returning either a normalized response or a normalized failure
with a closed `kind` — never a raw Python exception or traceback.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
import socket
import ssl
import urllib.error
import urllib.request


@dataclass(frozen=True)
class HttpTransportRequest:
    """Private normalized outbound HTTP request."""

    method: str
    url: str
    headers: Mapping[str, str]
    body: bytes
    timeout_seconds: float


@dataclass(frozen=True)
class HttpTransportResponse:
    """Private normalized outbound HTTP response."""

    status: int
    headers: Mapping[str, str]
    body: bytes


@dataclass(frozen=True)
class HttpTransportFailure:
    """Private normalized transport failure with a closed `kind`."""

    kind: str


HttpTransport = Callable[[HttpTransportRequest], HttpTransportResponse]


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        return None


def _default_transport(request: HttpTransportRequest) -> HttpTransportResponse:
    wire_request = urllib.request.Request(
        request.url,
        data=request.body,
        headers=dict(request.headers),
        method=request.method,
    )
    opener = urllib.request.build_opener(_NoRedirect)
    try:
        with opener.open(wire_request, timeout=request.timeout_seconds) as response:
            return HttpTransportResponse(
                response.status,
                dict(response.headers.items()),
                response.read(),
            )
    except urllib.error.HTTPError as error:
        try:
            body = error.read()
        finally:
            error.close()
        return HttpTransportResponse(error.code, dict(error.headers.items()), body)


def _classify(exc: BaseException) -> str:
    if isinstance(exc, (TimeoutError, socket.timeout)):
        return "timeout"
    if isinstance(exc, urllib.error.URLError):
        reason = exc.reason
        if isinstance(reason, BaseException):
            return _classify(reason)
        return "other"
    if isinstance(exc, ssl.SSLError):
        return "tls"
    if isinstance(exc, socket.gaierror):
        return "dns"
    if isinstance(exc, OSError):
        return "connect"
    return "other"


def send_http_request(
    request: HttpTransportRequest,
    transport: HttpTransport | None = None,
) -> HttpTransportResponse | HttpTransportFailure:
    """Make exactly one synchronous outbound HTTP transport attempt."""

    selected = _default_transport if transport is None else transport
    if not callable(selected):
        raise TypeError("HTTP transport capability expected a callable transport")
    try:
        return selected(request)
    except Exception as error:  # noqa: BLE001 - normalized boundary, never re-raised
        return HttpTransportFailure(_classify(error))
