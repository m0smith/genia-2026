import json
import socket
import urllib.error

import pytest

from genia.builtins import make_global_env
from genia.configuration import create_declassification_authority
from genia.interpreter import run_source
from genia.utf8 import format_display
from genia.values import GeniaMap, GeniaOptionErr, GeniaOptionNone, GeniaOptionSome, symbol

from genia.gemini_rest import (
    GeminiRestResponse,
    create_gemini_rest_model_provider,
)


KEY = "GEMINI_KEY_SENTINEL_613"
CREDENTIAL = "GEMINI_CREDENTIAL_SENTINEL_613"


def _map(**values):
    result = GeniaMap()
    for key, value in values.items():
        result = result.put(key, value)
    return result


def _env(transport, *, purpose="model_call", authority_provider=None):
    env = make_global_env([])
    provider = run_source(
        'config_provider([{kind: quote(values), values: {'
        f'{KEY}: "{CREDENTIAL}"'
        "}}]) |> unwrap_or(none)",
        env,
    )
    credential = run_source(
        f'secret_get(provider_fixture, "{KEY}", quote({purpose})) |> unwrap_or(none)',
        _set(env, provider_fixture=provider),
    )
    audits = []
    authority = create_declassification_authority(
        provider if authority_provider is None else authority_provider,
        [symbol("model_call")],
        audits.append,
    )
    capability = create_gemini_rest_model_provider(transport)
    _set(
        env,
        model_provider_fixture=capability,
        model_credential_fixture=credential,
        model_authority_fixture=authority,
    )
    return env, capability, audits


def _set(env, **values):
    for key, value in values.items():
        env.set(key, value)
    return env


def _source(*, model_id="gemini-3.1-flash-lite", request=None):
    request = request or (
        "{messages: ["
        '{role: quote(system), content: {kind: quote(text), text: "be concise"}}, '
        '{role: quote(user), content: {kind: quote(text), text: "hello"}}, '
        '{role: quote(assistant), content: {kind: quote(text), text: "hi"}}], '
        "output: {kind: quote(text)}}"
    )
    return (
        f'm = model(model_provider_fixture, {{id: "{model_id}", timeout_ms: 1250}}, '
        "model_credential_fixture, model_authority_fixture)\n"
        f"m({request})"
    )


def _success(*, finish="STOP", usage=True, text_parts=("fixture ", "reply")):
    payload = {
        "candidates": [
            {
                "content": {
                    "role": "model",
                    "parts": [{"text": text} for text in text_parts],
                },
                "finishReason": finish,
            }
        ]
    }
    if usage:
        payload["usageMetadata"] = {
            "promptTokenCount": 2,
            "candidatesTokenCount": 3,
            "totalTokenCount": 5,
        }
    return GeminiRestResponse(200, {}, json.dumps(payload).encode())


def test_gemini_rest_text_translation_is_one_audited_attempt():
    observed = []

    def transport(request):
        observed.append(request)
        return _success()

    env, capability, audits = _env(transport)
    result = run_source(_source(), env)

    assert format_display(result) == (
        "some({message: {role: assistant, content: {kind: text, text: fixture reply}}, "
        "finish_reason: stop, usage: some({input_tokens: 2, output_tokens: 3, total_tokens: 5})})"
    )
    assert capability.attempt_count == 1
    assert len(observed) == 1
    request = observed[0]
    assert request.url == (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        "gemini-3.1-flash-lite:generateContent"
    )
    assert request.timeout_seconds == 1.25
    assert request.headers == {
        "Content-Type": "application/json",
        "x-goog-api-key": CREDENTIAL,
    }
    assert json.loads(request.body) == {
        "systemInstruction": {"parts": [{"text": "be concise"}]},
        "contents": [
            {"role": "user", "parts": [{"text": "hello"}]},
            {"role": "model", "parts": [{"text": "hi"}]},
        ],
    }
    assert len(audits) == 1 and audits[0]["success"] is True
    assert KEY not in repr(audits) and CREDENTIAL not in repr(audits)


def test_gemini_rest_json_translation_uses_existing_represented_schema():
    observed = []
    request = (
        "{messages: [{role: quote(user), content: {kind: quote(text), text: \"return 7\"}}], "
        "output: {kind: quote(json), "
        'schema: json_decode("{\\"type\\":\\"integer\\"}") |> unwrap_or({}), '
        "template: (_) -> some(true)}}"
    )
    env, _, _ = _env(lambda value: observed.append(value) or _success(text_parts=("7",)))

    result = run_source(_source(request=request), env)

    body = json.loads(observed[0].body)
    assert body["generationConfig"] == {
        "responseMimeType": "application/json",
        "responseJsonSchema": {"type": "integer"},
    }
    assert result.value.get("message").get("content").get("kind") == symbol("json")


@pytest.mark.parametrize(
    "finish, expected",
    [
        ("MAX_TOKENS", "length"),
        ("SAFETY", "filtered"),
        ("RECITATION", "filtered"),
        ("OTHER", "other"),
    ],
)
def test_gemini_finish_reason_mapping(finish, expected):
    env, _, _ = _env(lambda _: _success(finish=finish))
    result = run_source(_source(), env)
    assert result.value.get("finish_reason") == symbol(expected)


def test_gemini_absent_candidate_and_usage_normalize_without_retry():
    responses = [
        GeminiRestResponse(200, {}, b'{"candidates": []}'),
        _success(usage=False),
    ]
    for response in responses:
        env, capability, _ = _env(lambda _: response)
        result = run_source(_source(), env)
        assert capability.attempt_count == 1
        if response.body == b'{"candidates": []}':
            assert isinstance(result, GeniaOptionNone)
            assert result.reason == "model-no-response"
        else:
            assert isinstance(result.value.get("usage"), GeniaOptionNone)


@pytest.mark.parametrize(
    "status, headers, reason, kind",
    [
        (408, {}, "model-timeout", None),
        (504, {}, "model-timeout", None),
        (429, {"Retry-After": "2"}, "model-rate-limited", None),
        (429, {"Retry-After": "secret"}, "model-rate-limited", None),
        (401, {}, "model-rejected", "authentication"),
        (403, {}, "model-rejected", "permission"),
        (400, {}, "model-rejected", "request"),
        (500, {}, "model-transport-failure", "unavailable"),
    ],
)
def test_gemini_http_failures_normalize_once(status, headers, reason, kind):
    response = GeminiRestResponse(status, headers, f"raw {KEY} {CREDENTIAL}".encode())
    env, capability, audits = _env(lambda _: response)
    result = run_source(_source(), env)

    assert isinstance(result, GeniaOptionErr) and result.reason == reason
    assert capability.attempt_count == 1 and len(audits) == 1
    if kind is not None:
        assert result.context.get("kind") == symbol(kind)
    if status == 429:
        retry = result.context.get("retry_after_ms")
        if headers["Retry-After"] == "2":
            assert isinstance(retry, GeniaOptionSome) and retry.value == 2000
        else:
            assert isinstance(retry, GeniaOptionNone)
    assert KEY not in repr(result) and CREDENTIAL not in repr(result)


@pytest.mark.parametrize("error", [TimeoutError("sentinel"), socket.timeout("sentinel")])
def test_gemini_local_timeout_normalizes(error):
    def transport(_):
        raise error

    env, capability, _ = _env(transport)
    result = run_source(_source(), env)
    assert isinstance(result, GeniaOptionErr)
    assert result.reason == "model-timeout"
    assert result.context.get("timeout_ms") == 1250
    assert capability.attempt_count == 1


def test_gemini_connection_error_and_malformed_success_do_not_leak():
    cases = [
        (urllib.error.URLError(f"dns {KEY} {CREDENTIAL}"), "model-transport-failure"),
        (None, "model-response-invalid"),
    ]
    for error, reason in cases:
        def transport(_, error=error):
            if error is not None:
                raise error
            return GeminiRestResponse(200, {}, f"not-json {KEY} {CREDENTIAL}".encode())

        env, capability, audits = _env(transport)
        result = run_source(_source(), env)
        assert isinstance(result, GeniaOptionErr) and result.reason == reason
        assert capability.attempt_count == 1 and len(audits) == 1
        assert KEY not in repr(result) and CREDENTIAL not in repr(result)


def test_validation_and_authority_failures_have_zero_transport_attempts():
    observed = []
    env, capability, audits = _env(lambda value: observed.append(value) or _success())
    with pytest.raises(TypeError, match="non-empty messages"):
        run_source(_source(request="{messages: [], output: {kind: quote(text)}}"), env)
    assert capability.attempt_count == 0 and observed == [] and audits == []

    other_env = make_global_env([])
    other_provider = run_source(
        'config_provider([{kind: quote(values), values: {OTHER: "value"}}]) |> unwrap_or(none)',
        other_env,
    )
    env, capability, audits = _env(
        lambda value: observed.append(value) or _success(),
        authority_provider=other_provider,
    )
    with pytest.raises(TypeError, match="does not permit"):
        run_source(_source(), env)
    assert capability.attempt_count == 0 and observed == []
    assert len(audits) == 1 and audits[0]["success"] is False


def test_default_transport_is_not_exercised_by_construction():
    capability = create_gemini_rest_model_provider()
    assert repr(capability) == "<model-provider>"
    assert capability.attempt_count == 0
