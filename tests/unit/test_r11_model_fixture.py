import pytest

from genia.builtins import make_global_env
from genia.configuration import create_declassification_authority
from genia.interpreter import run_source
from genia.values import (
    GeniaMap,
    GeniaOptionErr,
    GeniaOptionSome,
    make_none,
    symbol,
)


KEY = "R11_MODEL_KEY_SENTINEL_611"
PAYLOAD = "R11_MODEL_PAYLOAD_SENTINEL_611"


def _map(**values):
    result = GeniaMap()
    for key, value in values.items():
        result = result.put(key, value)
    return result


def _text(value):
    return _map(kind=symbol("text"), text=value)


def _message(role, value):
    return _map(role=symbol(role), content=_text(value))


def _usage(input_tokens=2, output_tokens=3, total_tokens=5):
    return _map(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=total_tokens,
    )


def _response(*, usage=None):
    return _map(
        message=_message("assistant", "fixture reply"),
        finish_reason=symbol("stop"),
        usage=GeniaOptionSome(_usage()) if usage is None else usage,
    )


def _request():
    return _map(
        messages=[_message("user", "hello")],
        output=_map(kind=symbol("text")),
    )


def _fixture_env(result):
    from genia.model import create_fixture_model_provider

    env = make_global_env([])
    provider = run_source(
        "config_provider([{kind: quote(values), values: {"
        f'{KEY}: "{PAYLOAD}"'
        "}}]) |> unwrap_or(none)",
        env,
    )
    credential = run_source(
        f'secret_get(provider_fixture, "{KEY}", quote(model_call)) |> unwrap_or(none)',
        _env_with(env, provider_fixture=provider),
    )
    audits = []
    authority = create_declassification_authority(
        provider, [symbol("model_call")], audits.append
    )
    fixture = create_fixture_model_provider(lambda config, request, secret: result)
    env.set("provider_fixture", provider)
    env.set("model_provider_fixture", fixture)
    env.set("model_credential_fixture", credential)
    env.set("model_authority_fixture", authority)
    return env, fixture, audits


def _env_with(env, **values):
    for key, value in values.items():
        env.set(key, value)
    return env


def _model_source(request_source):
    return (
        'm = model(model_provider_fixture, {id: "fixture-text", timeout_ms: 1000}, '
        "model_credential_fixture, model_authority_fixture)\n"
        f"m({request_source})"
    )


VALID_REQUEST_SOURCE = (
    "{messages: [{role: quote(user), content: {kind: quote(text), text: \"hello\"}}], "
    "output: {kind: quote(text)}}"
)


def test_model_fixture_success_is_one_attempt_and_one_audit():
    env, fixture, audits = _fixture_env(GeniaOptionSome(_response()))

    result = run_source(_model_source(VALID_REQUEST_SOURCE), env)

    assert result == GeniaOptionSome(_response())
    assert fixture.attempt_count == 1
    assert len(audits) == 1 and audits[0]["success"] is True
    assert KEY not in repr(result) and PAYLOAD not in repr(result)


@pytest.mark.parametrize(
    "outcome",
    [
        make_none("model-no-response"),
        GeniaOptionErr("model-timeout", _map(timeout_ms=1000)),
        GeniaOptionErr(
            "model-rate-limited",
            _map(retry_after_ms=make_none("model-retry-after-unavailable")),
        ),
        GeniaOptionErr("model-rejected", _map(kind=symbol("policy"))),
        GeniaOptionErr("model-transport-failure", _map(kind=symbol("unavailable"))),
    ],
)
def test_model_fixture_preserves_approved_outcomes_once(outcome):
    env, fixture, audits = _fixture_env(outcome)
    assert run_source(_model_source(VALID_REQUEST_SOURCE), env) == outcome
    assert fixture.attempt_count == 1
    assert len(audits) == 1


@pytest.mark.parametrize(
    "request_source, message",
    [
        ("{messages: [], output: {kind: quote(text)}}", "non-empty messages"),
        (
            "{messages: [{role: quote(tool), content: {kind: quote(text), text: \"x\"}}], output: {kind: quote(text)}}",
            "message role",
        ),
        (
            "{messages: [{role: quote(user), content: {kind: quote(image), text: \"x\"}}], output: {kind: quote(text)}}",
            "content kind",
        ),
        (
            "{messages: [{role: quote(user), content: {kind: quote(text), text: \"x\", extra: 1}}], output: {kind: quote(text)}}",
            "closed content",
        ),
        (
            "{messages: [{role: quote(user), content: {kind: quote(text), text: \"x\"}}], output: {kind: quote(json)}}",
            "text output only",
        ),
    ],
)
def test_invalid_request_fails_before_declassification_or_attempt(request_source, message):
    env, fixture, audits = _fixture_env(GeniaOptionSome(_response()))
    with pytest.raises(TypeError, match=message):
        run_source(_model_source(request_source), env)
    assert fixture.attempt_count == 0
    assert audits == []


def test_malformed_fixture_response_normalizes_without_leaking_or_retrying():
    env, fixture, audits = _fixture_env(GeniaOptionSome(_response(usage=GeniaOptionSome(_usage(total_tokens=99)))))
    result = run_source(_model_source(VALID_REQUEST_SOURCE), env)
    assert result == GeniaOptionErr(
        "model-response-invalid", _map(stage=symbol("provider_response"))
    )
    assert fixture.attempt_count == 1
    assert len(audits) == 1


def test_fixture_exception_becomes_non_sensitive_transport_failure_once():
    from genia.model import create_fixture_model_provider

    env, _, audits = _fixture_env(GeniaOptionSome(_response()))

    def fail(config, request, secret):
        raise RuntimeError(f"provider exploded {KEY} {PAYLOAD}")

    fixture = create_fixture_model_provider(fail)
    env.set("model_provider_fixture", fixture)
    result = run_source(_model_source(VALID_REQUEST_SOURCE), env)
    assert result == GeniaOptionErr(
        "model-transport-failure", _map(kind=symbol("other"))
    )
    assert fixture.attempt_count == 1
    assert len(audits) == 1
    assert KEY not in repr(result) and PAYLOAD not in repr(result)


def test_model_config_is_closed_and_validated_without_side_effects():
    env, fixture, audits = _fixture_env(GeniaOptionSome(_response()))
    with pytest.raises(TypeError, match="closed config"):
        run_source(
            'model(model_provider_fixture, {id: "x", timeout_ms: 1000, extra: true}, '
            "model_credential_fixture, model_authority_fixture)",
            env,
        )
    with pytest.raises(TypeError, match="timeout_ms"):
        run_source(
            'model(model_provider_fixture, {id: "x", timeout_ms: true}, '
            "model_credential_fixture, model_authority_fixture)",
            env,
        )
    assert fixture.attempt_count == 0
    assert audits == []
