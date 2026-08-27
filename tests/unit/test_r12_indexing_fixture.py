import copy

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
    symbol,
)


KEY = "R12_INDEX_KEY_SENTINEL_645"
PAYLOAD = "R12_INDEX_PAYLOAD_SENTINEL_645"
CONFIG_ID = "R12_INDEX_CONFIG_SENTINEL_645"
SPACE = "fixture-space-v1"


def _map(**values):
    result = GeniaMap()
    for key, value in values.items():
        result = result.put(key, value)
    return result


def _chunk(text="hello", doc_id="doc-1"):
    return _map(
        text=text,
        source=_map(doc_id=doc_id, offset=0, length=len(text)),
        meta=GeniaRepresented("json", _map(origin="fixture")),
    )


def _embedded(text="hello", vector=None, dims=None, space=SPACE, doc_id="doc-1"):
    vector = [0.25, -1, 3.5] if vector is None else vector
    return _map(
        chunk=_chunk(text, doc_id),
        embedding=_map(
            vector=vector,
            dims=len(vector) if dims is None else dims,
            space=space,
        ),
    )


def _env(handler):
    from genia.retrieval import create_fixture_index_provider

    env = make_global_env([])
    config_provider = run_source(
        "config_provider([{kind: quote(values), values: {"
        f'{KEY}: "{PAYLOAD}"'
        "}}]) |> unwrap_or(none)",
        env,
    )
    credential = run_source(
        f'secret_get(provider_fixture, "{KEY}", quote(index_call)) |> unwrap_or(none)',
        _env_with(env, "provider_fixture", config_provider),
    )
    audits = []
    authority = create_declassification_authority(
        config_provider, [symbol("index_call")], audits.append
    )
    fixture = create_fixture_index_provider(handler)
    env.set("index_provider_fixture", fixture)
    env.set("index_credential_fixture", credential)
    env.set("index_authority_fixture", authority)
    return env, fixture, audits


def _env_with(env, name, value):
    env.set(name, value)
    return env


def _source(corpus="embedded_fixture", config=None):
    config = config or f'{{id: "{CONFIG_ID}", timeout_ms: 1000}}'
    return (
        f"i = index(index_provider_fixture, {config}, "
        "index_credential_fixture, index_authority_fixture)\n"
        f"i({corpus})"
    )


def test_compatible_corpus_attempts_once_and_returns_only_opaque_handle():
    from genia.retrieval import create_fixture_index_result

    seen = []
    backend_ref = object()

    def handler(config, corpus, credential):
        seen.append((config, corpus, credential))
        return GeniaOptionSome(create_fixture_index_result(backend_ref))

    env, fixture, audits = _env(handler)
    corpus = [_embedded(), _embedded("world", doc_id="doc-2")]
    env.set("embedded_fixture", corpus)

    result = run_source(_source(), env)

    assert isinstance(result, GeniaOptionSome)
    handle = result.value
    assert repr(handle) == "<index-handle>"
    assert format_display(handle) == "<index-handle>"
    assert format_debug(handle) == "<index-handle>"
    assert format_display(result) == "some(<index-handle>)"
    assert fixture.attempt_count == 1
    assert len(audits) == 1 and audits[0]["success"] is True
    assert seen == [(seen[0][0], corpus, PAYLOAD)]
    assert seen[0][0].get("id") == CONFIG_ID
    assert fixture._handle_is_compatible_for_test(handle, SPACE, 3)
    assert fixture._backend_ref_for_test(handle) is backend_ref


def test_each_success_creates_a_distinct_non_comparable_handle():
    from genia.retrieval import create_fixture_index_result

    env, fixture, audits = _env(
        lambda *_args: GeniaOptionSome(create_fixture_index_result(object()))
    )
    env.set("embedded_fixture", [_embedded()])

    first = run_source(_source(), env).value
    second = run_source(_source(), env).value

    assert first is not second
    with pytest.raises(TypeError, match="index handles cannot be compared"):
        _ = first == second
    assert fixture.attempt_count == 2
    assert len(audits) == 2


def test_constructor_is_inert_and_capability_is_opaque():
    from genia.retrieval import create_fixture_index_result

    env, fixture, audits = _env(
        lambda *_args: GeniaOptionSome(create_fixture_index_result(object()))
    )
    result = run_source(
        f'index(index_provider_fixture, {{id: "{CONFIG_ID}", timeout_ms: 1000}}, '
        "index_credential_fixture, index_authority_fixture)",
        env,
    )

    assert repr(result) == "<function>"
    assert repr(fixture) == "<index-provider>"
    assert format_display(fixture) == "<index-provider>"
    assert fixture.attempt_count == 0
    assert audits == []


@pytest.mark.parametrize(
    "config, message",
    [
        ('{id: "x", timeout_ms: 1, extra: true}', "closed config"),
        ('{id: "", timeout_ms: 1}', "config id"),
        ('{id: "x", timeout_ms: true}', "timeout_ms"),
        ('{id: "x", timeout_ms: 0}', "timeout_ms"),
        ('{id: "x", timeout_ms: 300001}', "timeout_ms"),
    ],
)
def test_invalid_constructor_config_is_inert(config, message):
    env, fixture, audits = _env(lambda *_args: None)
    with pytest.raises(TypeError, match=message):
        run_source(_source("[]", config), env)
    assert fixture.attempt_count == 0
    assert audits == []


def test_empty_input_is_runtime_misuse_before_declassification_or_attempt():
    env, fixture, audits = _env(lambda *_args: None)
    with pytest.raises(TypeError, match="non-empty list"):
        run_source(_source("[]"), env)
    assert fixture.attempt_count == 0
    assert audits == []


@pytest.mark.parametrize(
    "corpus, expected",
    [
        ([_embedded(vector=[])], 'err("embedding-invalid", {stage: vector})'),
        ([_embedded(dims=2)], 'err("embedding-invalid", {stage: dims})'),
        ([_embedded(space="")], 'err("embedding-invalid", {stage: space})'),
        (
            [_embedded(), _embedded(vector=[1, 2], dims=2)],
            'err("index-embedding-incompatible", {kind: dimension})',
        ),
        (
            [_embedded(), _embedded(space="other-space")],
            'err("index-embedding-incompatible", {kind: space})',
        ),
    ],
)
def test_local_embedding_failures_precede_declassification(corpus, expected):
    env, fixture, audits = _env(lambda *_args: None)
    env.set("embedded_fixture", corpus)
    result = run_source(_source(), env)
    assert format_display(result) == expected
    assert fixture.attempt_count == 0
    assert audits == []


def test_malformed_chunk_fails_locally_without_attempt():
    malformed = _embedded()
    malformed = malformed.put("chunk", malformed.get("chunk").put("text", ""))
    env, fixture, audits = _env(lambda *_args: None)
    env.set("embedded_fixture", [malformed])
    result = run_source(_source(), env)
    assert format_display(result) == 'err("chunk-invalid", {stage: document})'
    assert fixture.attempt_count == 0
    assert audits == []


@pytest.mark.parametrize(
    "observation, expected",
    [
        (
            GeniaOptionErr("index-timeout", _map(timeout_ms=1000)),
            'err("index-timeout", {timeout_ms: 1000})',
        ),
        (
            GeniaOptionErr(
                "index-rate-limited",
                _map(retry_after_ms=GeniaOptionNone("index-retry-after-unavailable")),
            ),
            'err("index-rate-limited", {retry_after_ms: none("index-retry-after-unavailable")})',
        ),
        (
            GeniaOptionErr("index-rejected", _map(kind=symbol("permission"))),
            'err("index-rejected", {kind: permission})',
        ),
        (
            GeniaOptionErr("index-transport-failure", _map(kind=symbol("unavailable"))),
            'err("index-transport-failure", {kind: unavailable})',
        ),
    ],
)
def test_exact_provider_errors_are_preserved(observation, expected):
    env, fixture, audits = _env(lambda *_args: observation)
    env.set("embedded_fixture", [_embedded()])
    result = run_source(_source(), env)
    assert format_display(result) == expected
    assert fixture.attempt_count == 1
    assert len(audits) == 1


@pytest.mark.parametrize(
    "observation, stage",
    [
        (None, "provider_response"),
        (GeniaOptionSome("forged"), "index_handle"),
        (GeniaOptionErr("wrong", _map(secret=PAYLOAD)), "provider_response"),
    ],
)
def test_malformed_provider_observation_is_non_sensitive(observation, stage):
    env, fixture, audits = _env(lambda *_args: observation)
    env.set("embedded_fixture", [_embedded()])
    result = run_source(_source(), env)
    assert format_display(result) == f'err("index-response-invalid", {{stage: {stage}}})'
    assert KEY not in repr(result) and PAYLOAD not in repr(result)
    assert CONFIG_ID not in repr(result)
    assert fixture.attempt_count == 1
    assert len(audits) == 1


def test_provider_exception_is_transport_failure_without_retry_or_leak():
    def fail(*_args):
        raise RuntimeError(f"provider exploded {KEY} {PAYLOAD} {CONFIG_ID}")

    env, fixture, audits = _env(fail)
    env.set("embedded_fixture", [_embedded()])
    result = run_source(_source(), env)
    assert format_display(result) == 'err("index-transport-failure", {kind: other})'
    assert KEY not in repr(result) and PAYLOAD not in repr(result)
    assert CONFIG_ID not in repr(result)
    assert fixture.attempt_count == 1
    assert len(audits) == 1


def test_handle_cannot_be_hashed_keyed_copied_or_serialized():
    from genia.retrieval import create_fixture_index_result

    env, _fixture, _audits = _env(
        lambda *_args: GeniaOptionSome(create_fixture_index_result(object()))
    )
    env.set("embedded_fixture", [_embedded()])
    handle = run_source(_source(), env).value
    env.set("index_handle_fixture", handle)

    with pytest.raises(TypeError, match="index handles cannot be hashed"):
        hash(handle)
    with pytest.raises(TypeError, match="index handles cannot be map keys"):
        GeniaMap().put(handle, True)
    with pytest.raises(TypeError, match="index handles cannot be copied"):
        copy.copy(handle)
    with pytest.raises(TypeError, match="index handles cannot be copied"):
        copy.deepcopy(handle)
    encoded = run_source("json_encode(index_handle_fixture)", env)
    assert isinstance(encoded, GeniaOptionErr)
    assert format_display(encoded) == (
        "err(unsupported_json_value, {kind: json, operation: encode, status: error, "
        "reason: unsupported_json_value, value_type: index-handle})"
    )


def test_authority_mismatch_prevents_attempt():
    env, fixture, audits = _env(lambda *_args: None)
    config_provider = env.get("provider_fixture")
    env.set(
        "index_authority_fixture",
        create_declassification_authority(
            config_provider, [symbol("embed_call")], audits.append
        ),
    )
    env.set("embedded_fixture", [_embedded()])
    with pytest.raises(TypeError, match="authority does not permit"):
        run_source(_source(), env)
    assert fixture.attempt_count == 0
    assert len(audits) == 1 and audits[0]["success"] is False


def test_fixture_factory_and_global_environment_are_narrow():
    from genia.retrieval import create_fixture_index_provider

    with pytest.raises(TypeError, match="callable handler"):
        create_fixture_index_provider(42)
    env = make_global_env([])
    assert "index" in env.values
    for name in (
        "index_provider_fixture",
        "index_credential_fixture",
        "index_authority_fixture",
        "index_retry",
        "index_batch",
    ):
        assert name not in env.values
