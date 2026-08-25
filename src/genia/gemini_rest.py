"""Experimental Python-host Gemini REST adapter for the R11 model boundary."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
import json
import socket
from typing import Any
import urllib.error
import urllib.parse
import urllib.request

from .model import GeniaModelProvider
from .values import (
    GeniaMap,
    GeniaOptionErr,
    GeniaOptionNone,
    GeniaOptionSome,
    GeniaRepresented,
    symbol,
)


_ORIGIN = "https://generativelanguage.googleapis.com"
_FILTERED_REASONS = {
    "BLOCKLIST",
    "IMAGE_SAFETY",
    "PROHIBITED_CONTENT",
    "RECITATION",
    "SAFETY",
    "SPII",
}


@dataclass(frozen=True)
class GeminiRestRequest:
    """Private unary request supplied to the host transport."""

    url: str
    headers: Mapping[str, str]
    body: bytes
    timeout_seconds: float


@dataclass(frozen=True)
class GeminiRestResponse:
    """Private unary response returned by the host transport."""

    status: int
    headers: Mapping[str, str]
    body: bytes


GeminiRestTransport = Callable[[GeminiRestRequest], GeminiRestResponse]


def _map(**values: Any) -> GeniaMap:
    result = GeniaMap()
    for key, value in values.items():
        result = result.put(key, value)
    return result


def _ordinary_json(value: Any) -> Any:
    if isinstance(value, GeniaMap):
        result: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError("Gemini JSON schema keys must be strings")
            result[key] = _ordinary_json(item)
        return result
    if isinstance(value, list):
        return [_ordinary_json(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError("Gemini JSON schema contains an unsupported value")


def _translate_request(
    config: GeniaMap, request: GeniaMap, credential: str
) -> GeminiRestRequest:
    systems: list[dict[str, str]] = []
    contents: list[dict[str, Any]] = []
    for message in request.get("messages"):
        role = message.get("role").name
        text = message.get("content").get("text")
        part = {"text": text}
        if role == "system":
            systems.append(part)
        else:
            contents.append(
                {"role": "model" if role == "assistant" else "user", "parts": [part]}
            )
    body: dict[str, Any] = {"contents": contents}
    if systems:
        body["systemInstruction"] = {"parts": systems}
    output = request.get("output")
    if output.get("kind") == symbol("json"):
        schema = output.get("schema")
        if not isinstance(schema, GeniaRepresented) or schema.facet != "json":
            raise TypeError("model expected one outer JSON represented schema")
        body["generationConfig"] = {
            "responseMimeType": "application/json",
            "responseJsonSchema": _ordinary_json(schema.value),
        }
    model_id = urllib.parse.quote(config.get("id"), safe="")
    return GeminiRestRequest(
        url=f"{_ORIGIN}/v1beta/models/{model_id}:generateContent",
        headers={"Content-Type": "application/json", "x-goog-api-key": credential},
        body=json.dumps(body, ensure_ascii=False, separators=(",", ":")).encode("utf-8"),
        timeout_seconds=config.get("timeout_ms") / 1000,
    )


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        return None


def _default_transport(request: GeminiRestRequest) -> GeminiRestResponse:
    wire_request = urllib.request.Request(
        request.url,
        data=request.body,
        headers=dict(request.headers),
        method="POST",
    )
    opener = urllib.request.build_opener(_NoRedirect)
    try:
        with opener.open(wire_request, timeout=request.timeout_seconds) as response:
            return GeminiRestResponse(
                response.status,
                dict(response.headers.items()),
                response.read(),
            )
    except urllib.error.HTTPError as error:
        try:
            body = error.read()
        finally:
            error.close()
        return GeminiRestResponse(error.code, dict(error.headers.items()), body)


def _header(headers: Mapping[str, str], name: str) -> str | None:
    lowered = name.lower()
    for key, value in headers.items():
        if key.lower() == lowered:
            return value
    return None


def _http_failure(response: GeminiRestResponse, timeout_ms: int) -> GeniaOptionErr:
    status = response.status
    if status in {408, 504}:
        return GeniaOptionErr("model-timeout", _map(timeout_ms=timeout_ms))
    if status == 429:
        raw_retry = _header(response.headers, "retry-after")
        retry: Any = GeniaOptionNone("model-retry-after-unavailable")
        if raw_retry is not None:
            try:
                seconds = int(raw_retry)
            except (TypeError, ValueError):
                pass
            else:
                if seconds >= 0:
                    retry = GeniaOptionSome(seconds * 1000)
        return GeniaOptionErr("model-rate-limited", _map(retry_after_ms=retry))
    if status == 401:
        return GeniaOptionErr("model-rejected", _map(kind=symbol("authentication")))
    if status == 403:
        return GeniaOptionErr("model-rejected", _map(kind=symbol("permission")))
    if 400 <= status < 500:
        return GeniaOptionErr("model-rejected", _map(kind=symbol("request")))
    if 500 <= status < 600:
        return GeniaOptionErr(
            "model-transport-failure", _map(kind=symbol("unavailable"))
        )
    return GeniaOptionErr("model-transport-failure", _map(kind=symbol("other")))


def _invalid(stage: str = "provider_response") -> GeniaOptionErr:
    return GeniaOptionErr("model-response-invalid", _map(stage=symbol(stage)))


def _normalize_success(response: GeminiRestResponse) -> Any:
    try:
        payload = json.loads(response.body)
    except (UnicodeDecodeError, json.JSONDecodeError, TypeError):
        return _invalid()
    if not isinstance(payload, dict):
        return _invalid()
    candidates = payload.get("candidates")
    if not isinstance(candidates, list):
        return _invalid()
    if not candidates:
        prompt_feedback = payload.get("promptFeedback")
        if isinstance(prompt_feedback, dict) and prompt_feedback.get("blockReason"):
            return GeniaOptionErr("model-rejected", _map(kind=symbol("policy")))
        return GeniaOptionNone("model-no-response")
    candidate = candidates[0]
    if not isinstance(candidate, dict):
        return _invalid()
    content = candidate.get("content")
    if not isinstance(content, dict) or content.get("role") != "model":
        return _invalid("message")
    parts = content.get("parts")
    if not isinstance(parts, list) or not parts:
        return _invalid("message")
    text_parts: list[str] = []
    for part in parts:
        if not isinstance(part, dict) or not isinstance(part.get("text"), str):
            return _invalid("message")
        text_parts.append(part["text"])
    raw_finish = candidate.get("finishReason")
    if not isinstance(raw_finish, str):
        return _invalid("finish_reason")
    if raw_finish == "STOP":
        finish = "stop"
    elif raw_finish == "MAX_TOKENS":
        finish = "length"
    elif raw_finish in _FILTERED_REASONS:
        finish = "filtered"
    else:
        finish = "other"
    raw_usage = payload.get("usageMetadata")
    if raw_usage is None:
        usage: Any = GeniaOptionNone("model-usage-unavailable")
    elif isinstance(raw_usage, dict):
        usage = GeniaOptionSome(
            _map(
                input_tokens=raw_usage.get("promptTokenCount"),
                output_tokens=raw_usage.get("candidatesTokenCount"),
                total_tokens=raw_usage.get("totalTokenCount"),
            )
        )
    else:
        return _invalid("usage")
    return GeniaOptionSome(
        _map(
            message=_map(
                role=symbol("assistant"),
                content=_map(kind=symbol("text"), text="".join(text_parts)),
            ),
            finish_reason=symbol(finish),
            usage=usage,
        )
    )


def _handler(transport: GeminiRestTransport) -> Callable[[GeniaMap, GeniaMap, str], Any]:
    def attempt(config: GeniaMap, request: GeniaMap, credential: str) -> Any:
        private_request = _translate_request(config, request, credential)
        try:
            response = transport(private_request)
        except (TimeoutError, socket.timeout):
            return GeniaOptionErr(
                "model-timeout", _map(timeout_ms=config.get("timeout_ms"))
            )
        except urllib.error.URLError:
            return GeniaOptionErr(
                "model-transport-failure", _map(kind=symbol("unavailable"))
            )
        except Exception:
            return GeniaOptionErr(
                "model-transport-failure", _map(kind=symbol("other"))
            )
        if not isinstance(response, GeminiRestResponse):
            return _invalid()
        if response.status != 200:
            return _http_failure(response, config.get("timeout_ms"))
        return _normalize_success(response)

    return attempt


def create_gemini_rest_model_provider(
    transport: GeminiRestTransport | None = None,
) -> GeniaModelProvider:
    """Create one explicit opaque Gemini REST model-provider capability."""

    selected = _default_transport if transport is None else transport
    if not callable(selected):
        raise TypeError("Gemini REST model provider expected a callable transport")
    return GeniaModelProvider(_handler(selected))
