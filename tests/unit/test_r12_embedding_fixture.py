import math

import pytest

from genia.builtins import make_global_env
from genia.configuration import create_declassification_authority
from genia.interpreter import run_source
from genia.utf8 import format_debug, format_display
from genia.values import (
    GeniaMap,
    GeniaOptionErr,
    GeniaOptionNone,
    GeniaOptionSome,
    GeniaRepresented,
    make_none,
    symbol,
)


KEY = "R12_EMBED_KEY_SENTINEL_644"
PAYLOAD = "R12_EMBED_PAYLOAD_SENTINEL_644"
SPACE = "fixture-space-v1"


def _map(**values):
    result = GeniaMap()
    for key, value in values.items():
        result = result.put(key, value)
    return result


def _chunk(text="hello"):
    return _map(
        text=text,
        source=_map(doc_id="doc-1", offset=0, length=len(text)),
        meta=GeniaRepresented("json", _map(origin="fixture")),
    )


def _embedding(vector=None, dims=None, space=SPACE):
    vector = [0.25, -1, 3.5] if vector is None else vector
    return _map(
        vector=vector,
        dims=len(vector) if dims is None else dims,
        space=space,
    )


def _query_response(text="hello", **embedding):
    return _map(text=text, embedding=_embedding(**embedding))


def _chunk_response(chunk=None, **embedding):
    return _map(chunk=_chunk() if chunk is None else chunk, embedding=_embedding(**embedding))


def _env(handler):
    from genia.retrieval import create_fixture_embed_provider

    env = make_global_env([])
    provider = run_source(
        "config_provider([{kind: quote(values), values: {"
        f'{KEY}: "{PAYLOAD}"'
        "}}]) |> unwrap_or(none)",
        env,
    )
    env.set("provider_fixture", provider)
    credential = run_source(
        f'secret_get(provider_fixture, "{KEY}", quote(embed_call)) |> unwrap_or(none)',
        env,
    )
    audits = []
    authority = create_declassification_authority(
        provider, [symbol("embed_call")], audits.append
    )
    fixture = create_fixture_embed_provider(handler)
    env.set("embed_provider_fixture", fixture)
    env.set("embed_credential_fixture", credential)
    env.set("embed_authority_fixture", authority)
    return env, fixture, audits


def _source(input_source, config=None):
    config = config or f'{{id: "fixture", space: "{SPACE}", timeout_ms: 1000}}'
    return (
        f"e = embed(embed_provider_fixture, {config}, "
        "embed_credential_fixture, embed_authority_fixture)\n"
        f"e({input_source})"
    )


QUERY_SOURCE = '{kind: quote(query), text: "hello"}'


def test_query_embedding_preserves_text_and_attempts_once():
    seen = []

    def handler(config, embedding_input, credential):
        seen.append((config, embedding_input, credential))
        return GeniaOptionSome(_query_response())

    env, fixture, audits = _env(handler)
    result = run_source(_source(QUERY_SOURCE), env)

    assert isinstance(result, GeniaOptionSome)
    assert result.value.get("text") == "hello"
    assert result.value.get("embedding").get("vector") == [0.25, -1, 3.5]
    assert result.value.get("embedding").get("dims") == 3
    assert result.value.get("embedding").get("space") == SPACE
    assert "chunk" not in [key for key, _ in result.value.items()]
    assert fixture.attempt_count == 1
    assert len(audits) == 1 and audits[0]["success"] is True
    assert seen[0][1].get("kind") == symbol("query")
    assert seen[0][1].get("text") == "hello"
    assert seen[0][2] == PAYLOAD


def test_chunk_embedding_preserves_exact_chunk_and_metadata_identity():
    chunk = _chunk("hello")
    env, fixture, audits = _env(
        lambda _config, _input, _credential: GeniaOptionSome(_chunk_response(chunk))
    )
    env.set("chunk_fixture", chunk)

    result = run_source(
        _source("{kind: quote(chunk), chunk: chunk_fixture}"), env
    )

    assert isinstance(result, GeniaOptionSome)
    assert result.value.get("chunk") is chunk
    assert result.value.get("chunk").get("meta") is chunk.get("meta")
    assert fixture.attempt_count == 1
    assert len(audits) == 1


def test_constructor_is_inert_and_provider_is_opaque():
    env, fixture, audits = _env(
        lambda _config, _input, _credential: GeniaOptionSome(_query_response())
    )

    result = run_source(
        f'embed(embed_provider_fixture, {{id: "fixture", space: "{SPACE}", timeout_ms: 1000}}, '
        "embed_credential_fixture, embed_authority_fixture)",
        env,
    )

    assert repr(result) == "<function>"
    assert repr(fixture) == "<embed-provider>"
    assert format_display(fixture) == "<embed-provider>"
    assert format_debug(fixture) == "<embed-provider>"
    encoded = run_source("json_encode(embed_provider_fixture)", env)
    assert isinstance(encoded, GeniaOptionErr)
    with pytest.raises(TypeError, match="map key type is not supported"):
        GeniaMap().put(fixture, True)
    assert fixture.attempt_count == 0
    assert audits == []


@pytest.mark.parametrize(
    "config, message",
    [
        ('{id: "x", space: "s", timeout_ms: 1, extra: true}', "closed config"),
        ('{id: "", space: "s", timeout_ms: 1}', "config id"),
        ('{id: "x", space: "", timeout_ms: 1}', "config space"),
        ('{id: "x", space: "s", timeout_ms: true}', "timeout_ms"),
        ('{id: "x", space: "s", timeout_ms: 0}', "timeout_ms"),
        ('{id: "x", space: "s", timeout_ms: 300001}', "timeout_ms"),
    ],
)
def test_invalid_constructor_config_has_no_side_effects(config, message):
    env, fixture, audits = _env(
        lambda _config, _input, _credential: GeniaOptionSome(_query_response())
    )
    with pytest.raises(TypeError, match=message):
        run_source(
            f"embed(embed_provider_fixture, {config}, "
            "embed_credential_fixture, embed_authority_fixture)",
            env,
        )
    assert fixture.attempt_count == 0
    assert audits == []


@pytest.mark.parametrize(
    "input_source, message",
    [
        ('{kind: quote(query), text: ""}', "query text"),
        ('{kind: quote(query), text: "x", extra: 1}', "closed query input"),
        ('{kind: quote(chunk), text: "x"}', "closed chunk input"),
        ('{kind: quote(other), text: "x"}', "input kind"),
        ('"query"', "input map"),
    ],
)
def test_invalid_input_has_no_declassification_or_attempt(input_source, message):
    env, fixture, audits = _env(
        lambda _config, _input, _credential: GeniaOptionSome(_query_response())
    )
    with pytest.raises(TypeError, match=message):
        run_source(_source(input_source), env)
    assert fixture.attempt_count == 0
    assert audits == []


def test_protected_ordinary_input_is_rejected_without_attempt():
    env, fixture, audits = _env(
        lambda _config, _input, _credential: GeniaOptionSome(_query_response())
    )
    env.set("protected_text_fixture", env.get("embed_credential_fixture"))
    with pytest.raises(TypeError, match="protected-value: embed-input"):
        run_source(
            _source("{kind: quote(query), text: protected_text_fixture}"), env
        )
    assert fixture.attempt_count == 0
    assert audits == []


def test_malformed_chunk_returns_exact_error_without_attempt():
    env, fixture, audits = _env(
        lambda _config, _input, _credential: GeniaOptionSome(_chunk_response())
    )
    result = run_source(
        _source(
            '{kind: quote(chunk), chunk: {text: "x", source: '
            '{doc_id: "doc-1", offset: 0, length: 2}, meta: represent("json", {})}}'
        ),
        env,
    )
    assert format_display(result) == 'err("chunk-invalid", {stage: document})'
    assert fixture.attempt_count == 0
    assert audits == []


@pytest.mark.parametrize(
    "response, stage",
    [
        (_query_response(vector=[]), "vector"),
        (_query_response(vector=[True]), "vector"),
        (_query_response(vector=[math.nan]), "vector"),
        (_query_response(vector=[math.inf]), "vector"),
        (_query_response(vector=[1.0], dims=True), "dims"),
        (_query_response(vector=[1.0, 2.0], dims=1), "dims"),
        (_query_response(space="other-space"), "space"),
        (_query_response(text="replaced"), "input_identity"),
        (_map(text="hello"), "provider_response"),
    ],
)
def test_invalid_provider_success_normalizes_once(response, stage):
    env, fixture, audits = _env(
        lambda _config, _input, _credential: GeniaOptionSome(response)
    )
    result = run_source(_source(QUERY_SOURCE), env)
    assert format_display(result) == f'err("embed-response-invalid", {{stage: {stage}}})'
    assert fixture.attempt_count == 1
    assert len(audits) == 1


@pytest.mark.parametrize(
    "outcome",
    [
        GeniaOptionErr("embed-timeout", _map(timeout_ms=1000)),
        GeniaOptionErr(
            "embed-rate-limited",
            _map(retry_after_ms=make_none("embed-retry-after-unavailable")),
        ),
        GeniaOptionErr("embed-rate-limited", _map(retry_after_ms=GeniaOptionSome(0))),
        GeniaOptionErr("embed-rejected", _map(kind=symbol("policy"))),
        GeniaOptionErr(
            "embed-transport-failure", _map(kind=symbol("unavailable"))
        ),
    ],
)
def test_approved_provider_errors_are_preserved_once(outcome):
    env, fixture, audits = _env(lambda *_args: outcome)
    assert run_source(_source(QUERY_SOURCE), env) == outcome
    assert fixture.attempt_count == 1
    assert len(audits) == 1


@pytest.mark.parametrize(
    "observation",
    [
        GeniaOptionNone("embed-no-response"),
        GeniaOptionSome(_query_response(), _map(secret=PAYLOAD)),
        GeniaOptionErr("embed-timeout", _map(timeout_ms=999)),
        GeniaOptionErr("embed-rejected", _map(kind=symbol("provider-secret"))),
        "not an outcome",
    ],
)
def test_unapproved_provider_observation_is_non_sensitive_response_invalid(observation):
    env, fixture, audits = _env(lambda *_args: observation)
    result = run_source(_source(QUERY_SOURCE), env)
    assert format_display(result) == (
        'err("embed-response-invalid", {stage: provider_response})'
    )
    assert KEY not in repr(result) and PAYLOAD not in repr(result)
    assert SPACE not in repr(result)
    assert fixture.attempt_count == 1
    assert len(audits) == 1


def test_provider_exception_is_non_sensitive_transport_failure_without_retry():
    def fail(*_args):
        raise RuntimeError(f"provider exploded {KEY} {PAYLOAD} {SPACE}")

    env, fixture, audits = _env(fail)
    result = run_source(_source(QUERY_SOURCE), env)
    assert format_display(result) == (
        'err("embed-transport-failure", {kind: other})'
    )
    assert KEY not in repr(result) and PAYLOAD not in repr(result)
    assert SPACE not in repr(result)
    assert fixture.attempt_count == 1
    assert len(audits) == 1


def test_authority_mismatch_prevents_attempt():
    env, fixture, audits = _env(
        lambda _config, _input, _credential: GeniaOptionSome(_query_response())
    )
    provider = env.get("provider_fixture")
    env.set(
        "embed_authority_fixture",
        create_declassification_authority(
            provider, [symbol("model_call")], audits.append
        ),
    )
    with pytest.raises(TypeError, match="authority does not permit"):
        run_source(_source(QUERY_SOURCE), env)
    assert fixture.attempt_count == 0
    assert len(audits) == 1 and audits[0]["success"] is False


def test_fixture_factory_and_global_environment_are_narrow():
    from genia.retrieval import create_fixture_embed_provider

    with pytest.raises(TypeError, match="callable handler"):
        create_fixture_embed_provider(42)
    env = make_global_env([])
    for name in (
        "embed_provider_fixture",
        "embed_credential_fixture",
        "embed_authority_fixture",
        "embed_retry",
        "embed_batch",
        "retrieve",
        "index",
    ):
        assert name not in env.values
