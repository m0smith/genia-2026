"""Focused tests for the R14 E14-5 ``http_operation`` builtin (issue #622):
one inert, closed ``HttpOperation`` value construction with zero network
IO, per docs/design/r14-composable-lifecycle-contract.md's "HTTP operation
representation" section.

Peer-shape/identity tests use the real builtin fetched via
``make_global_env().get("http_operation")`` and plain Python values,
mirroring ``tests/unit/test_lifecycle_runtime.py``'s
``_lifecycle_config()`` helper pattern. The protected-header redaction
regression proof uses ``run_source``, mirroring
``tests/unit/test_lifecycle_config.py``.
"""

from __future__ import annotations

import pytest

from genia.builtins import make_global_env
from genia.interpreter import run_source
from genia.utf8 import format_debug, format_display
from genia.values import (
    GeniaConfigProvider,
    GeniaMap,
    GeniaOptionErr,
    GeniaOptionNone,
    GeniaOptionSome,
    GeniaProtected,
    make_none,
    symbol,
)


def _http_operation():
    return make_global_env().get("http_operation")


def _call(method="get", base_url="https://api.example.com", path="/v1/things",
           headers=None, query=None, body=None):
    op = _http_operation()
    return op(
        symbol(method) if isinstance(method, str) else method,
        base_url,
        path,
        headers if headers is not None else GeniaMap(),
        query if query is not None else GeniaMap(),
        body if body is not None else make_none("no-body"),
    )


def _stage(result):
    assert isinstance(result, GeniaOptionErr)
    assert result.reason == "http-operation-invalid"
    return result.context.get("stage")


# --- method --------------------------------------------------------------


@pytest.mark.parametrize("method", ["get", "post", "put", "patch", "delete"])
def test_http_operation_accepts_every_supported_method(method):
    result = _call(method=method)

    assert isinstance(result, GeniaOptionSome)
    op = result.value
    assert op.get("method") == symbol(method)


@pytest.mark.parametrize("bad_method", ["head", "options", "connect", "trace", "GET"])
def test_http_operation_rejects_unsupported_method_symbols(bad_method):
    result = _call(method=bad_method)

    assert _stage(result) == symbol("method")


def test_http_operation_rejects_non_symbol_method():
    op = _http_operation()
    result = op("get", "https://api.example.com", "/v1/things", GeniaMap(), GeniaMap(), make_none("no-body"))

    assert _stage(result) == symbol("method")


# --- base_url --------------------------------------------------------------


@pytest.mark.parametrize(
    "base_url",
    [
        "https://api.example.com",
        "http://api.example.com",
        "https://api.example.com:8443",
        "http://a",
        "https://sub.domain-name.example.com:1",
    ],
)
def test_http_operation_accepts_valid_base_urls(base_url):
    result = _call(base_url=base_url)

    assert isinstance(result, GeniaOptionSome)
    assert result.value.get("base_url") == base_url


@pytest.mark.parametrize(
    "base_url",
    [
        "ftp://api.example.com",
        "api.example.com",
        "https://",
        "https://user@api.example.com",
        "https://api.example.com/path",
        "https://api.example.com?x=1",
        "https://api.example.com#frag",
        "https://api.example.com:notaport",
        "",
    ],
)
def test_http_operation_rejects_invalid_base_urls(base_url):
    result = _call(base_url=base_url)

    assert _stage(result) == symbol("base_url")


# --- path --------------------------------------------------------------


@pytest.mark.parametrize("path", ["/", "/v1/things", "/a/b/c", "/weird%20but%20passthrough"])
def test_http_operation_accepts_valid_paths_byte_for_byte(path):
    result = _call(path=path)

    assert isinstance(result, GeniaOptionSome)
    assert result.value.get("path") == path


@pytest.mark.parametrize("path", ["things", "/things?x=1", "/things#frag", ""])
def test_http_operation_rejects_invalid_paths(path):
    result = _call(path=path)

    assert _stage(result) == symbol("path")


# --- headers --------------------------------------------------------------


def test_http_operation_lowercases_header_keys():
    headers = GeniaMap().put("X-Trace-Id", "abc")
    result = _call(headers=headers)

    assert isinstance(result, GeniaOptionSome)
    assert result.value.get("headers").get("x-trace-id") == "abc"
    assert isinstance(result.value.get("headers").get("X-Trace-Id"), GeniaOptionNone)


def test_http_operation_rejects_case_insensitive_header_collision():
    headers = GeniaMap().put("X-Trace-Id", "abc").put("x-trace-id", "def")
    result = _call(headers=headers)

    assert _stage(result) == symbol("headers")


def test_http_operation_preserves_a_protected_header_value_by_identity():
    protected = GeniaProtected("super-secret", object(), symbol("http_send"))
    headers = GeniaMap().put("authorization", protected)
    result = _call(headers=headers)

    assert isinstance(result, GeniaOptionSome)
    assert result.value.get("headers").get("authorization") is protected


def test_http_operation_rejects_non_string_non_protected_header_value():
    headers = GeniaMap().put("x-count", 5)
    result = _call(headers=headers)

    assert _stage(result) == symbol("headers")


def test_http_operation_rejects_non_map_headers():
    op = _http_operation()
    result = op(symbol("get"), "https://api.example.com", "/x", "not-a-map", GeniaMap(), make_none("no-body"))

    assert _stage(result) == symbol("headers")


# --- query --------------------------------------------------------------


def test_http_operation_accepts_plain_string_query_entries_unmodified_keys():
    query = GeniaMap().put("Q", "1").put("limit", "10")
    result = _call(query=query)

    assert isinstance(result, GeniaOptionSome)
    out = result.value.get("query")
    assert out.get("Q") == "1"
    assert out.get("limit") == "10"


def test_http_operation_rejects_protected_value_in_query():
    protected = GeniaProtected("leak", object(), symbol("http_send"))
    query = GeniaMap().put("token", protected)
    result = _call(query=query)

    assert _stage(result) == symbol("query")


def test_http_operation_rejects_non_string_query_value():
    query = GeniaMap().put("limit", 10)
    result = _call(query=query)

    assert _stage(result) == symbol("query")


# --- body --------------------------------------------------------------


def test_http_operation_defaults_body_to_no_body_regardless_of_caller_reason():
    for reason in ("no-body", "http-no-body", "anything"):
        result = _call(body=make_none(reason))

        assert isinstance(result, GeniaOptionSome)
        body = result.value.get("body")
        assert isinstance(body, GeniaOptionNone)
        assert body.reason == "http-no-body"


def test_http_operation_no_body_adds_no_implicit_content_type():
    result = _call(body=make_none("no-body"))

    assert isinstance(result, GeniaOptionSome)
    assert isinstance(result.value.get("headers").get("content-type"), GeniaOptionNone)


def test_http_operation_text_body_injects_implicit_content_type_when_absent():
    body = GeniaMap().put("kind", symbol("text")).put("text", "hello")
    result = _call(body=body)

    assert isinstance(result, GeniaOptionSome)
    op = result.value
    assert op.get("body").get("kind") == symbol("text")
    assert op.get("body").get("text") == "hello"
    assert op.get("headers").get("content-type") == "text/plain; charset=utf-8"


def test_http_operation_text_body_never_overwrites_explicit_content_type():
    body = GeniaMap().put("kind", symbol("text")).put("text", "hello")
    headers = GeniaMap().put("Content-Type", "text/markdown")
    result = _call(headers=headers, body=body)

    assert isinstance(result, GeniaOptionSome)
    assert result.value.get("headers").get("content-type") == "text/markdown"


def test_http_operation_json_body_injects_implicit_content_type_when_absent():
    body = GeniaMap().put("kind", symbol("json")).put("value", GeniaMap().put("a", 1))
    result = _call(body=body)

    assert isinstance(result, GeniaOptionSome)
    op = result.value
    assert op.get("body").get("kind") == symbol("json")
    assert op.get("headers").get("content-type") == "application/json"


def test_http_operation_json_body_never_overwrites_explicit_content_type():
    body = GeniaMap().put("kind", symbol("json")).put("value", GeniaMap().put("a", 1))
    headers = GeniaMap().put("content-type", "application/vnd.custom+json")
    result = _call(headers=headers, body=body)

    assert isinstance(result, GeniaOptionSome)
    assert result.value.get("headers").get("content-type") == "application/vnd.custom+json"


def test_http_operation_json_body_with_protected_leaf_fails_at_body_stage():
    protected = GeniaProtected("secret", object(), symbol("http_send"))
    body = GeniaMap().put("kind", symbol("json")).put("value", GeniaMap().put("token", protected))
    result = _call(body=body)

    assert _stage(result) == symbol("body")


@pytest.mark.parametrize(
    "body",
    [
        GeniaMap().put("kind", symbol("bogus")).put("text", "x"),
        GeniaMap().put("kind", symbol("text")),
        GeniaMap().put("kind", symbol("json")),
        "not-a-body-shape",
        42,
    ],
)
def test_http_operation_rejects_malformed_body_shapes(body):
    result = _call(body=body)

    assert _stage(result) == symbol("body")


# --- validation order / determinism ----------------------------------------


def test_http_operation_reports_the_first_invalid_field_in_declared_order():
    # Both method and base_url are invalid here; method is validated first.
    op = _http_operation()
    result = op("get", "not-a-url", "/x", GeniaMap(), GeniaMap(), make_none("no-body"))

    assert _stage(result) == symbol("method")


# --- protected-header non-leakage regression (R10) --------------------------


def test_http_operation_protected_header_redacts_under_display_and_debug():
    provider = GeniaConfigProvider(({"API_KEY": "super-secret-value"},))
    env = make_global_env([])
    env.set("provider", provider)
    src = """
    key = unwrap_or(none, secret_get(provider, "API_KEY", quote(http_send)))
    op = http_operation(quote(get), "https://api.example.com", "/v1/things", {authorization: key}, {}, none("no-body"))
    op
    """
    result = run_source(src, env)

    assert isinstance(result, GeniaOptionSome)
    op = result.value
    protected = op.get("headers").get("authorization")
    assert isinstance(protected, GeniaProtected)

    rendered_op = format_display(op)
    assert "super-secret-value" not in rendered_op
    assert "<protected>" in rendered_op
    assert "super-secret-value" not in format_debug(op)
