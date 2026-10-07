"""Experimental Python-host outbound HTTP transport capability for R14.

This module has no Genia-visible surface: it is a private host capability
consumed by ``http_client.py`` (`web.http_send`, E14-7), not registered as a
Genia builtin. It accepts an already-normalized request (method, absolute
URL, string headers, byte body) and makes exactly one synchronous transport
attempt. Exceptions raised by the selected callable become non-sensitive
failures with a closed ``kind``. Callable selection errors and non-Exception
BaseException subclasses remain outside that normalization boundary.
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
    """Private wire request: method/absolute URL, string headers, bytes, seconds timeout.

    Callers prepare and validate fields. Frozen attributes do not deep-freeze
    the supplied header mapping; no IO or defensive copy occurs on creation.
    """

    method: str
    url: str
    headers: Mapping[str, str]
    body: bytes
    timeout_seconds: float


@dataclass(frozen=True)
class HttpTransportResponse:
    """Private response retaining status, header spelling and fully read body bytes.

    HTTP error statuses are responses too. Fields are not validated and the
    header mapping is not deep-frozen; the client converts this host record.
    """

    status: int
    headers: Mapping[str, str]
    body: bytes


@dataclass(frozen=True)
class HttpTransportFailure:
    """Non-sensitive failure record emitted with a closed transport kind.

    send_http_request supplies timeout/connect/tls/dns/other without retaining
    exception text. Direct construction does not validate the kind string.
    """

    kind: str


HttpTransport = Callable[[HttpTransportRequest], HttpTransportResponse]


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Prevent urllib from issuing a second request for an HTTP redirect."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        """Decline redirect construction; urllib exposes the redirect as HTTPError."""
        return None


def _default_transport(request: HttpTransportRequest) -> HttpTransportResponse:
    """Perform one blocking urllib request using normalized method/URL/headers/bytes.

    Disable redirects and retries. Fully read and close the response; HTTPError
    statuses, including redirects, are read and closed as ordinary responses.
    Other exceptions escape for send_http_request to classify. The seconds
    timeout is passed to urllib; there is no streaming or response-size bound.
    """
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
    """Reduce an exception to timeout, tls, dns, connect or other without its text.

    Recursively classify exception-valued URLError reasons; textual reasons
    become other. Check TLS and DNS before their broader OSError superclass.
    """
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
    """Call the selected transport once and normalize raised Exceptions.

    Use urllib by default or an injected callable accepting the prepared
    request and returning HttpTransportResponse. Return its result unchanged;
    this boundary does not validate injected results or request fields. A
    non-callable transport raises TypeError before the attempt. Exceptions
    from the call become HttpTransportFailure with a closed kind; BaseException
    subclasses outside Exception propagate. No exception text is retained.
    """

    selected = _default_transport if transport is None else transport
    if not callable(selected):
        raise TypeError("HTTP transport capability expected a callable transport")
    try:
        return selected(request)
    except Exception as error:  # noqa: BLE001 - normalized boundary, never re-raised
        return HttpTransportFailure(_classify(error))
