import http.server
import json
import socket
import threading
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import pytest

from genia import make_global_env, run_source


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _start_server(source: str, env, *, filename: str):
    outcome: dict[str, object] = {}

    def target() -> None:
        try:
            outcome["result"] = run_source(source, env, filename=filename)
        except BaseException as exc:  # pragma: no cover - surfaced through assertions
            outcome["error"] = exc

    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    return thread, outcome


def _request(method: str, url: str):
    last_error = None
    for _ in range(60):
        try:
            request = Request(url, method=method)
            with urlopen(request, timeout=2) as response:
                return response.status, response.read().decode("utf-8")
        except HTTPError as exc:
            return exc.code, exc.read().decode("utf-8")
        except URLError as exc:
            last_error = exc
            time.sleep(0.02)
    raise last_error  # type: ignore[misc]


def _finish_server(thread: threading.Thread, outcome: dict[str, object]):
    thread.join(timeout=5)
    assert not thread.is_alive(), "server thread did not stop"
    if "error" in outcome:
        raise outcome["error"]  # type: ignore[misc]
    return outcome["result"]


class _DownstreamHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        self.server.hits.append(self.path)  # type: ignore[attr-defined]
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(f"downstream:{self.path}".encode("utf-8"))

    def log_message(self, format, *args):  # noqa: A002
        pass


class _DownstreamServer(http.server.ThreadingHTTPServer):
    def __init__(self):
        super().__init__(("127.0.0.1", 0), _DownstreamHandler)
        self.hits: list[str] = []
        self.daemon_threads = True

    def start(self) -> None:
        threading.Thread(target=self.serve_forever, daemon=True).start()

    def stop(self) -> None:
        self.shutdown()
        self.server_close()


@pytest.mark.loopback
def test_request_handler_outbound_call_success_and_server_stays_active():
    downstream = _DownstreamServer()
    downstream.start()
    server_port = _free_port()
    try:
        env = make_global_env([])
        source = f"""
import web

handler(request) = {{
  op = http_operation(quote(get), "http://127.0.0.1:{downstream.server_port}", "/ping", {{}}, {{}}, none("http-no-body")) |> unwrap_or(none)
  result = web.http_send(op, none("nil"), 2000)
  status = unwrap_or(none, result)("status")
  web.json({{downstream_status: status}})
}}

web.serve_http({{host: "127.0.0.1", port: {server_port}, max_requests: 2}}, web.route_request([web.get("/proxy", handler)]))
"""
        thread, outcome = _start_server(source, env, filename="<server-client-success>")
        status1, body1 = _request("GET", f"http://127.0.0.1:{server_port}/proxy")
        status2, body2 = _request("GET", f"http://127.0.0.1:{server_port}/proxy")
        result = _finish_server(thread, outcome)
    finally:
        downstream.stop()

    assert status1 == 200
    assert json.loads(body1) == {"downstream_status": 200}
    assert status2 == 200
    assert json.loads(body2) == {"downstream_status": 200}
    assert result.get("handled_requests") == 2
    assert len(downstream.hits) == 2


@pytest.mark.loopback
def test_request_handler_outbound_call_failure_does_not_stop_server():
    dead_port = _free_port()
    server_port = _free_port()
    env = make_global_env([])
    source = f"""
import web

classify_outcome(result) = (some(_)) -> "ok" | (err(_, _)) -> "failed"

handler(request) = {{
  op = http_operation(quote(get), "http://127.0.0.1:{dead_port}", "/ping", {{}}, {{}}, none("http-no-body")) |> unwrap_or(none)
  result = web.http_send(op, none("nil"), 2000)
  web.json({{outbound: classify_outcome(result)}})
}}

web.serve_http({{host: "127.0.0.1", port: {server_port}, max_requests: 2}}, web.route_request([web.get("/proxy", handler)]))
"""
    thread, outcome = _start_server(source, env, filename="<server-client-failure>")
    status1, body1 = _request("GET", f"http://127.0.0.1:{server_port}/proxy")
    status2, body2 = _request("GET", f"http://127.0.0.1:{server_port}/proxy")
    result = _finish_server(thread, outcome)

    assert status1 == 200
    assert json.loads(body1) == {"outbound": "failed"}
    assert status2 == 200
    assert json.loads(body2) == {"outbound": "failed"}
    assert result.get("handled_requests") == 2


@pytest.mark.loopback
def test_request_handler_makes_two_sequential_outbound_calls():
    downstream = _DownstreamServer()
    downstream.start()
    server_port = _free_port()
    try:
        env = make_global_env([])
        source = f"""
import web

handler(request) = {{
  op_a = http_operation(quote(get), "http://127.0.0.1:{downstream.server_port}", "/a", {{}}, {{}}, none("http-no-body")) |> unwrap_or(none)
  op_b = http_operation(quote(get), "http://127.0.0.1:{downstream.server_port}", "/b", {{}}, {{}}, none("http-no-body")) |> unwrap_or(none)
  result_a = unwrap_or(none, web.http_send(op_a, none("nil"), 2000))
  result_b = unwrap_or(none, web.http_send(op_b, none("nil"), 2000))
  web.json({{a: result_a("status"), b: result_b("status")}})
}}

web.serve_http({{host: "127.0.0.1", port: {server_port}, max_requests: 1}}, web.route_request([web.get("/proxy", handler)]))
"""
        thread, outcome = _start_server(source, env, filename="<server-client-two-calls>")
        status, body = _request("GET", f"http://127.0.0.1:{server_port}/proxy")
        _finish_server(thread, outcome)
    finally:
        downstream.stop()

    assert status == 200
    assert json.loads(body) == {"a": 200, "b": 200}
    assert sorted(downstream.hits) == ["/a", "/b"]


@pytest.mark.loopback
def test_request_handler_using_send_annotated_composes_too():
    downstream = _DownstreamServer()
    downstream.start()
    server_port = _free_port()
    try:
        env = make_global_env([])
        source = f"""
import web

@get {{path: "/ping"}}
ping() = {{headers: {{}}, query: {{}}, body: none("http-no-body")}}

handler(request) = {{
  result = unwrap_or(none, web.send_annotated(ping, "http://127.0.0.1:{downstream.server_port}", none("nil"), 2000))
  web.json({{downstream_status: result("status")}})
}}

web.serve_http({{host: "127.0.0.1", port: {server_port}, max_requests: 1}}, web.route_request([web.get("/proxy", handler)]))
"""
        thread, outcome = _start_server(source, env, filename="<server-client-annotated>")
        status, body = _request("GET", f"http://127.0.0.1:{server_port}/proxy")
        _finish_server(thread, outcome)
    finally:
        downstream.stop()

    assert status == 200
    assert json.loads(body) == {"downstream_status": 200}
