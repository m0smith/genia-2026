"""P8 alternate-provider substitution proof for `retrieve/4` (issue #945).

Scope authority: issue #945, design
`docs/design/p8-alternate-provider-substitution-proof-design.md`.

Realization A: the existing fixed-order/fixed-score list-backed fixture
pattern (`hosts/python/exec_r12_grounded_fixture.py`,
`tests/unit/test_r12_retrieval_fixture.py`).

Realization B: `hosts.python.r12_retrieve_cosine_fixture` -- a dict-keyed
backend plus real computed cosine-similarity ranking with a deterministic
tie-break, installed through the same unmodified
`create_fixture_index_provider`/`create_fixture_retrieve_provider`
factories.

Both realizations are plain handler closures behind the unchanged
`GeniaRetrieveProvider`/`GeniaRetriever` classes. No `src/genia/retrieval.py`
change is required or made by this proof.
"""

from __future__ import annotations

import inspect
import math

import pytest

from genia.builtins import make_global_env
from genia.configuration import create_declassification_authority
from genia.interpreter import run_source
from genia.numeric_runtime import GeniaDecimal, GeniaRational
from genia.utf8 import format_debug, format_display
from genia.values import (
    GeniaMap,
    GeniaOptionErr,
    GeniaOptionNone,
    GeniaOptionSome,
    GeniaRepresented,
    symbol,
)
from genia.retrieval import (
    create_fixture_index_provider,
    create_fixture_index_result,
    create_fixture_retrieve_provider,
    create_fixture_retrieve_result,
)
from hosts.python.r12_retrieve_cosine_fixture import (
    build_cosine_index_handler,
    build_cosine_retrieve_handler,
)


KEY = "R12_RETRIEVE_ALT_KEY_SENTINEL_945"
PAYLOAD = "R12_RETRIEVE_ALT_PAYLOAD_SENTINEL_945"
CONFIG_ID = "R12_RETRIEVE_ALT_CONFIG_SENTINEL_945"
SPACE = "fixture-space-v1"


def _map(**values):
    result = GeniaMap()
    for key, value in values.items():
        result = result.put(key, value)
    return result


def _chunk(text, doc_id):
    return _map(
        text=text,
        source=_map(doc_id=doc_id, offset=0, length=len(text)),
        meta=GeniaRepresented("json", _map(origin="fixture")),
    )


def _embedded(chunk, vector, space=SPACE):
    return _map(
        chunk=chunk,
        embedding=_map(vector=vector, dims=len(vector), space=space),
    )


def _query(text="query", vector=None, dims=None, space=SPACE):
    vector = [1.0, 0.0] if vector is None else vector
    return _map(
        text=text,
        embedding=_map(vector=vector, dims=len(vector) if dims is None else dims, space=space),
    )


# Three chunks with genuinely distinct (non-degenerate) vectors so that
# realization B's computed cosine ranking can differ from realization A's
# fixed insertion-order ranking for a non-trivial query.
_CORPUS_CHUNKS = [_chunk(f"chunk-{i}", f"doc-{i}") for i in range(3)]
_CORPUS_VECTORS = [[1.0, 0.0], [0.0, 1.0], [0.7071067811865476, 0.7071067811865476]]


def _build_corpus():
    return [
        _embedded(_CORPUS_CHUNKS[i], _CORPUS_VECTORS[i]) for i in range(len(_CORPUS_CHUNKS))
    ]


# --- Realization A: existing fixed-order/fixed-score list-backed pattern ---
# (matches hosts/python/exec_r12_grounded_fixture.py and
# tests/unit/test_r12_retrieval_fixture.py's `_env` helper exactly; no new
# production code is required for this realization).


def _realization_a_index_handler(_config, corpus, _credential):
    return GeniaOptionSome(create_fixture_index_result(list(corpus)))


def _realization_a_retrieve_handler(_config, backend_ref, _query, k, _credential):
    return GeniaOptionSome(
        create_fixture_retrieve_result(
            [_map(chunk=item.get("chunk"), score=1.0) for item in backend_ref[:k]]
        )
    )


_REALIZATIONS = {
    "A": (_realization_a_index_handler, _realization_a_retrieve_handler),
    "B": (build_cosine_index_handler(), build_cosine_retrieve_handler()),
}


def _build_providers(realization, corpus=None):
    index_handler, retrieve_handler = _REALIZATIONS[realization]
    index_provider = create_fixture_index_provider(index_handler)
    retrieve_provider = create_fixture_retrieve_provider(index_provider, retrieve_handler)
    return index_provider, retrieve_provider


def _env(realization=None, corpus=None, index_provider=None, retrieve_provider=None):
    """Build an environment with one explicitly bound (index, retrieve)
    provider pairing. Explicit binding only: nothing here is ambient --
    every provider is an ordinary Python object passed by explicit
    ``env.set`` call, exactly mirroring the existing R12 fixture pattern.
    """

    if index_provider is None or retrieve_provider is None:
        index_provider, retrieve_provider = _build_providers(realization, corpus)

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
    env.set("index_provider_fixture", index_provider)
    env.set("index_credential_fixture", index_credential)
    env.set("index_authority_fixture", index_authority)
    env.set("retrieve_provider_fixture", retrieve_provider)
    env.set("retrieve_credential_fixture", retrieve_credential)
    env.set("retrieve_authority_fixture", retrieve_authority)
    corpus = _build_corpus() if corpus is None else corpus
    env.set("embedded_corpus_fixture", corpus)
    handle = run_source(
        'i = index(index_provider_fixture, {id: "index", timeout_ms: 1000}, '
        "index_credential_fixture, index_authority_fixture)\n"
        "i(embedded_corpus_fixture) |> unwrap_or(none)",
        env,
    )
    env.set("index_handle_fixture", handle)
    env.set("query_embedding_fixture", _query())
    return env, index_provider, retrieve_provider, retrieve_audits


def _source(query="query_embedding_fixture", k="2", config=None):
    config = config or f'{{id: "{CONFIG_ID}", timeout_ms: 1000}}'
    return (
        f"r = retrieve(retrieve_provider_fixture, {config}, "
        "retrieve_credential_fixture, retrieve_authority_fixture)\n"
        f"r(index_handle_fixture, {query}, {k})"
    )


# ---------------------------------------------------------------------------
# Required-evidence item 1: same application logic across both realizations
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("realization", ["A", "B"])
def test_same_application_logic_produces_contract_conformant_results(realization):
    """The exact same Genia-source call sequence, exercised against both
    realizations, produces a contract-conformant Outcome from either --
    the application-facing source (`_source()`) is byte-for-byte identical
    for A and B; only the host-side provider construction differs."""

    env, _index, provider, audits = _env(realization)
    result = run_source(_source(k="2"), env)

    assert isinstance(result, GeniaOptionSome)
    assert 1 <= len(result.value) <= 2
    seen_texts = set()
    for item in result.value:
        assert isinstance(item, GeniaMap)
        chunk = item.get("chunk")
        score = item.get("score")
        assert chunk in _CORPUS_CHUNKS
        assert chunk.get("text") not in seen_texts
        seen_texts.add(chunk.get("text"))
        assert isinstance(score, float) or isinstance(score, int)
        assert math.isfinite(score)
    assert provider.attempt_count == 1
    assert len(audits) == 1 and audits[0]["success"] is True


# ---------------------------------------------------------------------------
# Required-evidence item 2: explicit binding only, no ambient discovery
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("realization", ["A", "B"])
def test_binding_is_explicit_and_never_ambient(realization):
    """The retrieve provider is only reachable because the test explicitly
    called ``env.set("retrieve_provider_fixture", ...)``; an environment
    that never receives that explicit call has no way to resolve the name
    at all (no default/global/current-provider fallback exists)."""

    bare_env = make_global_env([])
    with pytest.raises(Exception):
        run_source(_source(), bare_env)

    env, _index, provider, _audits = _env(realization)
    assert env.get("retrieve_provider_fixture") is provider
    # The binding call site is visible/traceable: it is the explicit
    # env.set call above, not a lookup by name/registry.


def test_realization_a_and_b_bindings_are_fully_independent():
    """Building both realizations' providers side by side proves the
    binding choice is a single explicit construction-time call: invoking
    realization A's callable never touches realization B's handler (or
    its attempt counter) and vice versa -- there is no ambiguous shared
    registry a binding could resolve against."""

    env_a, _index_a, provider_a, _audits_a = _env("A")
    env_b, _index_b, provider_b, _audits_b = _env("B")

    run_source(_source(), env_a)
    assert provider_a.attempt_count == 1
    assert provider_b.attempt_count == 0

    run_source(_source(), env_b)
    assert provider_a.attempt_count == 1
    assert provider_b.attempt_count == 1


# ---------------------------------------------------------------------------
# Required-evidence item 3: exact interface/revision match accepted
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("realization", ["A", "B"])
def test_valid_pairing_passes_all_three_compatibility_guards(realization):
    """A retrieve provider built via ``create_fixture_retrieve_provider``
    from the same index provider that produced the handle under test must
    pass E12-4's identity/space/dims guards regardless of which handler
    (A's or B's) it wraps."""

    env, _index, provider, audits = _env(realization)
    result = run_source(_source(), env)
    assert not (isinstance(result, GeniaOptionErr) and result.reason.startswith("retrieve-capability"))
    assert not (isinstance(result, GeniaOptionErr) and result.reason.startswith("retrieve-embedding"))
    assert provider.attempt_count == 1
    assert len(audits) == 1


# ---------------------------------------------------------------------------
# Required-evidence item 4: equivalent portable observations, differing
# content
# ---------------------------------------------------------------------------


def test_outcome_shape_identical_content_may_differ_across_realizations():
    env_a, _ia, _pa, _aud_a = _env("A")
    env_b, _ib, _pb, _aud_b = _env("B")

    # A non-degenerate query that is not axis-aligned with any corpus
    # vector, so realization B's computed ranking is free to differ from
    # realization A's fixed insertion order.
    query = _query(vector=[0.0, 1.0])
    env_a.set("query_embedding_fixture", query)
    env_b.set("query_embedding_fixture", query)

    result_a = run_source(_source(k="3"), env_a)
    result_b = run_source(_source(k="3"), env_b)

    # Outcome shape: both are `some([{chunk, score}, ...])` of the same
    # cardinality bound, over exactly the same corpus chunks.
    assert isinstance(result_a, GeniaOptionSome)
    assert isinstance(result_b, GeniaOptionSome)
    assert len(result_a.value) == len(result_b.value) == 3
    chunks_a = [item.get("chunk") for item in result_a.value]
    chunks_b = [item.get("chunk") for item in result_b.value]
    assert set(id(c) for c in chunks_a) == set(id(c) for c in chunks_b)
    for item in result_a.value + result_b.value:
        assert isinstance(item.get("score"), (int, float))
        assert math.isfinite(item.get("score"))

    # Realization A always returns the fixed score 1.0 for every result;
    # realization B returns a genuine, non-constant computed cosine
    # similarity -- content legitimately differs (R12 Replaceability).
    assert all(score == 1.0 for score in (item.get("score") for item in result_a.value))
    assert any(score != 1.0 for score in (item.get("score") for item in result_b.value))
    # Realization B ranks the axis-aligned [0,1] corpus vector first for a
    # [0,1] query -- a real ranking decision realization A cannot make
    # (its order is always fixed insertion order).
    assert chunks_b[0].get("text") == "chunk-1"


# ---------------------------------------------------------------------------
# Required-evidence item 5: provider-specific internals stay below the
# boundary
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("realization", ["A", "B"])
def test_no_provider_internal_object_is_observable_from_outcome(realization):
    env, index_provider, provider, _audits = _env(realization)
    result = run_source(_source(), env)

    rendered = repr(result) + format_display(result) + format_debug(result)
    # Neither a raw dict/list backend_ref, nor the compatibility identity
    # object, nor any Python id()-shaped token ever appears.
    assert "dict" not in rendered.lower() or "backend" not in rendered.lower()
    assert "object at 0x" not in rendered
    assert repr(provider) == "<retrieve-provider>"
    assert format_display(provider) == "<retrieve-provider>"
    assert format_debug(provider) == "<retrieve-provider>"
    assert repr(index_provider) == "<index-provider>"


# ---------------------------------------------------------------------------
# Required-evidence item 6: normalized failure behavior (handler raises)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("realization", ["A", "B"])
def test_handler_exception_normalizes_without_raw_traceback(realization):
    def fail(*_args):
        raise RuntimeError(f"provider exploded {KEY} {PAYLOAD} {CONFIG_ID}")

    index_provider, _valid_provider = _build_providers(realization)
    broken_provider = create_fixture_retrieve_provider(index_provider, fail)
    env, _index, _provider, audits = _env(
        index_provider=index_provider, retrieve_provider=broken_provider
    )
    result = run_source(_source(), env)
    assert format_display(result) == 'err("retrieve-transport-failure", {kind: other})'
    assert KEY not in repr(result) and PAYLOAD not in repr(result)
    assert "RuntimeError" not in repr(result)
    assert broken_provider.attempt_count == 1
    assert len(audits) == 1


# ---------------------------------------------------------------------------
# Required-evidence item 7: P3/P4 numeric matrix (Integer/Decimal/Rational/
# Float64) and non-numeric evidence values survive intact
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("realization", ["A", "B"])
@pytest.mark.parametrize(
    "score",
    [
        7,
        GeniaDecimal(15, -1),
        GeniaRational(1, 3),
        2.5,
    ],
    ids=["integer", "decimal", "rational", "float64"],
)
def test_numeric_score_kinds_survive_intact_through_both_realizations(realization, score):
    """`_is_finite_score` explicitly accepts int/float/GeniaDecimal/
    GeniaRational; this proves each kind crosses the shared interface
    unchanged for either realization's handler."""

    corpus = [_embedded(_CORPUS_CHUNKS[0], _CORPUS_VECTORS[0])]

    def handler(_config, backend_ref, _query, _k, _credential):
        if isinstance(backend_ref, list):
            chunk = backend_ref[0].get("chunk")
        else:
            chunk = backend_ref[0]["chunk"]
        return GeniaOptionSome(create_fixture_retrieve_result([_map(chunk=chunk, score=score)]))

    index_handler = _REALIZATIONS[realization][0]
    index_provider = create_fixture_index_provider(index_handler)
    retrieve_provider = create_fixture_retrieve_provider(index_provider, handler)
    env, _index, provider, audits = _env(
        corpus=corpus, index_provider=index_provider, retrieve_provider=retrieve_provider
    )
    result = run_source(_source(k="1"), env)
    assert isinstance(result, GeniaOptionSome)
    assert len(result.value) == 1
    assert result.value[0].get("score") == score
    assert type(result.value[0].get("score")) is type(score)
    assert provider.attempt_count == 1
    assert len(audits) == 1


@pytest.mark.parametrize("realization", ["A", "B"])
def test_non_numeric_evidence_values_survive_intact(realization):
    """Chunk text/source/meta (non-numeric evidence fields) round-trip
    exactly for either realization."""

    env, _index, _provider, _audits = _env(realization)
    result = run_source(_source(k="3"), env)
    assert isinstance(result, GeniaOptionSome)
    for item in result.value:
        chunk = item.get("chunk")
        assert chunk in _CORPUS_CHUNKS
        assert chunk.get("meta").facet == "json"
        assert chunk.get("meta").value.get("origin") == "fixture"


# ---------------------------------------------------------------------------
# Required-evidence item 8: R18 equality unchanged
# ---------------------------------------------------------------------------


def test_r18_equality_is_unchanged_by_this_proof():
    """Nothing in this proof touches R18 equality; a quick regression
    check that Genia's R18 structural equality (`genia_equal`, the same
    engine `==` uses) still holds for two independently constructed equal
    chunk maps. (`GeniaMap` itself defines no Python `__eq__` -- host
    identity is intentional per R18; the R18 boundary is `genia_equal`.)"""

    from genia.equality import genia_equal

    left = _chunk("same-text", "doc-x")
    right = _chunk("same-text", "doc-x")
    assert left is not right
    assert genia_equal(left, right) is True
    different = _chunk("other-text", "doc-x")
    assert genia_equal(left, different) is False


# ---------------------------------------------------------------------------
# Required-evidence item 9: R20 open-function dispatch unchanged
# ---------------------------------------------------------------------------


def test_no_r20_dispatch_participates_in_realization_selection():
    """`construct_retrieve`/`create_fixture_retrieve_provider` are plain
    Python functions, not R20 multi-clause dispatch objects; the
    realization choice happens entirely at host-side construction, never
    via pattern/guard dispatch."""

    from genia import retrieval

    assert inspect.isfunction(retrieval.construct_retrieve)
    assert inspect.isfunction(retrieval.create_fixture_retrieve_provider)
    source = inspect.getsource(retrieval)
    assert "open_function" not in source
    assert "dispatch" not in source.lower()


# ---------------------------------------------------------------------------
# Required-evidence item 10: R14 lifecycle -- not applicable, documented
# ---------------------------------------------------------------------------


def test_retrieve_does_not_interact_with_r14_lifecycle_scopes():
    """`retrieve/4` performs one direct handler attempt inside
    `GeniaRetriever.__call__`; it opens no lifecycle scope and imports no
    lifecycle module. Documented explicitly rather than skipped: R14
    lifecycle simply does not apply to this interface."""

    from genia import retrieval

    source = inspect.getsource(retrieval)
    assert "lifecycle" not in source.lower()


# ---------------------------------------------------------------------------
# Required-evidence item 11: Outcome semantics unchanged
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("realization", ["A", "B"])
def test_outcome_semantics_unchanged_some_none_err(realization):
    # some(...)
    env, _index, provider, _audits = _env(realization)
    some_result = run_source(_source(k="3"), env)
    assert isinstance(some_result, GeniaOptionSome)

    # none("retrieval-no-results")
    index_handler = _REALIZATIONS[realization][0]
    index_provider = create_fixture_index_provider(index_handler)
    empty_provider = create_fixture_retrieve_provider(
        index_provider, lambda *_args: GeniaOptionSome(create_fixture_retrieve_result([]))
    )
    empty_env, _i2, _p2, _a2 = _env(index_provider=index_provider, retrieve_provider=empty_provider)
    none_result = run_source(_source(), empty_env)
    assert isinstance(none_result, GeniaOptionNone)
    assert none_result.reason == "retrieval-no-results"

    # err(...)
    err_provider = create_fixture_retrieve_provider(
        index_provider,
        lambda *_args: GeniaOptionErr("retrieve-rejected", _map(kind=symbol("policy"))),
    )
    err_env, _i3, _p3, _a3 = _env(index_provider=index_provider, retrieve_provider=err_provider)
    err_result = run_source(_source(), err_env)
    assert isinstance(err_result, GeniaOptionErr)
    assert err_result.reason == "retrieve-rejected"


# ---------------------------------------------------------------------------
# Negative scenarios
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("realization", ["A", "B"])
def test_wrong_interface_revision_mismatched_dims_rejected(realization):
    env, _index, provider, audits = _env(realization)
    env.set("query_embedding_fixture", _query(vector=[1.0], space=SPACE))
    result = run_source(_source(), env)
    assert format_display(result) == 'err("retrieve-embedding-incompatible", {kind: dimension})'
    assert provider.attempt_count == 0
    assert audits == []


@pytest.mark.parametrize("realization", ["A", "B"])
def test_incompatible_provider_wrong_space_rejected(realization):
    env, _index, provider, audits = _env(realization)
    env.set("query_embedding_fixture", _query(vector=[1.0, 0.0], space="other-space"))
    result = run_source(_source(), env)
    assert format_display(result) == 'err("retrieve-embedding-incompatible", {kind: space})'
    assert provider.attempt_count == 0
    assert audits == []


@pytest.mark.parametrize("realization", ["A", "B"])
def test_incompatible_index_identity_rejected(realization):
    """A retrieve provider paired (via create_fixture_retrieve_provider)
    to a *different* index provider than the one that produced the
    handle under test must fail identity, regardless of handler."""

    env, _index, _provider, audits = _env(realization)
    other_index = create_fixture_index_provider(_realization_a_index_handler)
    other_retrieve_handler = _REALIZATIONS[realization][1]
    other_provider = create_fixture_retrieve_provider(other_index, other_retrieve_handler)
    env.set("retrieve_provider_fixture", other_provider)
    result = run_source(_source(), env)
    assert format_display(result) == 'err("retrieve-capability-incompatible", {kind: index_handle})'
    assert other_provider.attempt_count == 0
    assert audits == []


def test_ambiguous_binding_is_not_constructible_vacuously_satisfied():
    """R12 constructs exactly one `retrieve` callable per explicit
    `construct_retrieve` call; there is no registry or lookup that could
    resolve a name to more than one provider. There is therefore no
    constructible "ambiguous binding" scenario for `retrieve/4` -- every
    binding names its provider by explicit Python object reference. This
    test documents and proves that absence: two providers can coexist in
    the same environment (different variable names) without either ever
    being selected implicitly."""

    env_a, _ia, provider_a, _aa = _env("A")
    _ib, provider_b = _build_providers("B")
    env_a.set("other_retrieve_provider_fixture", provider_b)
    # Only the explicitly named `retrieve_provider_fixture` is ever used;
    # `other_retrieve_provider_fixture` sits unused in the same
    # environment with zero ambiguity.
    run_source(_source(), env_a)
    assert provider_a.attempt_count == 1
    assert provider_b.attempt_count == 0


@pytest.mark.parametrize(
    "bad_provider", [None, "not-a-provider", 42, GeniaMap()], ids=["nil", "string", "int", "map"]
)
def test_missing_or_wrong_type_provider_fails_closed(bad_provider):
    from genia.retrieval import construct_retrieve

    with pytest.raises(TypeError, match="retrieve provider capability"):
        construct_retrieve(bad_provider, _map(id="x", timeout_ms=1000), None, None)


@pytest.mark.parametrize("realization", ["A", "B"])
def test_provider_native_backend_object_never_leaks(realization):
    env, index_provider, provider, _audits = _env(realization)
    result = run_source(_source(k="3"), env)
    rendered = repr(result) + format_display(result) + format_debug(result)
    assert "_FixtureRetrieveResult" not in rendered
    assert "_FixtureIndexResult" not in rendered
    assert "GeniaIndexHandle" not in rendered
    assert repr(index_provider._compatibility_identity) not in rendered


@pytest.mark.parametrize("realization", ["A", "B"])
def test_index_handle_embedded_in_query_is_rejected_before_any_handler(realization):
    """Passing a Local-only/non-transferable index handle as if it were
    an ordinary boundary payload (embedded inside `query`'s map) is
    rejected as runtime misuse before either realization's handler ever
    runs."""

    env, _index, provider, audits = _env(realization)
    handle = env.get("index_handle_fixture")
    env.set("misused_query_fixture", handle)
    with pytest.raises(TypeError):
        run_source(
            _source(query='{text: "x", embedding: misused_query_fixture}'),
            env,
        )
    assert provider.attempt_count == 0
    assert audits == []


@pytest.mark.parametrize("realization", ["A", "B"])
@pytest.mark.parametrize("bad_score", [math.nan, math.inf, -math.inf], ids=["nan", "inf", "neg-inf"])
def test_malformed_nonfinite_score_rejected_for_both_realizations(realization, bad_score):
    """Realization B's real cosine scores are always finite by
    construction; this proves the shared `_is_finite_score` boundary
    still rejects a deliberately-broken handler variant returning a
    non-finite score, regardless of which realization's backend shape it
    otherwise mimics. GeniaDecimal/GeniaRational are always finite by
    construction (R22 exact arithmetic has no NaN/Infinity representation)
    so no analogous Decimal/Rational non-finite case exists to test."""

    index_handler = _REALIZATIONS[realization][0]
    index_provider = create_fixture_index_provider(index_handler)
    broken_provider = create_fixture_retrieve_provider(
        index_provider,
        lambda config, backend_ref, query, k, credential: GeniaOptionSome(
            create_fixture_retrieve_result(
                [_map(chunk=_CORPUS_CHUNKS[0], score=bad_score)]
            )
        ),
    )
    env, _index, provider, audits = _env(
        index_provider=index_provider, retrieve_provider=broken_provider
    )
    result = run_source(_source(k="1"), env)
    assert format_display(result) == 'err("retrieve-response-invalid", {stage: score})'
    assert provider.attempt_count == 1
    assert len(audits) == 1


@pytest.mark.parametrize("realization", ["A", "B"])
def test_normalized_provider_failure_never_leaks_raw_exception(realization):
    def fail(*_args):
        raise ValueError(f"internal detail {KEY} {PAYLOAD}")

    index_handler = _REALIZATIONS[realization][0]
    index_provider = create_fixture_index_provider(index_handler)
    broken_provider = create_fixture_retrieve_provider(index_provider, fail)
    env, _index, provider, audits = _env(
        index_provider=index_provider, retrieve_provider=broken_provider
    )
    result = run_source(_source(), env)
    assert format_display(result) == 'err("retrieve-transport-failure", {kind: other})'
    assert KEY not in repr(result)
    assert PAYLOAD not in repr(result)
    assert "ValueError" not in repr(result)
    assert "Traceback" not in repr(result)
    assert provider.attempt_count == 1
    assert len(audits) == 1
