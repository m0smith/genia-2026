import pytest

from genia.builtins import make_global_env
from genia.host_bridge import _genia_to_python_host
from genia.interpreter import run_source
from genia.utf8 import format_debug, format_display
from genia.values import GeniaMap, GeniaOptionErr, GeniaOptionNone, GeniaOptionSome


def _run(source: str, **env_kwargs):
    return run_source(source, make_global_env([], **env_kwargs))


def test_literal_provider_distinguishes_found_empty_and_missing():
    result = _run(
        """
        provider = config_provider([{kind: quote(values), values: {A: "x", EMPTY: ""}}]) |> unwrap_or(none)
        [config_get(provider, "A"), config_get(provider, "EMPTY"), config_get(provider, "MISSING")]
        """
    )

    assert isinstance(result[0], GeniaOptionSome) and result[0].value == "x"
    assert isinstance(result[1], GeniaOptionSome) and result[1].value == ""
    assert isinstance(result[2], GeniaOptionNone) and result[2].reason == "config-missing"
    assert result[2].context is None


def test_source_order_is_first_source_wins_and_repeat_lookup_is_stable():
    result = _run(
        """
        provider = config_provider([
          {kind: quote(values), values: {PORT: "9000"}},
          {kind: quote(values), values: {PORT: "8080"}}
        ]) |> unwrap_or(none)
        [config_get(provider, "PORT"), config_get(provider, "PORT")]
        """
    )

    assert [item.value for item in result] == ["9000", "9000"]


def test_environment_is_snapshotted_at_construction(monkeypatch):
    monkeypatch.setenv("GENIA_R10_SNAPSHOT", "before")
    env = make_global_env([])
    provider = run_source(
        "config_provider([{kind: quote(environment)}]) |> unwrap_or(none)", env
    )
    monkeypatch.setenv("GENIA_R10_SNAPSHOT", "after")

    lookup = env.get("config_get")(provider, "GENIA_R10_SNAPSHOT")
    next_provider = env.get("config_provider")([GeniaMap().put("kind", _symbol("environment"))])

    assert lookup.value == "before"
    assert next_provider.value is not provider
    assert env.get("config_get")(next_provider.value, "GENIA_R10_SNAPSHOT").value == "after"


def test_capability_is_not_called_for_literal_only_provider():
    calls = []

    def snapshot():
        calls.append(True)
        return {"A": "host"}

    result = _run(
        'config_provider([{kind: quote(values), values: {A: "literal"}}])',
        environment_snapshot_provider=snapshot,
    )

    assert isinstance(result, GeniaOptionSome)
    assert calls == []


def test_all_descriptors_validate_before_environment_capability_is_called():
    calls = []

    def snapshot():
        calls.append(True)
        return {}

    with pytest.raises(
        TypeError,
        match="config_provider expected a values map at index 1, received int",
    ):
        _run(
            "config_provider([{kind: quote(environment)}, {kind: quote(values), values: 1}])",
            environment_snapshot_provider=snapshot,
        )

    assert calls == []


def test_unavailable_and_failed_environment_sources_are_normalized():
    unavailable = _run(
        "config_provider([{kind: quote(environment)}])",
        environment_snapshot_provider=None,
    )

    def fail():
        raise RuntimeError("RAW HOST DETAIL MUST NOT LEAK")

    failed = _run(
        "config_provider([{kind: quote(values), values: {}}, {kind: quote(environment)}])",
        environment_snapshot_provider=fail,
    )

    assert isinstance(unavailable, GeniaOptionErr)
    assert unavailable.reason == "config-source-unavailable"
    assert unavailable.context.items() == [["source_index", 0]]
    assert isinstance(failed, GeniaOptionErr)
    assert failed.reason == "config-provider-failure"
    assert failed.context.items() == [["source_index", 1]]
    assert "RAW HOST DETAIL" not in format_debug(failed)


def test_invalid_key_diagnostic_does_not_include_key_text():
    provider = _run("config_provider([]) |> unwrap_or(none)")
    sentinel = "SECRET_KEY_NAME"

    with pytest.raises(TypeError) as excinfo:
        make_global_env([]).get("config_get")(provider, sentinel + "\0")

    assert sentinel not in str(excinfo.value)
    assert str(excinfo.value) == (
        "config_get expected a non-empty configuration key string without NUL, received string"
    )


def test_provider_is_opaque_identity_and_rejected_by_host_conversion():
    first = _run("config_provider([]) |> unwrap_or(none)")
    second = _run("config_provider([]) |> unwrap_or(none)")

    assert first is not second
    assert first != second
    assert format_display(first) == "<config-provider>"
    assert format_debug(first) == "<config-provider>"
    with pytest.raises(TypeError, match="python interop cannot convert config-provider"):
        _genia_to_python_host(first)
    with pytest.raises(TypeError, match="map key type is not supported"):
        GeniaMap().put(first, "value")


def _symbol(name: str):
    from genia.values import symbol

    return symbol(name)
