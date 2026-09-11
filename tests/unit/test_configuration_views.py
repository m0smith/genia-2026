import pytest

import genia.configuration as configuration
from genia.builtins import make_global_env
from genia.interpreter import run_source
from genia.utf8 import format_debug
from genia.values import GeniaOptionNone, GeniaOptionSome, GeniaProtected, GeniaSymbol


def _run(source: str):
    return run_source(source, make_global_env([]))


def _provider():
    return _run(
        'config_provider([{kind: quote(values), values: {'
        'SERVER_PORT: "8080", OPENAI_TOKEN: "payload"}}]) |> unwrap_or(none)'
    )


def test_construction_is_inert_and_each_call_delegates_exactly_once(monkeypatch):
    provider = _provider()
    calls = []
    expected = GeniaOptionSome("result")

    def lookup(actual_provider, key):
        calls.append((actual_provider, key))
        return expected

    monkeypatch.setattr(configuration, "get_configuration", lookup)
    view = make_global_env([]).get("config_view")(provider, "SERVER_")

    assert calls == []
    assert view("PORT") is expected
    assert calls == [(provider, "SERVER_PORT")]


def test_secret_view_preserves_provider_identity_purpose_and_protected_value():
    """The view must acquire exactly what a direct acquisition would.

    R18 (#793): this can no longer be checked with `==`. Protected equality
    observes carrier identity only, and the view's carrier and the direct
    carrier are two independent acquisitions, so they are correctly unequal.
    Comparing them with `==` would only work if equality compared payloads,
    which is precisely the oracle R18 removes.

    The equivalence is therefore established through the authorized
    declassification boundary — the only supported way to reach a payload —
    which also proves both carriers accept the *same* provider and purpose.
    """
    provider = _provider()
    result = make_global_env([]).get("secret_view")(
        provider, "OPENAI_", GeniaSymbol("model_call")
    )("TOKEN")

    assert isinstance(result, GeniaOptionSome)
    assert isinstance(result.value, GeniaProtected)
    direct = configuration.get_secret_configuration(
        provider, "OPENAI_TOKEN", GeniaSymbol("model_call")
    )
    assert isinstance(direct.value, GeniaProtected)

    # Two independent acquisitions are distinct carriers.
    assert result.value != direct.value

    authority = configuration.create_declassification_authority(
        provider, [GeniaSymbol("model_call")], lambda event: None
    )
    view_allowed, view_purpose, view_payload = result.value._declassify_with(authority)
    direct_allowed, direct_purpose, direct_payload = direct.value._declassify_with(
        authority
    )

    assert view_allowed is True and direct_allowed is True
    assert view_purpose == direct_purpose == "model_call"
    assert view_payload == direct_payload


def test_secret_view_construction_is_inert_and_delegates_exactly_once(monkeypatch):
    provider = _provider()
    purpose = GeniaSymbol("model_call")
    calls = []
    expected = GeniaOptionSome("protected-result")

    def lookup(actual_provider, key, actual_purpose):
        calls.append((actual_provider, key, actual_purpose))
        return expected

    monkeypatch.setattr(configuration, "get_secret_configuration", lookup)
    view = make_global_env([]).get("secret_view")(provider, "OPENAI_", purpose)

    assert calls == []
    assert view("TOKEN") is expected
    assert calls == [(provider, "OPENAI_TOKEN", purpose)]


def test_empty_prefix_and_missing_are_exact_r10_results():
    provider = _provider()
    view = make_global_env([]).get("config_view")(provider, "")

    found = view("SERVER_PORT")
    missing = view("MISSING")

    assert isinstance(found, GeniaOptionSome) and found.value == "8080"
    assert isinstance(missing, GeniaOptionNone)
    assert missing.reason == "config-missing" and missing.context is None


@pytest.mark.parametrize(
    ("source", "message"),
    [
        ("config_view(1, \"P_\")", "config_view expected a configuration provider, received int"),
        (
            "config_view(config_provider([]) |> unwrap_or(none), 1)",
            "config_view expected a prefix string without NUL, received int",
        ),
        (
            'config_view(config_provider([]) |> unwrap_or(none), "P_")("")',
            "config_view expected a non-empty logical name string without NUL, received string",
        ),
        (
            'secret_view(config_provider([]) |> unwrap_or(none), "P_", "purpose")',
            "secret_view expected a non-empty purpose symbol",
        ),
    ],
)
def test_view_misuse_is_exact_and_non_revealing(source, message):
    with pytest.raises(TypeError, match=message):
        _run(source)


def test_invalid_logical_name_performs_no_lookup_and_leaks_no_sentinel(monkeypatch):
    provider = _provider()
    calls = []

    def lookup(*args):
        calls.append(args)
        raise AssertionError("lookup must not run")

    monkeypatch.setattr(configuration, "get_configuration", lookup)
    view = make_global_env([]).get("config_view")(provider, "PREFIX_SENTINEL_")

    with pytest.raises(TypeError) as excinfo:
        view("LOGICAL_SENTINEL\0HIDDEN")

    assert calls == []
    rendered = str(excinfo.value)
    assert "PREFIX_SENTINEL" not in rendered
    assert "LOGICAL_SENTINEL" not in rendered
    assert rendered == (
        "config_view expected a non-empty logical name string without NUL, "
        "received string"
    )


def test_secret_view_remains_rejected_by_protected_sink():
    with pytest.raises(TypeError, match="protected-value: print"):
        _run(
            'provider = config_provider([{kind: quote(values), values: {P_K: "payload"}}]) |> unwrap_or(none)\n'
            'secret = secret_view(provider, "P_", quote(outbound))\n'
            'print(secret("K") |> unwrap_or(none))'
        )

    assert "payload" not in format_debug(
        _run(
            'provider = config_provider([{kind: quote(values), values: {P_K: "payload"}}]) |> unwrap_or(none)\n'
            'secret_view(provider, "P_", quote(outbound))("K")'
        )
    )
