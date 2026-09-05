import http.server
import socket
import threading

import pytest

from genia.builtins import make_global_env
from genia.configuration import create_declassification_authority
from genia.http_client import perform_http_send
from genia.http_operation import construct_http_operation
from genia.http_transport import HttpTransportFailure, HttpTransportRequest, HttpTransportResponse
from genia.interpreter import run_source
from genia.values import (
    GeniaBytes,
    GeniaMap,
    GeniaOptionErr,
    GeniaOptionNone,
    GeniaOptionSome,
    make_none,
    symbol,
)


def _invoke(fn, args):
    return fn(*args)


def _json_encode(value):
    return GeniaOptionSome("{}")


def _operation(**overrides):
    fields = {
        "method": symbol("get"),
        "base_url": "http://example.invalid",
        "path": "/items",
        "headers": GeniaMap(),
        "query": GeniaMap(),
        "body": make_none("http-no-body"),
    }
    fields.update(overrides)
    result = construct_http_operation(
        fields["method"],
        fields["base_url"],
        fields["path"],
        fields["headers"],
        fields["query"],
        fields["body"],
        _json_encode,
    )
    assert isinstance(result, GeniaOptionSome), result
    return result.value


def _fake_transport(response=None, failure=None, calls=None):
    def transport(request):
        if calls is not None:
            calls.append(request)
        if failure is not None:
            raise failure
        return response

    return transport


def test_perform_http_send_returns_response_for_any_received_status():
    calls = []
    transport = _fake_transport(
        response=HttpTransportResponse(status=404, headers={"X-Test": "1"}, body=b"missing"),
        calls=calls,
    )
    operation = _operation()

    result = perform_http_send(
        operation, GeniaOptionNone("nil"), 2000,
        json_encode=_json_encode, invoke=_invoke, transport=transport,
    )

    assert isinstance(result, GeniaOptionSome)
    response = result.value
    assert response.get("status") == 404
    assert response.get("headers").get("X-Test") == "1"
    assert isinstance(response.get("body"), GeniaBytes)
    assert response.get("body").value == b"missing"
    assert len(calls) == 1


def test_perform_http_send_invokes_transport_exactly_once():
    calls = []
    transport = _fake_transport(
        response=HttpTransportResponse(status=200, headers={}, body=b"ok"), calls=calls
    )
    operation = _operation()

    perform_http_send(
        operation, GeniaOptionNone("nil"), 2000,
        json_encode=_json_encode, invoke=_invoke, transport=transport,
    )

    assert len(calls) == 1


@pytest.mark.parametrize(
    "kind,expected_reason",
    [
        ("timeout", "http-timeout"),
        ("connect", "http-transport-failure"),
        ("tls", "http-transport-failure"),
        ("dns", "http-transport-failure"),
        ("other", "http-transport-failure"),
    ],
)
def test_perform_http_send_maps_every_transport_failure_kind(kind, expected_reason):
    transport = _fake_transport(response=HttpTransportFailure(kind))
    operation = _operation()

    result = perform_http_send(
        operation, GeniaOptionNone("nil"), 2000,
        json_encode=_json_encode, invoke=_invoke, transport=transport,
    )

    assert isinstance(result, GeniaOptionErr)
    assert result.reason == expected_reason
    if kind == "timeout":
        assert result.context.get("timeout_ms") == 2000
    else:
        assert result.context.get("kind") == symbol(kind)


def test_perform_http_send_rejects_malformed_operation():
    with pytest.raises(TypeError):
        perform_http_send(
            GeniaMap(), GeniaOptionNone("nil"), 2000,
            json_encode=_json_encode, invoke=_invoke, transport=_fake_transport(),
        )


def test_perform_http_send_rejects_malformed_authority():
    operation = _operation()
    with pytest.raises(TypeError):
        perform_http_send(
            operation, "not-an-authority", 2000,
            json_encode=_json_encode, invoke=_invoke, transport=_fake_transport(),
        )


@pytest.mark.parametrize("bad_timeout", [0, -1, 300001, 1.5, "2000", True])
def test_perform_http_send_rejects_malformed_timeout_ms(bad_timeout):
    operation = _operation()
    with pytest.raises(TypeError):
        perform_http_send(
            operation, GeniaOptionNone("nil"), bad_timeout,
            json_encode=_json_encode, invoke=_invoke, transport=_fake_transport(),
        )


def test_perform_http_send_protected_header_with_no_authority_is_misuse():
    env = make_global_env([])
    provider, token = run_source(
        'provider = config_provider([{kind: quote(values), values: {K: "secret-value"}}]) |> unwrap_or(none)\n'
        'token = secret_get(provider, "K", quote(http_send)) |> unwrap_or(none)\n'
        "[provider, token]",
        env,
    )
    operation = _operation(headers=GeniaMap().put("authorization", token))

    with pytest.raises(TypeError):
        perform_http_send(
            operation, GeniaOptionNone("nil"), 2000,
            json_encode=_json_encode, invoke=_invoke, transport=_fake_transport(),
        )


def test_perform_http_send_protected_header_with_mismatched_authority_is_misuse():
    env = make_global_env([])
    provider, token = run_source(
        'provider = config_provider([{kind: quote(values), values: {K: "secret-value"}}]) |> unwrap_or(none)\n'
        'token = secret_get(provider, "K", quote(http_send)) |> unwrap_or(none)\n'
        "[provider, token]",
        env,
    )
    wrong_authority = create_declassification_authority(
        provider, [symbol("different_purpose")], lambda event: None
    )
    operation = _operation(headers=GeniaMap().put("authorization", token))

    with pytest.raises(TypeError):
        perform_http_send(
            operation, GeniaOptionSome(wrong_authority), 2000,
            json_encode=_json_encode, invoke=_invoke, transport=_fake_transport(),
        )


def test_perform_http_send_declassifies_matching_protected_header_and_never_leaks_it():
    env = make_global_env([])
    provider, token = run_source(
        'provider = config_provider([{kind: quote(values), values: {K: "SECRET_PAYLOAD_624"}}]) |> unwrap_or(none)\n'
        'token = secret_get(provider, "K", quote(http_send)) |> unwrap_or(none)\n'
        "[provider, token]",
        env,
    )
    authority = create_declassification_authority(
        provider, [symbol("http_send")], lambda event: None
    )
    operation = _operation(headers=GeniaMap().put("authorization", token))
    calls = []
    transport = _fake_transport(
        response=HttpTransportResponse(status=200, headers={}, body=b"ok"), calls=calls
    )

    result = perform_http_send(
        operation, GeniaOptionSome(authority), 2000,
        json_encode=_json_encode, invoke=_invoke, transport=transport,
    )

    assert isinstance(result, GeniaOptionSome)
    assert calls[0].headers["authorization"] == "SECRET_PAYLOAD_624"
    assert "SECRET_PAYLOAD_624" not in str(result.value)


def test_perform_http_send_query_percent_encoding_is_exact():
    calls = []
    transport = _fake_transport(
        response=HttpTransportResponse(status=200, headers={}, body=b""), calls=calls
    )
    operation = _operation(
        query=GeniaMap().put("b", "hello world").put("a", "x/y&z")
    )

    perform_http_send(
        operation, GeniaOptionNone("nil"), 2000,
        json_encode=_json_encode, invoke=_invoke, transport=transport,
    )

    assert calls[0].url == "http://example.invalid/items?a=x%2Fy%26z&b=hello%20world"


def test_perform_http_send_no_query_produces_no_question_mark():
    calls = []
    transport = _fake_transport(
        response=HttpTransportResponse(status=200, headers={}, body=b""), calls=calls
    )
    operation = _operation()

    perform_http_send(
        operation, GeniaOptionNone("nil"), 2000,
        json_encode=_json_encode, invoke=_invoke, transport=transport,
    )

    assert calls[0].url == "http://example.invalid/items"


def test_perform_http_send_text_body_encodes_utf8():
    calls = []
    transport = _fake_transport(
        response=HttpTransportResponse(status=200, headers={}, body=b""), calls=calls
    )
    operation = _operation(body=GeniaMap().put("kind", symbol("text")).put("text", "héllo"))

    perform_http_send(
        operation, GeniaOptionNone("nil"), 2000,
        json_encode=_json_encode, invoke=_invoke, transport=transport,
    )

    assert calls[0].body == "héllo".encode("utf-8")


def test_perform_http_send_json_body_uses_injected_json_encode():
    calls = []
    transport = _fake_transport(
        response=HttpTransportResponse(status=200, headers={}, body=b""), calls=calls
    )
    operation = _operation(body=GeniaMap().put("kind", symbol("json")).put("value", GeniaMap()))

    def json_encode(value):
        return GeniaOptionSome('{"k":"v"}')

    perform_http_send(
        operation, GeniaOptionNone("nil"), 2000,
        json_encode=json_encode, invoke=_invoke, transport=transport,
    )

    assert calls[0].body == b'{"k":"v"}'


def test_perform_http_send_none_body_sends_empty_bytes():
    calls = []
    transport = _fake_transport(
        response=HttpTransportResponse(status=200, headers={}, body=b""), calls=calls
    )
    operation = _operation()

    perform_http_send(
        operation, GeniaOptionNone("nil"), 2000,
        json_encode=_json_encode, invoke=_invoke, transport=transport,
    )

    assert calls[0].body == b""


def test_perform_http_send_response_headers_are_returned_as_supplied():
    transport = _fake_transport(
        response=HttpTransportResponse(status=200, headers={"X-Foo": "bar"}, body=b"")
    )
    operation = _operation()

    result = perform_http_send(
        operation, GeniaOptionNone("nil"), 2000,
        json_encode=_json_encode, invoke=_invoke, transport=transport,
    )

    assert result.value.get("headers").get("X-Foo") == "bar"


def test_perform_http_send_timeout_seconds_derived_from_timeout_ms():
    calls = []
    transport = _fake_transport(
        response=HttpTransportResponse(status=200, headers={}, body=b""), calls=calls
    )
    operation = _operation()

    perform_http_send(
        operation, GeniaOptionNone("nil"), 3000,
        json_encode=_json_encode, invoke=_invoke, transport=transport,
    )

    assert calls[0].timeout_seconds == 3.0


# --- Loopback: real server, real evaluator invocation via run_source ---


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class _FixtureHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"ok")

    def log_message(self, format, *args):  # noqa: A002
        pass


@pytest.mark.loopback
def test_http_send_via_genia_source_against_real_local_server():
    server = http.server.HTTPServer(("127.0.0.1", 0), _FixtureHandler)
    thread = threading.Thread(target=server.handle_request, daemon=True)
    thread.start()
    try:
        env = make_global_env([])
        source = f"""
import web

operation = http_operation(quote(get), "http://127.0.0.1:{server.server_port}", "/health", {{}}, {{}}, none("http-no-body")) |> unwrap_or(none)
result = web.http_send(operation, none("nil"), 2000)
display(result)
"""
        output = run_source(source, env)
    finally:
        thread.join(timeout=3)
        server.server_close()

    assert 'status: 200' in output
