import json
import socket
import threading
import time
from pathlib import Path
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


def _request(method: str, url: str, *, body: str | None = None, headers: dict[str, str] | None = None):
    encoded_body = None if body is None else body.encode("utf-8")
    last_error = None

    for _ in range(60):
        try:
            request = Request(url, data=encoded_body, method=method, headers={} if headers is None else headers)
            with urlopen(request, timeout=2) as response:
                return response.status, response.headers, response.read().decode("utf-8")
        except HTTPError as exc:
            return exc.code, exc.headers, exc.read().decode("utf-8")
        except URLError as exc:
            last_error = exc
            time.sleep(0.02)

    raise last_error  # type: ignore[misc]


def _finish_server(thread: threading.Thread, outcome: dict[str, object]):
    thread.join(timeout=3)
    assert not thread.is_alive(), "server thread did not stop"
    if "error" in outcome:
        raise outcome["error"]  # type: ignore[misc]
    return outcome["result"]


def test_serve_http_plain_text_response():
    port = _free_port()
    env = make_global_env([])
    env.set("host", "127.0.0.1")
    env.set("port", port)

    source = """
import web

get = web.get
ok_text = web.ok_text
route_request = web.route_request
serve_http = web.serve_http

serve_http(
  {host: host, port: port, max_requests: 1},
    route_request([
        get("/health", (_) -> ok_text("ok"))
  ])
)
"""

    thread, outcome = _start_server(source, env, filename="<http-plain-text>")
    status, headers, body = _request("GET", f"http://127.0.0.1:{port}/health")
    result = _finish_server(thread, outcome)

    assert status == 200
    assert headers["Content-Type"] == "text/plain; charset=utf-8"
    assert body == "ok"
    assert result.get("handled_requests") == 1


def test_serve_http_json_response_and_request_body_parsing():
    port = _free_port()
    env = make_global_env([])
    env.set("host", "127.0.0.1")
    env.set("port", port)

    source = """
import web

post = web.post
json = web.json
route_request = web.route_request
serve_http = web.serve_http

serve_http(
  {host: host, port: port, max_requests: 1},
    route_request([
        post("/echo", (request) -> json({
      method: request.method,
      path: request.path,
      query: request.query,
      body: request.body
    }))
  ])
)
"""

    thread, outcome = _start_server(source, env, filename="<http-json>")
    status, headers, body = _request(
        "POST",
        f"http://127.0.0.1:{port}/echo?name=genia",
        body='{"answer":42}',
        headers={"Content-Type": "application/json"},
    )
    result = _finish_server(thread, outcome)
    parsed = json.loads(body)

    assert status == 200
    assert headers["Content-Type"] == "application/json; charset=utf-8"
    assert parsed == {
        "method": "POST",
        "path": "/echo",
        "query": {"name": "genia"},
        "body": {"answer": 42},
    }
    assert result.get("handled_requests") == 1


def test_serve_http_emits_headers_composed_by_with_headers():
    port = _free_port()
    env = make_global_env([])
    env.set("host", "127.0.0.1")
    env.set("port", port)

    source = """
import web

serve_http = web.serve_http
route_request = web.route_request
get = web.get
response_headers = {
  "X-Request-ID": "abc123",
  "Content-Type": "application/problem+json"
}

serve_http(
  {host: host, port: port, max_requests: 1},
  route_request([
    get("/composed", (_) -> web.with_headers(
      response_headers,
      web.json({message: "hello"})
    ))
  ])
)
"""

    thread, outcome = _start_server(source, env, filename="<http-with-headers>")
    status, headers, body = _request("GET", f"http://127.0.0.1:{port}/composed")
    result = _finish_server(thread, outcome)

    assert status == 200
    assert headers["Content-Type"] == "application/problem+json"
    assert headers["X-Request-ID"] == "abc123"
    assert json.loads(body) == {"message": "hello"}
    assert result.get("handled_requests") == 1


def test_serve_http_cors_preflight_then_json_request():
    port = _free_port()
    env = make_global_env([])
    env.set("host", "127.0.0.1")
    env.set("port", port)

    source = """
import web

handler = web.route_request([
  web.get("/data", (_) -> web.json({message: "hello"}))
]) |> web.cors({
  origin: "http://localhost:5173",
  methods: ["GET", "POST"],
  headers: ["content-type", "x-request-id"]
})

web.serve_http({host: host, port: port, max_requests: 2}, handler)
"""

    thread, outcome = _start_server(source, env, filename="<http-cors>")
    status, headers, body = _request(
        "OPTIONS",
        f"http://127.0.0.1:{port}/data",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert status == 204
    assert body == ""
    assert headers["Access-Control-Allow-Origin"] == "http://localhost:5173"
    assert headers["Access-Control-Allow-Methods"] == "GET, POST"
    assert headers["Access-Control-Allow-Headers"] == "content-type, x-request-id"

    status, headers, body = _request(
        "GET",
        f"http://127.0.0.1:{port}/data",
        headers={"Origin": "http://localhost:5173"},
    )
    result = _finish_server(thread, outcome)

    assert status == 200
    assert headers["Content-Type"] == "application/json; charset=utf-8"
    assert headers["Access-Control-Allow-Origin"] == "http://localhost:5173"
    assert headers["Access-Control-Allow-Methods"] == "GET, POST"
    assert headers["Access-Control-Allow-Headers"] == "content-type, x-request-id"
    assert json.loads(body) == {"message": "hello"}
    assert result.get("handled_requests") == 2


@pytest.mark.parametrize(
    ("source", "message"),
    [
        ('web.cors([], (_) -> web.ok("ok"))', "cors expected policy to be a map"),
        ('web.cors({extra: true}, (_) -> web.ok("ok"))', 'cors unexpected policy field "extra"'),
        ('web.cors({origin: ""}, (_) -> web.ok("ok"))', "cors expected policy.origin to be a non-empty string"),
        ('web.cors({methods: []}, (_) -> web.ok("ok"))', "cors expected policy.methods to be a non-empty list"),
        ('web.cors({methods: ["GET", ""]}, (_) -> web.ok("ok"))', "cors expected policy.methods item at index 1 to be a non-empty string"),
        ('web.cors({headers: []}, (_) -> web.ok("ok"))', "cors expected policy.headers to be a non-empty list"),
        ('web.cors({headers: ["content-type", 7]}, (_) -> web.ok("ok"))', "cors expected policy.headers item at index 1 to be a non-empty string"),
        ('web.cors({}, 7)', "cors expected handler to be callable"),
    ],
)
def test_cors_rejects_programmer_misuse(source, message):
    env = make_global_env([])

    with pytest.raises(TypeError, match=message):
        run_source(f"import web\n{source}", env, filename="<cors-misuse>")


def test_cors_validation_stops_at_first_contract_error():
    env = make_global_env([])

    with pytest.raises(TypeError, match="cors expected policy to be a map"):
        run_source("import web\nweb.cors([], 7)", env, filename="<cors-order>")


@pytest.mark.parametrize(
    ("source", "message"),
    [
        ('web.with_headers([], {status: 200, headers: {}, body: "ok"})', "with_headers expected headers to be a map"),
        ('web.with_headers({}, [])', "with_headers expected response to be a map"),
        ('web.with_headers({}, {headers: {}, body: "ok"})', "with_headers expected response.status field"),
        ('web.with_headers({}, {status: 200, body: "ok"})', "with_headers expected response.headers field"),
        ('web.with_headers({}, {status: 200, headers: {}})', "with_headers expected response.body field"),
        ('web.with_headers({}, {status: 200, headers: [], body: "ok"})', "with_headers expected response.headers to be a map"),
        ('web.with_headers({}, {status: 200, headers: map_put({}, 7, "bad"), body: "ok"})', "with_headers expected response header name at index 0 to be a string"),
        ('web.with_headers({}, {status: 200, headers: {"x-ok": "yes", "x-bad": 7}, body: "ok"})', "with_headers expected response header value at index 1 to be a string"),
        ('web.with_headers(map_put({}, 7, "bad"), {status: 200, headers: {}, body: "ok"})', "with_headers expected supplied header name at index 0 to be a string"),
        ('web.with_headers({"x-ok": "yes", "x-bad": 7}, {status: 200, headers: {}, body: "ok"})', "with_headers expected supplied header value at index 1 to be a string"),
    ],
)
def test_with_headers_rejects_programmer_misuse(source, message):
    env = make_global_env([])

    with pytest.raises(TypeError, match=message):
        run_source(f"import web\n{source}", env, filename="<with-headers-misuse>")


def test_with_headers_validation_stops_at_first_contract_error():
    env = make_global_env([])

    with pytest.raises(TypeError, match="with_headers expected headers to be a map"):
        run_source("import web\nweb.with_headers([], [])", env, filename="<with-headers-order>")


def test_serve_http_request_map_includes_client_and_raw_text_body():
    port = _free_port()
    env = make_global_env([])
    env.set("host", "127.0.0.1")
    env.set("port", port)

    source = """
import web

post = web.post
json = web.json
route_request = web.route_request
serve_http = web.serve_http

serve_http(
  {host: host, port: port, max_requests: 1},
    route_request([
        post("/inspect", (request) -> json({
      method: request.method,
      path: request.path,
      raw_body: request.raw_body,
      body: request.body,
      client_host: unwrap_or("", get("host", request.client)),
      client_port: unwrap_or(0, get("port", request.client))
    }))
  ])
)
"""

    thread, outcome = _start_server(source, env, filename="<http-request-shape>")
    status, headers, body = _request(
        "POST",
        f"http://127.0.0.1:{port}/inspect",
        body="hello from text",
        headers={"Content-Type": "text/plain"},
    )
    result = _finish_server(thread, outcome)
    parsed = json.loads(body)

    assert status == 200
    assert headers["Content-Type"] == "application/json; charset=utf-8"
    assert parsed["method"] == "POST"
    assert parsed["path"] == "/inspect"
    assert parsed["raw_body"] == "hello from text"
    assert parsed["body"] == "hello from text"
    assert parsed["client_host"] == "127.0.0.1"
    assert isinstance(parsed["client_port"], int)
    assert result.get("handled_requests") == 1


def test_serve_http_json_body_parse_failure_stays_in_request_body_as_absence():
    port = _free_port()
    env = make_global_env([])
    env.set("host", "127.0.0.1")
    env.set("port", port)

    source = """
import web

post = web.post
json = web.json
route_request = web.route_request
serve_http = web.serve_http

serve_http(
  {host: host, port: port, max_requests: 1},
    route_request([
        post("/inspect", (request) -> json({
      raw_body: request.raw_body,
      body_reason: unwrap_or("?", absence_reason(request.body)),
      body_source: unwrap_or("?", then_get("source", absence_context(request.body)))
    }))
  ])
)
"""

    thread, outcome = _start_server(source, env, filename="<http-json-parse-failure>")
    status, headers, body = _request(
        "POST",
        f"http://127.0.0.1:{port}/inspect",
        body='{"answer":',
        headers={"Content-Type": "application/json"},
    )
    result = _finish_server(thread, outcome)
    parsed = json.loads(body)

    assert status == 200
    assert headers["Content-Type"] == "application/json; charset=utf-8"
    assert parsed == {
        "raw_body": '{"answer":',
        "body_reason": "json-parse-error",
        "body_source": "json_parse",
    }
    assert result.get("handled_requests") == 1


def test_serve_http_route_request_returns_not_found_response():
    port = _free_port()
    env = make_global_env([])
    env.set("host", "127.0.0.1")
    env.set("port", port)

    source = """
import web

get = web.get
ok_text = web.ok_text
route_request = web.route_request
serve_http = web.serve_http

serve_http(
  {host: host, port: port, max_requests: 1},
    route_request([
        get("/health", (_) -> ok_text("ok"))
  ])
)
"""

    thread, outcome = _start_server(source, env, filename="<http-not-found>")
    status, headers, body = _request("GET", f"http://127.0.0.1:{port}/missing")
    _finish_server(thread, outcome)

    assert status == 404
    assert headers["Content-Type"] == "text/plain; charset=utf-8"
    assert body == "not found"


def test_serve_http_invalid_handler_result_returns_500():
    port = _free_port()
    env = make_global_env([])
    env.set("host", "127.0.0.1")
    env.set("port", port)

    source = """
import web

get = web.get
route_request = web.route_request
serve_http = web.serve_http

serve_http(
  {host: host, port: port, max_requests: 1},
    route_request([
        get("/broken", (_) -> 42)
  ])
)
"""

    thread, outcome = _start_server(source, env, filename="<http-invalid-response>")
    status, headers, body = _request("GET", f"http://127.0.0.1:{port}/broken")
    _finish_server(thread, outcome)

    assert status == 500
    assert headers["Content-Type"] == "text/plain; charset=utf-8"
    assert body == "internal server error"


def test_http_service_example_runs_health_endpoint():
    port = _free_port()
    source_path = Path("examples/http_service.genia")
    source = source_path.read_text(encoding="utf-8")
    env = make_global_env([])

    threaded_source = source + f'\nmain(["--port", "{port}", "--max-requests", "1"])\n'

    thread, outcome = _start_server(threaded_source, env, filename=str(source_path.resolve()))
    status, headers, body = _request("GET", f"http://127.0.0.1:{port}/health")
    _finish_server(thread, outcome)

    assert status == 200
    assert headers["Content-Type"] == "text/plain; charset=utf-8"
    assert headers["Access-Control-Allow-Origin"] == "http://localhost:5173"
    assert body == "ok"
