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

    env = make_global_env([])
    encoded = env.get("_json_encode")(first)
    assert isinstance(encoded, GeniaOptionErr)
    assert str(encoded.reason) == "unsupported_json_value"
    assert "config-provider" in format_debug(encoded)
    legacy_encoded = env.get("_json_stringify")(first)
    assert isinstance(legacy_encoded, GeniaOptionNone)
    assert legacy_encoded.reason == "json-stringify-error"
    assert "config-provider" in format_debug(legacy_encoded)


@pytest.mark.parametrize(
    ("source", "message"),
    [
        ("config_provider(1)", "expected a list of source descriptors, received int"),
        ("config_provider([1])", "expected a source descriptor map at index 0, received int"),
        ("config_provider([{}])", "expected a source kind symbol at index 0, received none"),
        (
            'config_provider([{kind: "values", values: {}}])',
            "expected a source kind symbol at index 0, received string",
        ),
        (
            "config_provider([{kind: quote(remote)}])",
            "received unsupported source kind at index 0",
        ),
        (
            "config_get(1, \"A\")",
            "config_get expected a configuration provider, received int",
        ),
    ],
)
def test_provider_programmer_misuse_is_exact_and_non_revealing(source, message):
    with pytest.raises(TypeError, match=message):
        _run(source)


def test_invalid_environment_snapshot_is_normalized_without_raw_data():
    result = _run(
        "config_provider([{kind: quote(environment)}])",
        environment_snapshot_provider=lambda: {"SENSITIVE_ENVIRONMENT_KEY": 42},
    )

    assert isinstance(result, GeniaOptionErr)
    assert result.reason == "config-provider-failure"
    rendered = format_debug(result)
    assert "SENSITIVE_ENVIRONMENT_KEY" not in rendered
    assert "42" not in rendered


def test_config_get_or_invokes_default_once_only_for_missing_lookup():
    result = _run(
        """
        calls = ref(0)
        fallback() = {
          ref_update(calls, (n) -> n + 1)
          "fallback"
        }
        provider = config_provider([{kind: quote(values), values: {FOUND: "value", EMPTY: ""}}]) |> unwrap_or(none)
        [
          config_get_or(provider, "FOUND", fallback),
          config_get_or(provider, "EMPTY", fallback),
          config_get_or(provider, "MISSING", fallback),
          ref_get(calls)
        ]
        """
    )

    assert [item.value for item in result[:3]] == ["value", "", "fallback"]
    assert result[3] == 1


def test_config_get_or_flattens_outcome_defaults_and_wraps_falsey_values():
    result = _run(
        """
        provider = config_provider([]) |> unwrap_or(none)
        [
          config_get_or(provider, "A", () -> some("ready")),
          config_get_or(provider, "B", () -> none("not-available")),
          config_get_or(provider, "C", () -> err("default-failed")),
          config_get_or(provider, "D", () -> false),
          config_get_or(provider, "E", () -> 0),
          config_get_or(provider, "F", () -> "")
        ]
        """
    )

    assert isinstance(result[0], GeniaOptionSome) and result[0].value == "ready"
    assert isinstance(result[1], GeniaOptionNone) and result[1].reason == "not-available"
    assert isinstance(result[2], GeniaOptionErr) and result[2].reason == "default-failed"
    assert isinstance(result[3], GeniaOptionSome) and result[3].value is False
    assert isinstance(result[4], GeniaOptionSome) and result[4].value == 0
    assert isinstance(result[5], GeniaOptionSome) and result[5].value == ""


def test_config_get_or_composes_explicit_conversion_and_callable_template():
    result = _run(
        """
        pattern Port(value) = refinement_match((n) -> n > 0, value)
        provider = config_provider([{kind: quote(values), values: {GOOD: "8080", BAD: "not-int", RANGE: "70000"}}]) |> unwrap_or(none)
        [
          config_get_or(provider, "GOOD", () -> "3000") |> parse_int |> Port,
          config_get_or(provider, "MISSING", () -> "3000") |> parse_int |> Port,
          config_get_or(provider, "BAD", () -> "3000") |> parse_int |> Port,
          config_get_or(provider, "RANGE", () -> "3000") |> parse_int |> ((n) -> refinement_match((x) -> x <= 65535, n))
        ]
        """
    )

    assert isinstance(result[0], GeniaOptionSome) and result[0].value == 8080
    assert isinstance(result[1], GeniaOptionSome) and result[1].value == 3000
    assert isinstance(result[2], GeniaOptionNone) and result[2].reason == "parse-error"
    assert isinstance(result[3], GeniaOptionNone) and result[3].reason == "refinement-mismatch"


def test_config_get_or_default_misuse_is_lazy_and_missing_branch_only():
    found = _run(
        """
        provider = config_provider([{kind: quote(values), values: {FOUND: "value"}}]) |> unwrap_or(none)
        [config_get_or(provider, "FOUND", 42), config_get_or(provider, "FOUND", (x) -> x)]
        """
    )
    assert [item.value for item in found] == ["value", "value"]

    with pytest.raises(TypeError, match="callable value"):
        _run(
            """
            provider = config_provider([]) |> unwrap_or(none)
            config_get_or(provider, "MISSING", 42)
            """
        )

    with pytest.raises(TypeError, match="lambda expected 1 args, got 0"):
        _run(
            """
            provider = config_provider([]) |> unwrap_or(none)
            config_get_or(provider, "MISSING", (x) -> x)
            """
        )


def _symbol(name: str):
    from genia.values import symbol

    return symbol(name)
