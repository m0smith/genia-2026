import pytest

from genia.builtins import make_global_env
from genia.interpreter import run_source
from genia.sheet import GeniaSheet
from genia.utf8 import format_debug, format_display
from genia.values import (
    GeniaMap,
    GeniaOptionErr,
    GeniaOptionNone,
    GeniaOptionSome,
    GeniaProtected,
    GeniaSymbol,
)


KEY_SENTINEL = "KEY_SENTINEL_591"
PAYLOAD_SENTINEL = "PAYLOAD_SENTINEL_591"
PURPOSE_SENTINEL = "PURPOSE_SENTINEL_591"


def _run(source: str):
    return run_source(source, make_global_env([]))


def _provider_source(values: str) -> str:
    return (
        "config_provider([{kind: quote(values), values: {"
        + values
        + "}}]) |> unwrap_or(none)"
    )


def _sentinel_provider_source() -> str:
    return _provider_source(f'{KEY_SENTINEL}: "{PAYLOAD_SENTINEL}"')


def test_secret_get_protects_found_and_empty_but_preserves_missing():
    result = _run(
        f"""
        provider = {_provider_source(f'{KEY_SENTINEL}: "{PAYLOAD_SENTINEL}", EMPTY: ""')}
        [
          secret_get(provider, "{KEY_SENTINEL}", quote({PURPOSE_SENTINEL})),
          secret_get(provider, "EMPTY", quote(empty_use)),
          secret_get(provider, "MISSING", quote(missing_use))
        ]
        """
    )

    assert isinstance(result[0], GeniaOptionSome)
    assert isinstance(result[0].value, GeniaProtected)
    assert isinstance(result[1], GeniaOptionSome)
    assert isinstance(result[1].value, GeniaProtected)
    assert isinstance(result[2], GeniaOptionNone)
    assert result[2].reason == "config-missing"
    rendered = format_debug(result)
    assert PAYLOAD_SENTINEL not in rendered
    assert KEY_SENTINEL not in rendered
    assert PURPOSE_SENTINEL not in rendered


def test_secret_get_or_is_lazy_and_protects_only_successes():
    result = _run(
        f"""
        calls = ref(0)
        fallback() = {{ ref_update(calls, (n) -> n + 1) "{PAYLOAD_SENTINEL}" }}
        provider = {_provider_source('FOUND: "found"')}
        [
          secret_get_or(provider, "FOUND", quote(use), fallback),
          secret_get_or(provider, "MISSING", quote(use), fallback),
          secret_get_or(provider, "NONE", quote(use), () -> none("absent")),
          secret_get_or(provider, "ERR", quote(use), () -> err("failed")),
          ref_get(calls)
        ]
        """
    )

    assert isinstance(result[0].value, GeniaProtected)
    assert isinstance(result[1].value, GeniaProtected)
    assert isinstance(result[2], GeniaOptionNone) and result[2].reason == "absent"
    assert isinstance(result[3], GeniaOptionErr) and result[3].reason == "failed"
    assert result[4] == 1


def test_secret_get_or_rejects_a_default_success_containing_protection():
    env = make_global_env([])
    protected = run_source(
        f"provider = {_sentinel_provider_source()}\n"
        f'secret_get(provider, "{KEY_SENTINEL}", quote(first_use)) |> unwrap_or(none)',
        env,
    )
    env.set("protected_fixture", protected)
    with pytest.raises(
        TypeError, match="default success cannot contain a protected value"
    ):
        run_source(
            "provider = config_provider([]) |> unwrap_or(none)\n"
            'secret_get_or(provider, "MISSING", quote(second_use), () -> [protected_fixture])',
            env,
        )


def test_protected_match_returns_exact_subject_and_named_pattern_binds_it():
    env = make_global_env([])
    protected = run_source(
        f"provider = {_sentinel_provider_source()}\n"
        f'secret_get(provider, "{KEY_SENTINEL}", quote({PURPOSE_SENTINEL})) |> unwrap_or(none)',
        env,
    )
    direct = env.get("protected_match")("secret", protected)
    assert isinstance(direct, GeniaOptionSome)
    assert direct.value is protected

    env.set("protected_fixture", protected)
    matched = run_source(
        'pattern Secret(value) = protected_match("secret", value)\n'
        "extract(value) = Secret(bound) -> bound | _ -> none\n"
        "extract(protected_fixture)",
        env,
    )
    assert matched is protected


def test_reserved_secret_facet_rejects_all_generic_carrier_operations_without_leak():
    provider = _run(_sentinel_provider_source())
    protected = make_global_env([]).get("secret_get")(
        provider, KEY_SENTINEL, _run(f"quote({PURPOSE_SENTINEL})")
    ).value

    operations = (
        ("represent", ["secret", PAYLOAD_SENTINEL]),
        ("representation_match", ["secret", protected]),
        ("strip_representation", ["secret", protected]),
    )
    env = make_global_env([])
    for name, args in operations:
        with pytest.raises(TypeError) as excinfo:
            env.get(name)(*args)
        text = str(excinfo.value)
        assert text == f'{name} cannot use reserved protected facet "secret"'
        assert PAYLOAD_SENTINEL not in text
        assert KEY_SENTINEL not in text
        assert PURPOSE_SENTINEL not in text


def test_protected_equality_includes_provider_purpose_and_payload_without_rendering_them():
    result = _run(
        f"""
        p1 = {_sentinel_provider_source()}
        p2 = {_sentinel_provider_source()}
        a = secret_get(p1, "{KEY_SENTINEL}", quote(first)) |> unwrap_or(none)
        b = secret_get(p1, "{KEY_SENTINEL}", quote(first)) |> unwrap_or(none)
        c = secret_get(p1, "{KEY_SENTINEL}", quote(second)) |> unwrap_or(none)
        d = secret_get(p2, "{KEY_SENTINEL}", quote(first)) |> unwrap_or(none)
        [a == b, a == c, a == d, a == "{PAYLOAD_SENTINEL}"]
        """
    )
    assert result == [True, False, False, False]


def test_protected_values_are_not_map_keys_and_errors_do_not_leak():
    protected = _run(
        f"provider = {_sentinel_provider_source()}\n"
        f'secret_get(provider, "{KEY_SENTINEL}", quote({PURPOSE_SENTINEL})) |> unwrap_or(none)'
    )
    with pytest.raises(TypeError, match="protected values cannot be map keys") as map_error:
        GeniaMap().put(protected, "value")
    text = str(map_error.value)
    assert PAYLOAD_SENTINEL not in text
    assert KEY_SENTINEL not in text
    assert PURPOSE_SENTINEL not in text


def test_exact_protected_leaf_transports_through_containers_pipeline_flow_sheet_and_ref():
    env = make_global_env([])
    protected = run_source(
        f"provider = {_sentinel_provider_source()}\n"
        f'secret_get(provider, "{KEY_SENTINEL}", quote({PURPOSE_SENTINEL})) |> unwrap_or(none)',
        env,
    )
    env.set("protected_fixture", protected)
    result = run_source(
        """
        holder = ref(protected_fixture)
        sheet_value = sheet([["credential", [protected_fixture]]])
        [
          protected_fixture |> ((x) -> x),
          [protected_fixture] |> map((x) -> x) |> first |> unwrap_or(none),
          [protected_fixture] |> each((x) -> x) |> collect |> first |> unwrap_or(none),
          rows(sheet_value) |> first |> unwrap_or(none) |> ((row) -> row_get(row, "credential")),
          ref_get(holder)
        ]
        """,
        env,
    )
    assert all(item is protected for item in result)
    assert isinstance(
        run_source('sheet([["credential", [protected_fixture]]])', env), GeniaSheet
    )


def test_protected_leaf_is_opaque_to_ordinary_derivation_and_all_observations_are_sentinel_free():
    env = make_global_env([])
    protected = _run(
        f"provider = {_sentinel_provider_source()}\n"
        f'secret_get(provider, "{KEY_SENTINEL}", quote({PURPOSE_SENTINEL})) |> unwrap_or(none)'
    )
    assert format_display(protected) == "<protected>"
    assert format_debug(protected) == "<protected>"
    env.set("protected_fixture", protected)
    derived = run_source('protected_fixture + "suffix"', env)
    assert isinstance(derived, GeniaOptionNone)
    assert derived.reason == "type-error"
    assert derived.context.get("left") == "protected"
    observed = "\n".join(
        (repr(protected), format_display(protected), format_debug(protected), format_debug(derived))
    )
    assert PAYLOAD_SENTINEL not in observed
    assert KEY_SENTINEL not in observed
    assert PURPOSE_SENTINEL not in observed


@pytest.mark.parametrize("source", [
    'secret_get(config_provider([]) |> unwrap_or(none), "K", "purpose")',
])
def test_invalid_purpose_is_non_sensitive_runtime_misuse(source):
    with pytest.raises((TypeError, ValueError, SyntaxError)) as excinfo:
        _run(source)
    assert KEY_SENTINEL not in str(excinfo.value)
    assert PAYLOAD_SENTINEL not in str(excinfo.value)

    provider = _run("config_provider([]) |> unwrap_or(none)")
    with pytest.raises(TypeError, match="expected a non-empty purpose symbol"):
        make_global_env([]).get("secret_get")(provider, "K", GeniaSymbol(""))
