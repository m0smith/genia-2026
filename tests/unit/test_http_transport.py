import http.server
import socket
import ssl
import threading
import time
import urllib.error

import pytest

from genia.http_transport import (
    HttpTransportFailure,
    HttpTransportRequest,
    HttpTransportResponse,
    send_http_request,
)


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class _FixtureServer(http.server.HTTPServer):
    def __init__(self, responses):
        super().__init__(("127.0.0.1", 0), _FixtureHandler)
        self.captured: list[dict] = []
        self._responses = list(responses)

    def next_response(self):
        if self._responses:
            return self._responses.pop(0)
        return 200, {}, b""

    @property
    def port(self) -> int:
        return self.server_port


class _FixtureHandler(http.server.BaseHTTPRequestHandler):
    def _handle(self) -> None:
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length) if length else b""
        self.server.captured.append(
            {
                "method": self.command,
                "path": self.path,
                "headers": {key.lower(): value for key, value in self.headers.items()},
                "body": body,
            }
        )
        status, headers, response_body = self.server.next_response()
        self.send_response(status)
        for key, value in headers.items():
            self.send_header(key, value)
        self.end_headers()
        if response_body:
            self.wfile.write(response_body)

    do_GET = _handle
    do_POST = _handle
    do_PUT = _handle
    do_PATCH = _handle
    do_DELETE = _handle

    def log_message(self, format, *args):  # noqa: A002 - silence test-server logging
        pass


def _run_fixture(server: _FixtureServer, request_count: int) -> threading.Thread:
    def serve() -> None:
        for _ in range(request_count):
            server.handle_request()

    thread = threading.Thread(target=serve, daemon=True)
    thread.start()
    return thread


class _SlowHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802 - stdlib handler naming
        time.sleep(1.0)
        self.send_response(200)
        self.end_headers()

    def log_message(self, format, *args):  # noqa: A002
        pass


@pytest.mark.loopback
def test_send_http_request_returns_exact_status_headers_body_from_real_server():
    server = _FixtureServer([(200, {"Content-Type": "text/plain"}, b"ok")])
    thread = _run_fixture(server, 1)
    try:
        request = HttpTransportRequest(
            method="GET",
            url=f"http://127.0.0.1:{server.port}/items?x=1",
            headers={"X-Test": "yes"},
            body=b"",
            timeout_seconds=2.0,
        )
        response = send_http_request(request)
    finally:
        thread.join(timeout=3)
        server.server_close()

    assert isinstance(response, HttpTransportResponse)
    assert response.status == 200
    assert response.headers["Content-Type"] == "text/plain"
    assert response.body == b"ok"
    assert len(server.captured) == 1
    assert server.captured[0]["method"] == "GET"
    assert server.captured[0]["path"] == "/items?x=1"
    assert server.captured[0]["headers"]["x-test"] == "yes"
    assert server.captured[0]["body"] == b""


@pytest.mark.loopback
def test_send_http_request_http_error_status_returns_ordinary_response_not_failure():
    server = _FixtureServer([(404, {"Content-Type": "text/plain"}, b"missing")])
    thread = _run_fixture(server, 1)
    try:
        request = HttpTransportRequest(
            method="POST",
            url=f"http://127.0.0.1:{server.port}/missing",
            headers={"Content-Type": "text/plain"},
            body=b"payload",
            timeout_seconds=2.0,
        )
        response = send_http_request(request)
    finally:
        thread.join(timeout=3)
        server.server_close()

    assert isinstance(response, HttpTransportResponse)
    assert response.status == 404
    assert response.body == b"missing"
    assert server.captured[0]["body"] == b"payload"


@pytest.mark.loopback
def test_send_http_request_does_not_follow_redirect():
    server = _FixtureServer([(302, {"Location": "/target"}, b"")])
    thread = _run_fixture(server, 1)
    try:
        request = HttpTransportRequest(
            method="GET",
            url=f"http://127.0.0.1:{server.port}/start",
            headers={},
            body=b"",
            timeout_seconds=2.0,
        )
        response = send_http_request(request)
    finally:
        thread.join(timeout=3)
        server.server_close()

    assert isinstance(response, HttpTransportResponse)
    assert response.status == 302
    assert len(server.captured) == 1
    assert server.captured[0]["path"] == "/start"


@pytest.mark.loopback
def test_send_http_request_connect_refused_returns_connect_failure():
    port = _free_port()
    request = HttpTransportRequest(
        method="GET",
        url=f"http://127.0.0.1:{port}/",
        headers={},
        body=b"",
        timeout_seconds=2.0,
    )

    response = send_http_request(request)

    assert isinstance(response, HttpTransportFailure)
    assert response.kind == "connect"


@pytest.mark.loopback
def test_send_http_request_timeout_against_slow_server_returns_timeout_failure():
    server = http.server.HTTPServer(("127.0.0.1", 0), _SlowHandler)
    threading.Thread(target=server.handle_request, daemon=True).start()
    try:
        request = HttpTransportRequest(
            method="GET",
            url=f"http://127.0.0.1:{server.server_port}/",
            headers={},
            body=b"",
            timeout_seconds=0.2,
        )
        response = send_http_request(request)
    finally:
        server.server_close()

    assert isinstance(response, HttpTransportFailure)
    assert response.kind == "timeout"


def test_send_http_request_classifies_dns_failure_via_gaierror():
    def fake_transport(request: HttpTransportRequest) -> HttpTransportResponse:
        raise socket.gaierror("nodename nor servname provided")

    request = HttpTransportRequest(
        method="GET", url="http://example.invalid/", headers={}, body=b"", timeout_seconds=1.0
    )

    response = send_http_request(request, transport=fake_transport)

    assert isinstance(response, HttpTransportFailure)
    assert response.kind == "dns"


def test_send_http_request_classifies_tls_failure_via_sslerror():
    def fake_transport(request: HttpTransportRequest) -> HttpTransportResponse:
        raise ssl.SSLError("certificate verify failed")

    request = HttpTransportRequest(
        method="GET", url="https://example.invalid/", headers={}, body=b"", timeout_seconds=1.0
    )

    response = send_http_request(request, transport=fake_transport)

    assert isinstance(response, HttpTransportFailure)
    assert response.kind == "tls"


def test_send_http_request_classifies_timeout_via_fake_transport():
    def fake_transport(request: HttpTransportRequest) -> HttpTransportResponse:
        raise TimeoutError("timed out")

    request = HttpTransportRequest(
        method="GET", url="http://example.invalid/", headers={}, body=b"", timeout_seconds=1.0
    )

    response = send_http_request(request, transport=fake_transport)

    assert isinstance(response, HttpTransportFailure)
    assert response.kind == "timeout"


def test_send_http_request_classifies_urlerror_wrapped_reason():
    def fake_transport(request: HttpTransportRequest) -> HttpTransportResponse:
        raise urllib.error.URLError(ConnectionRefusedError("refused"))

    request = HttpTransportRequest(
        method="GET", url="http://example.invalid/", headers={}, body=b"", timeout_seconds=1.0
    )

    response = send_http_request(request, transport=fake_transport)

    assert isinstance(response, HttpTransportFailure)
    assert response.kind == "connect"


def test_send_http_request_classifies_generic_oserror_as_connect():
    def fake_transport(request: HttpTransportRequest) -> HttpTransportResponse:
        raise ConnectionResetError("reset")

    request = HttpTransportRequest(
        method="GET", url="http://example.invalid/", headers={}, body=b"", timeout_seconds=1.0
    )

    response = send_http_request(request, transport=fake_transport)

    assert isinstance(response, HttpTransportFailure)
    assert response.kind == "connect"


def test_send_http_request_classifies_unrecognized_exception_as_other():
    def fake_transport(request: HttpTransportRequest) -> HttpTransportResponse:
        raise RuntimeError("boom")

    request = HttpTransportRequest(
        method="GET", url="http://example.invalid/", headers={}, body=b"", timeout_seconds=1.0
    )

    response = send_http_request(request, transport=fake_transport)

    assert isinstance(response, HttpTransportFailure)
    assert response.kind == "other"


def test_send_http_request_preserves_non_utf8_body_bytes():
    non_utf8 = b"\xff\xfe\x00binary"

    def fake_transport(request: HttpTransportRequest) -> HttpTransportResponse:
        assert request.body == non_utf8
        return HttpTransportResponse(status=200, headers={}, body=non_utf8)

    request = HttpTransportRequest(
        method="POST",
        url="http://example.invalid/",
        headers={},
        body=non_utf8,
        timeout_seconds=1.0,
    )

    response = send_http_request(request, transport=fake_transport)

    assert isinstance(response, HttpTransportResponse)
    assert response.body == non_utf8


def test_send_http_request_empty_body_request_and_response_round_trip():
    def fake_transport(request: HttpTransportRequest) -> HttpTransportResponse:
        assert request.body == b""
        return HttpTransportResponse(status=204, headers={}, body=b"")

    request = HttpTransportRequest(
        method="DELETE",
        url="http://example.invalid/",
        headers={},
        body=b"",
        timeout_seconds=1.0,
    )

    response = send_http_request(request, transport=fake_transport)

    assert isinstance(response, HttpTransportResponse)
    assert response.status == 204
    assert response.body == b""
