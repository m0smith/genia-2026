"""R14 E14-5 common HTTP operation representation core.

Implements the portable ``HttpOperation`` construction/validation contract
locked by the approved R14 contract
(``docs/design/r14-composable-lifecycle-contract.md``, "HTTP operation
representation" section, issue #622). ``construct_http_operation`` performs
no network IO of any kind — it only validates six fields and returns one
closed, ordinary map, or a staged ``err(...)``. The landed outbound client
in ``http_client.py`` owns activation and protected-header declassification;
``http_transport.py`` owns the private Python-host network attempt.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import Any

from .values import (
    GeniaMap,
    GeniaOptionErr,
    GeniaOptionNone,
    GeniaOptionSome,
    GeniaProtected,
    GeniaSymbol,
    make_none,
    symbol,
)

_METHODS = frozenset({"get", "post", "put", "patch", "delete"})
_BASE_URL_RE = re.compile(
    r"^(?P<scheme>https?)://(?P<host>[A-Za-z0-9.\-]+)(:(?P<port>[0-9]+))?$"
)
_NO_BODY_REASON = "http-no-body"
_TEXT_CONTENT_TYPE = "text/plain; charset=utf-8"
_JSON_CONTENT_TYPE = "application/json"
_CONTENT_TYPE_KEY = "content-type"


def _stage_error(stage: str) -> GeniaOptionErr:
    """Return a non-sensitive invalid-operation Outcome naming the first failed field."""
    return GeniaOptionErr("http-operation-invalid", GeniaMap().put("stage", symbol(stage)))


def _validate_method(value: Any) -> Any:
    """Accept only a Genia symbol naming get, post, put, patch or delete.

    Return some of the unchanged symbol, otherwise a method-stage error.
    """
    if isinstance(value, GeniaSymbol) and value.name in _METHODS:
        return GeniaOptionSome(value)
    return _stage_error("method")


def _validate_base_url(value: Any) -> Any:
    """Accept lowercase http(s)://host[:digits] with an ASCII host and no path.

    Host characters are letters, digits, dots and hyphens. The regex checks
    spelling only, not DNS reachability or port range; return some of the
    unchanged string or a base_url-stage error.
    """
    if isinstance(value, str) and _BASE_URL_RE.fullmatch(value):
        return GeniaOptionSome(value)
    return _stage_error("base_url")


def _validate_path(value: Any) -> Any:
    """Accept a string starting with / and containing neither ? nor #.

    Preserve its spelling without escaping or URL normalization; otherwise
    return a path-stage error.
    """
    if isinstance(value, str) and value.startswith("/") and "?" not in value and "#" not in value:
        return GeniaOptionSome(value)
    return _stage_error("path")


def _validate_headers(value: Any) -> Any:
    """Copy a GeniaMap to lowercase string keys, preserving header values.

    Values must be strings or exact protected carriers; no declassification
    occurs here. Reject non-string keys, unsupported values or collisions after
    lowercasing with a headers-stage error. No HTTP token validation is added.
    """
    if not isinstance(value, GeniaMap):
        return _stage_error("headers")
    normalized: dict[str, Any] = {}
    for key, header_value in value.items():
        if not isinstance(key, str):
            return _stage_error("headers")
        if not isinstance(header_value, (str, GeniaProtected)):
            return _stage_error("headers")
        lowered = key.lower()
        if lowered in normalized:
            return _stage_error("headers")
        normalized[lowered] = header_value
    result = GeniaMap()
    for lowered, header_value in normalized.items():
        result = result.put(lowered, header_value)
    return GeniaOptionSome(result)


def _validate_query(value: Any) -> Any:
    """Copy string-to-string GeniaMap entries without changing case or order.

    Return some of the copy, or a query-stage error for invalid entries,
    including protected values. URL encoding is deferred to the client.
    """
    if not isinstance(value, GeniaMap):
        return _stage_error("query")
    result = GeniaMap()
    for key, query_value in value.items():
        if not isinstance(key, str) or not isinstance(query_value, str):
            return _stage_error("query")
        result = result.put(key, query_value)
    return GeniaOptionSome(result)


def _validate_body(value: Any, json_encode: Callable[[Any], Any]) -> Any:
    """Normalize absence/text/JSON to some((body, implicit_content_type)).

    Any none reason becomes http-no-body with no content type. Text and JSON
    maps retain only their declared body fields; JSON requires a value key and
    a successful supplied json_encode Outcome, preserving the original value.
    Invalid bodies or encoder rejection return a body-stage error. Encoder
    exceptions propagate; encoding here validates only and performs no HTTP IO.
    """
    if isinstance(value, GeniaOptionNone):
        return GeniaOptionSome((make_none(_NO_BODY_REASON), None))
    if isinstance(value, GeniaMap):
        kind = value.get("kind")
        if kind == symbol("text"):
            text = value.get("text")
            if isinstance(text, str):
                body = GeniaMap().put("kind", symbol("text")).put("text", text)
                return GeniaOptionSome((body, _TEXT_CONTENT_TYPE))
            return _stage_error("body")
        if kind == symbol("json"):
            if not value.has("value"):
                return _stage_error("body")
            json_value = value.get("value")
            encoded = json_encode(json_value)
            if not isinstance(encoded, GeniaOptionSome):
                return _stage_error("body")
            body = GeniaMap().put("kind", symbol("json")).put("value", json_value)
            return GeniaOptionSome((body, _JSON_CONTENT_TYPE))
    return _stage_error("body")


def construct_http_operation(
    method: Any,
    base_url: Any,
    path: Any,
    headers: Any,
    query: Any,
    body: Any,
    json_encode: Callable[[Any], Any],
) -> Any:
    """``http_operation(method, base_url, path, headers, query, body)``.

    Validates each field in declared order, stopping at the first invalid
    one. Performs zero network IO. Returns ``some(HttpOperation)`` — one
    closed map with keys ``method, base_url, path, headers, query, body`` —
    or ``err("http-operation-invalid", {stage: quote(<field>)})``.

    Header names lowercase with collision rejection; protected header values
    retain their identity. Query strings stay unencoded. Body validation uses
    the supplied JSON encoder and adds a content type only when none was set.
    Callback exceptions propagate rather than becoming staged errors.
    """

    method_result = _validate_method(method)
    if not isinstance(method_result, GeniaOptionSome):
        return method_result

    base_url_result = _validate_base_url(base_url)
    if not isinstance(base_url_result, GeniaOptionSome):
        return base_url_result

    path_result = _validate_path(path)
    if not isinstance(path_result, GeniaOptionSome):
        return path_result

    headers_result = _validate_headers(headers)
    if not isinstance(headers_result, GeniaOptionSome):
        return headers_result

    query_result = _validate_query(query)
    if not isinstance(query_result, GeniaOptionSome):
        return query_result

    body_result = _validate_body(body, json_encode)
    if not isinstance(body_result, GeniaOptionSome):
        return body_result

    body_value, implicit_content_type = body_result.value
    normalized_headers = headers_result.value
    if implicit_content_type is not None and not normalized_headers.has(_CONTENT_TYPE_KEY):
        normalized_headers = normalized_headers.put(_CONTENT_TYPE_KEY, implicit_content_type)

    operation = (
        GeniaMap()
        .put("method", method_result.value)
        .put("base_url", base_url_result.value)
        .put("path", path_result.value)
        .put("headers", normalized_headers)
        .put("query", query_result.value)
        .put("body", body_value)
    )
    return GeniaOptionSome(operation)
