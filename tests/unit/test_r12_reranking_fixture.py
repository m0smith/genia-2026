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


KEY = "R12_RERANK_KEY_SENTINEL_647"
PAYLOAD = "R12_RERANK_PAYLOAD_SENTINEL_647"
CONFIG_ID = "R12_RERANK_CONFIG_SENTINEL_647"


def _map(**values):
    result = GeniaMap()
    for key, value in values.items():
        result = result.put(key, value)
    return result


def _chunk(text="hello", doc_id="doc-1", *, offset=0, origin="fixture"):
    return _map(
        text=text,
        source=_map(doc_id=doc_id, offset=offset, length=len(text)),
        meta=GeniaRepresented("json", _map(origin=origin)),
    )


def _retrieved(chunk, score):
    return _map(chunk=chunk, score=score)


def _env(handler):
    from genia.retrieval import create_fixture_rerank_provider

    env = make_global_env([])
    config_provider = run_source(
        "config_provider([{kind: quote(values), values: {"
        f'{KEY}: "{PAYLOAD}"'
        "}}]) |> unwrap_or(none)",
        env,
    )
    env.set("config_provider_fixture", config_provider)
    credential = run_source(
        f'secret_get(config_provider_fixture, "{KEY}", quote(rerank_call)) |> unwrap_or(none)',
        env,
    )
    audits = []
    authority = create_declassification_authority(
        config_provider, [symbol("rerank_call")], audits.append
    )
    provider = create_fixture_rerank_provider(handler)
    env.set("rerank_provider_fixture", provider)
    env.set("rerank_credential_fixture", credential)
    env.set("rerank_authority_fixture", authority)
    return env, provider, audits


def _source(query='"which?"', evidence="evidence_fixture", config=None):
    config = config or f'{{id: "{CONFIG_ID}", timeout_ms: 1000}}'
    return (
        f"rr = rerank(rerank_provider_fixture, {config}, "
        "rerank_credential_fixture, rerank_authority_fixture)\n"
        f"rr({query}, {evidence})"
    )


def test_success_reorders_and_rescores_exact_chunks_once():
    from genia.retrieval import create_fixture_rerank_result

    first = _chunk("first", "doc-1", origin="one")
    second = _chunk("second", "doc-2", offset=4, origin="two")
    evidence = [_retrieved(first, 0.1), _retrieved(second, 0.2)]
    seen = []

    def handler(config, query, supplied, credential):
        seen.append((config, query, supplied, credential))
        return GeniaOptionSome(
            create_fixture_rerank_result(
                [_retrieved(second, 9.5), _retrieved(first, -2)]
            )
        )

    env, provider, audits = _env(handler)
    env.set("evidence_fixture", evidence)
    result = run_source(_source(), env)

    assert isinstance(result, GeniaOptionSome)
    assert [item.get("chunk") for item in result.value] == [second, first]
    assert [item.get("score") for item in result.value] == [9.5, -2]
    assert result.value[0].get("chunk") is second
    assert result.value[1].get("chunk") is first
    assert provider.attempt_count == 1
    assert len(audits) == 1 and audits[0]["success"] is True
    assert seen[0][1:] == ("which?", evidence, PAYLOAD)


def test_repeated_exact_chunk_occurrences_preserve_multiplicity():
    from genia.retrieval import create_fixture_rerank_result

    repeated = _chunk("same")
    other = _chunk("other", "doc-2")
    evidence = [
        _retrieved(repeated, 0.1),
        _retrieved(other, 0.2),
        _retrieved(repeated, 0.3),
    ]
    output = [
        _retrieved(repeated, 3),
        _retrieved(repeated, 2),
        _retrieved(other, 1),
    ]
    env, provider, audits = _env(
        lambda *_args: GeniaOptionSome(create_fixture_rerank_result(output))
    )
    env.set("evidence_fixture", evidence)
    result = run_source(_source(), env)
    assert isinstance(result, GeniaOptionSome)
    assert [item.get("chunk") for item in result.value] == [repeated, repeated, other]
    assert provider.attempt_count == 1
    assert len(audits) == 1


def test_empty_valid_evidence_short_paths_without_declassification_or_attempt():
    env, provider, audits = _env(lambda *_args: pytest.fail("must not attempt"))
    env.set("evidence_fixture", [])
    result = run_source(_source(), env)
    assert isinstance(result, GeniaOptionSome) and result.value == []
    assert provider.attempt_count == 0
    assert audits == []


def test_constructor_is_inert_and_capability_is_opaque():
    env, provider, audits = _env(lambda *_args: None)
    result = run_source(
        f'rerank(rerank_provider_fixture, {{id: "{CONFIG_ID}", timeout_ms: 1000}}, '
        "rerank_credential_fixture, rerank_authority_fixture)",
        env,
    )
    assert repr(result) == "<function>"
    assert repr(provider) == "<rerank-provider>"
    assert format_display(provider) == "<rerank-provider>"
    assert format_debug(provider) == "<rerank-provider>"
    assert provider.attempt_count == 0
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
    env, provider, audits = _env(lambda *_args: None)
    env.set("evidence_fixture", [])
    with pytest.raises(TypeError, match=message):
        run_source(_source(config=config), env)
    assert provider.attempt_count == 0
    assert audits == []


@pytest.mark.parametrize(
    "query, evidence, message",
    [
        ('""', "[]", "query"),
        ("1", "[]", "query"),
        ('"q"', "1", "list of retrieved chunks"),
        ('"q"', "[{chunk: {text: \"x\"}, score: 1}]", "retrieved chunk"),
        ('"q"', "[{chunk: valid_chunk_fixture, score: true}]", "score"),
        ('"q"', "[{chunk: valid_chunk_fixture, score: 1, extra: 2}]", "retrieved chunk"),
    ],
)
def test_invalid_invocation_precedes_declassification(query, evidence, message):
    env, provider, audits = _env(lambda *_args: None)
    env.set("valid_chunk_fixture", _chunk())
    with pytest.raises(TypeError, match=message):
        run_source(_source(query=query, evidence=evidence), env)
    assert provider.attempt_count == 0
    assert audits == []


def test_protected_evidence_is_rejected_before_attempt():
    env, provider, audits = _env(lambda *_args: None)
    env.set("protected_fixture", env.get("rerank_credential_fixture"))
    with pytest.raises(TypeError, match="protected-value: rerank-input"):
        run_source(_source(evidence="[protected_fixture]"), env)
    assert provider.attempt_count == 0
    assert audits == []


@pytest.mark.parametrize(
    "observation, expected",
    [
        (
            GeniaOptionErr("rerank-timeout", _map(timeout_ms=1000)),
            'err("rerank-timeout", {timeout_ms: 1000})',
        ),
        (
            GeniaOptionErr(
                "rerank-rate-limited",
                _map(
                    retry_after_ms=GeniaOptionNone(
                        "rerank-retry-after-unavailable"
                    )
                ),
            ),
            'err("rerank-rate-limited", {retry_after_ms: none("rerank-retry-after-unavailable")})',
        ),
        (
            GeniaOptionErr("rerank-rejected", _map(kind=symbol("permission"))),
            'err("rerank-rejected", {kind: permission})',
        ),
        (
            GeniaOptionErr(
                "rerank-transport-failure", _map(kind=symbol("unavailable"))
            ),
            'err("rerank-transport-failure", {kind: unavailable})',
        ),
    ],
)
def test_exact_provider_errors_are_preserved(observation, expected):
    env, provider, audits = _env(lambda *_args: observation)
    env.set("evidence_fixture", [_retrieved(_chunk(), 0.5)])
    result = run_source(_source(), env)
    assert format_display(result) == expected
    assert provider.attempt_count == 1
    assert len(audits) == 1


def _success(results):
    from genia.retrieval import create_fixture_rerank_result

    return GeniaOptionSome(create_fixture_rerank_result(results))


@pytest.mark.parametrize(
    "make_results",
    [
        lambda chunk: "not-a-list",
        lambda chunk: [_map(chunk=chunk)],
        lambda chunk: [_retrieved(chunk, math.nan)],
        lambda chunk: [_retrieved(chunk, math.inf)],
        lambda chunk: [_retrieved(chunk, True)],
        lambda chunk: [],
        lambda chunk: [_retrieved(chunk, 1), _retrieved(chunk, 2)],
        lambda chunk: [_retrieved(_chunk("changed"), 1)],
        lambda chunk: [_retrieved(chunk.put("meta", GeniaRepresented("json", _map(origin="changed"))), 1)],
    ],
)
def test_malformed_or_non_preserving_success_is_result_invalid(make_results):
    chunk = _chunk()
    env, provider, audits = _env(lambda *_args: _success(make_results(chunk)))
    env.set("evidence_fixture", [_retrieved(chunk, 0.5)])
    result = run_source(_source(), env)
    assert format_display(result) == (
        'err("rerank-response-invalid", {stage: result})'
    )
    assert KEY not in repr(result) and PAYLOAD not in repr(result)
    assert CONFIG_ID not in repr(result)
    assert provider.attempt_count == 1
    assert len(audits) == 1


@pytest.mark.parametrize(
    "observation",
    [
        None,
        GeniaOptionSome("forged"),
        GeniaOptionErr("wrong", _map(secret=PAYLOAD)),
    ],
)
def test_malformed_observation_is_provider_response_invalid(observation):
    env, provider, audits = _env(lambda *_args: observation)
    env.set("evidence_fixture", [_retrieved(_chunk(), 0.5)])
    result = run_source(_source(), env)
    assert format_display(result) == (
        'err("rerank-response-invalid", {stage: provider_response})'
    )
    assert KEY not in repr(result) and PAYLOAD not in repr(result)
    assert CONFIG_ID not in repr(result)
    assert provider.attempt_count == 1
    assert len(audits) == 1


def test_provider_exception_is_transport_failure_without_retry_or_leak():
    def fail(*_args):
        raise RuntimeError(f"provider exploded {KEY} {PAYLOAD} {CONFIG_ID}")

    env, provider, audits = _env(fail)
    env.set("evidence_fixture", [_retrieved(_chunk(), 0.5)])
    result = run_source(_source(), env)
    assert format_display(result) == (
        'err("rerank-transport-failure", {kind: other})'
    )
    assert KEY not in repr(result) and PAYLOAD not in repr(result)
    assert CONFIG_ID not in repr(result)
    assert provider.attempt_count == 1
    assert len(audits) == 1


def test_authority_mismatch_prevents_attempt():
    env, provider, audits = _env(lambda *_args: None)
    env.set("evidence_fixture", [_retrieved(_chunk(), 0.5)])
    config_provider = env.get("config_provider_fixture")
    env.set(
        "rerank_authority_fixture",
        create_declassification_authority(
            config_provider, [symbol("retrieve_call")], audits.append
        ),
    )
    with pytest.raises(TypeError, match="authority does not permit"):
        run_source(_source(), env)
    assert provider.attempt_count == 0
    assert len(audits) == 1 and audits[0]["success"] is False


def test_fixture_factory_and_global_environment_are_narrow():
    from genia.retrieval import create_fixture_rerank_provider

    with pytest.raises(TypeError, match="callable handler"):
        create_fixture_rerank_provider(42)
    env = make_global_env([])
    assert "rerank" in env.values
    for name in (
        "rerank_provider_fixture",
        "rerank_credential_fixture",
        "rerank_authority_fixture",
        "rerank_retry",
        "rerank_local",
    ):
        assert name not in env.values
