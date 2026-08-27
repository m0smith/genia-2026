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
    symbol,
)


KEY = "R12_RETRIEVE_KEY_SENTINEL_646"
PAYLOAD = "R12_RETRIEVE_PAYLOAD_SENTINEL_646"
CONFIG_ID = "R12_RETRIEVE_CONFIG_SENTINEL_646"
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


def _embedded(chunk=None, vector=None, dims=None, space=SPACE):
    vector = [0.25, -1, 3.5] if vector is None else vector
    return _map(
        chunk=_chunk() if chunk is None else chunk,
        embedding=_map(
            vector=vector,
            dims=len(vector) if dims is None else dims,
            space=space,
        ),
    )


def _query(text="hello", vector=None, dims=None, space=SPACE):
    vector = [0.25, -1, 3.5] if vector is None else vector
    return _map(
        text=text,
        embedding=_map(
            vector=vector,
            dims=len(vector) if dims is None else dims,
            space=space,
        ),
    )


def _retrieved(chunk, score):
    return _map(chunk=chunk, score=score)


def _env(handler, corpus=None):
    from genia.retrieval import (
        create_fixture_index_provider,
        create_fixture_index_result,
        create_fixture_retrieve_provider,
    )

    env = make_global_env([])
    config_provider = run_source(
        "config_provider([{kind: quote(values), values: {"
        f'{KEY}: "{PAYLOAD}"'
        "}}]) |> unwrap_or(none)",
        env,
    )
    env.set("config_provider_fixture", config_provider)
    index_credential = run_source(
        f'secret_get(config_provider_fixture, "{KEY}", quote(index_call)) |> unwrap_or(none)',
        env,
    )
    retrieve_credential = run_source(
        f'secret_get(config_provider_fixture, "{KEY}", quote(retrieve_call)) |> unwrap_or(none)',
        env,
    )
    index_audits = []
    retrieve_audits = []
    index_authority = create_declassification_authority(
        config_provider, [symbol("index_call")], index_audits.append
    )
    retrieve_authority = create_declassification_authority(
        config_provider, [symbol("retrieve_call")], retrieve_audits.append
    )
    index_provider = create_fixture_index_provider(
        lambda *_args: GeniaOptionSome(create_fixture_index_result(object()))
    )
    retrieve_provider = create_fixture_retrieve_provider(index_provider, handler)
    env.set("index_provider_fixture", index_provider)
    env.set("index_credential_fixture", index_credential)
    env.set("index_authority_fixture", index_authority)
    env.set("retrieve_provider_fixture", retrieve_provider)
    env.set("retrieve_credential_fixture", retrieve_credential)
    env.set("retrieve_authority_fixture", retrieve_authority)
    corpus = [_embedded()] if corpus is None else corpus
    env.set("embedded_corpus_fixture", corpus)
    handle = run_source(
        f'i = index(index_provider_fixture, {{id: "index", timeout_ms: 1000}}, '
        "index_credential_fixture, index_authority_fixture)\n"
        "i(embedded_corpus_fixture) |> unwrap_or(none)",
        env,
    )
    env.set("index_handle_fixture", handle)
    env.set("query_embedding_fixture", _query())
    return env, index_provider, retrieve_provider, index_audits, retrieve_audits


def _source(query="query_embedding_fixture", k="2", config=None):
    config = config or f'{{id: "{CONFIG_ID}", timeout_ms: 1000}}'
    return (
        f"r = retrieve(retrieve_provider_fixture, {config}, "
        "retrieve_credential_fixture, retrieve_authority_fixture)\n"
        f"r(index_handle_fixture, {query}, {k})"
    )


def test_matching_query_attempts_once_and_preserves_best_first_exact_chunks():
    from genia.retrieval import create_fixture_retrieve_result

    first = _chunk("first", "doc-1")
    second = _chunk("second", "doc-2")
    corpus = [_embedded(first), _embedded(second)]
    seen = []

    def handler(config, backend_ref, query, k, credential):
        seen.append((config, backend_ref, query, k, credential))
        return GeniaOptionSome(
            create_fixture_retrieve_result(
                [_retrieved(second, 0.2), _retrieved(first, 0.9)]
            )
        )

    env, _index, fixture, _index_audits, audits = _env(handler, corpus)
    result = run_source(_source(), env)

    assert isinstance(result, GeniaOptionSome)
    assert [item.get("chunk") for item in result.value] == [second, first]
    assert [item.get("score") for item in result.value] == [0.2, 0.9]
    assert result.value[0].get("chunk") is second
    assert result.value[1].get("chunk") is first
    assert fixture.attempt_count == 1
    assert len(audits) == 1 and audits[0]["success"] is True
    assert seen[0][2] is env.get("query_embedding_fixture")
    assert seen[0][3:] == (2, PAYLOAD)


def test_valid_empty_result_is_exact_absence():
    from genia.retrieval import create_fixture_retrieve_result

    env, _index, fixture, _index_audits, audits = _env(
        lambda *_args: GeniaOptionSome(create_fixture_retrieve_result([]))
    )
    result = run_source(_source(), env)
    assert format_display(result) == 'none("retrieval-no-results")'
    assert fixture.attempt_count == 1
    assert len(audits) == 1


def test_constructor_is_inert_and_capability_is_opaque():
    env, _index, fixture, _index_audits, audits = _env(lambda *_args: None)
    result = run_source(
        f'retrieve(retrieve_provider_fixture, {{id: "{CONFIG_ID}", timeout_ms: 1000}}, '
        "retrieve_credential_fixture, retrieve_authority_fixture)",
        env,
    )
    assert repr(result) == "<function>"
    assert repr(fixture) == "<retrieve-provider>"
    assert format_display(fixture) == "<retrieve-provider>"
    assert format_debug(fixture) == "<retrieve-provider>"
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
    env, _index, fixture, _index_audits, audits = _env(lambda *_args: None)
    with pytest.raises(TypeError, match=message):
        run_source(_source(config=config), env)
    assert fixture.attempt_count == 0
    assert audits == []


@pytest.mark.parametrize(
    "query, k, message",
    [
        ('{text: "", embedding: {vector: [1], dims: 1, space: "s"}}', "2", "query text"),
        ('{text: "x", embedding: {vector: [], dims: 0, space: "s"}}', "2", "embedding vector"),
        ('{text: "x", embedding: {vector: [1], dims: 2, space: "s"}}', "2", "embedding dims"),
        ('{text: "x", embedding: {vector: [1], dims: 1, space: ""}}', "2", "embedding space"),
        ('{text: "x", embedding: {vector: [1], dims: 1, space: "s"}, extra: 1}', "2", "closed query embedding"),
        ("query_embedding_fixture", "true", "k"),
        ("query_embedding_fixture", "0", "k"),
        ("query_embedding_fixture", "1001", "k"),
    ],
)
def test_invalid_query_or_k_precedes_declassification(query, k, message):
    env, _index, fixture, _index_audits, audits = _env(lambda *_args: None)
    with pytest.raises(TypeError, match=message):
        run_source(_source(query=query, k=k), env)
    assert fixture.attempt_count == 0
    assert audits == []


def test_protected_query_field_is_rejected_before_attempt():
    env, _index, fixture, _index_audits, audits = _env(lambda *_args: None)
    env.set("protected_query_fixture", env.get("retrieve_credential_fixture"))
    with pytest.raises(TypeError, match="protected-value: retrieve-input"):
        run_source(
            _source(
                query='{text: protected_query_fixture, embedding: {vector: [1], dims: 1, space: "s"}}'
            ),
            env,
        )
    assert fixture.attempt_count == 0
    assert audits == []


def test_capability_mismatch_precedes_space_and_dimension_checks():
    from genia.retrieval import (
        create_fixture_index_provider,
        create_fixture_retrieve_provider,
    )

    env, _index, _fixture, _index_audits, audits = _env(lambda *_args: None)
    other_index = create_fixture_index_provider(lambda *_args: None)
    other_retriever = create_fixture_retrieve_provider(other_index, lambda *_args: None)
    env.set("retrieve_provider_fixture", other_retriever)
    env.set("query_embedding_fixture", _query(vector=[1], space="other-space"))
    result = run_source(_source(), env)
    assert format_display(result) == (
        'err("retrieve-capability-incompatible", {kind: index_handle})'
    )
    assert other_retriever.attempt_count == 0
    assert audits == []


def test_space_mismatch_precedes_dimension_check():
    env, _index, fixture, _index_audits, audits = _env(lambda *_args: None)
    env.set("query_embedding_fixture", _query(vector=[1], space="other-space"))
    result = run_source(_source(), env)
    assert format_display(result) == (
        'err("retrieve-embedding-incompatible", {kind: space})'
    )
    assert fixture.attempt_count == 0
    assert audits == []


def test_dimension_mismatch_follows_space_check():
    env, _index, fixture, _index_audits, audits = _env(lambda *_args: None)
    env.set("query_embedding_fixture", _query(vector=[1], space=SPACE))
    result = run_source(_source(), env)
    assert format_display(result) == (
        'err("retrieve-embedding-incompatible", {kind: dimension})'
    )
    assert fixture.attempt_count == 0
    assert audits == []


@pytest.mark.parametrize(
    "observation, expected",
    [
        (
            GeniaOptionErr("retrieve-timeout", _map(timeout_ms=1000)),
            'err("retrieve-timeout", {timeout_ms: 1000})',
        ),
        (
            GeniaOptionErr(
                "retrieve-rate-limited",
                _map(
                    retry_after_ms=GeniaOptionNone(
                        "retrieve-retry-after-unavailable"
                    )
                ),
            ),
            'err("retrieve-rate-limited", {retry_after_ms: none("retrieve-retry-after-unavailable")})',
        ),
        (
            GeniaOptionErr("retrieve-rejected", _map(kind=symbol("permission"))),
            'err("retrieve-rejected", {kind: permission})',
        ),
        (
            GeniaOptionErr(
                "retrieve-transport-failure", _map(kind=symbol("unavailable"))
            ),
            'err("retrieve-transport-failure", {kind: unavailable})',
        ),
    ],
)
def test_exact_provider_errors_are_preserved(observation, expected):
    env, _index, fixture, _index_audits, audits = _env(lambda *_args: observation)
    result = run_source(_source(), env)
    assert format_display(result) == expected
    assert fixture.attempt_count == 1
    assert len(audits) == 1


@pytest.mark.parametrize(
    "results, stage",
    [
        ("not-a-list", "result"),
        ([_map(chunk=_chunk())], "result"),
        ([_retrieved(_chunk().put("text", ""), 1.0)], "chunk"),
        ([_retrieved(_chunk(), math.nan)], "score"),
        ([_retrieved(_chunk(), math.inf)], "score"),
        ([_retrieved(_chunk(), True)], "score"),
        ([_retrieved(_chunk(), 1.0), _retrieved(_chunk(), 0.5)], "limit"),
        ([_retrieved(_chunk("not indexed", "other"), 1.0)], "provenance"),
    ],
)
def test_malformed_success_normalizes_to_exact_stage(results, stage):
    from genia.retrieval import create_fixture_retrieve_result

    env, _index, fixture, _index_audits, audits = _env(
        lambda *_args: GeniaOptionSome(create_fixture_retrieve_result(results))
    )
    result = run_source(_source(k="1"), env)
    assert format_display(result) == (
        f'err("retrieve-response-invalid", {{stage: {stage}}})'
    )
    assert KEY not in repr(result) and PAYLOAD not in repr(result)
    assert CONFIG_ID not in repr(result)
    assert fixture.attempt_count == 1
    assert len(audits) == 1


@pytest.mark.parametrize(
    "observation, stage",
    [
        (None, "provider_response"),
        (GeniaOptionSome("forged"), "provider_response"),
        (GeniaOptionErr("wrong", _map(secret=PAYLOAD)), "provider_response"),
    ],
)
def test_malformed_observation_is_non_sensitive(observation, stage):
    env, _index, fixture, _index_audits, audits = _env(lambda *_args: observation)
    result = run_source(_source(), env)
    assert format_display(result) == (
        f'err("retrieve-response-invalid", {{stage: {stage}}})'
    )
    assert KEY not in repr(result) and PAYLOAD not in repr(result)
    assert CONFIG_ID not in repr(result)
    assert fixture.attempt_count == 1
    assert len(audits) == 1


def test_provider_exception_is_transport_failure_without_retry_or_leak():
    def fail(*_args):
        raise RuntimeError(f"provider exploded {KEY} {PAYLOAD} {CONFIG_ID}")

    env, _index, fixture, _index_audits, audits = _env(fail)
    result = run_source(_source(), env)
    assert format_display(result) == (
        'err("retrieve-transport-failure", {kind: other})'
    )
    assert KEY not in repr(result) and PAYLOAD not in repr(result)
    assert CONFIG_ID not in repr(result)
    assert fixture.attempt_count == 1
    assert len(audits) == 1


def test_authority_mismatch_prevents_attempt():
    env, _index, fixture, _index_audits, audits = _env(lambda *_args: None)
    provider = env.get("config_provider_fixture")
    env.set(
        "retrieve_authority_fixture",
        create_declassification_authority(
            provider, [symbol("embed_call")], audits.append
        ),
    )
    with pytest.raises(TypeError, match="authority does not permit"):
        run_source(_source(), env)
    assert fixture.attempt_count == 0
    assert len(audits) == 1 and audits[0]["success"] is False


def test_fixture_factory_and_global_environment_are_narrow():
    from genia.retrieval import (
        create_fixture_index_provider,
        create_fixture_retrieve_provider,
    )

    index_provider = create_fixture_index_provider(lambda *_args: None)
    with pytest.raises(TypeError, match="index provider"):
        create_fixture_retrieve_provider(42, lambda *_args: None)
    with pytest.raises(TypeError, match="callable handler"):
        create_fixture_retrieve_provider(index_provider, 42)
    env = make_global_env([])
    assert "retrieve" in env.values
    for name in (
        "retrieve_provider_fixture",
        "retrieve_credential_fixture",
        "retrieve_authority_fixture",
        "retrieve_retry",
        "retrieve_and_embed",
        "rerank",
    ):
        assert name not in env.values
