import pytest

from genia.builtins import make_global_env
from genia.interpreter import run_source
from genia.utf8 import format_debug, format_display
from genia.values import GeniaMap, GeniaOptionErr, GeniaOptionSome, GeniaProtected, GeniaSymbol


def _standard(*, environment=None, dotenv=None):
    env = make_global_env(
        [],
        environment_snapshot_provider=environment,
        dotenv_snapshot_provider=dotenv,
    )
    return env, env.get("config_standard")


def test_config_standard_uses_fixed_precedence_and_optional_conventional_dotenv():
    calls = []

    def environment():
        calls.append("environment")
        return {"PAIR_TWO_THREE": "environment", "PAIR_ONE_TWO": "environment"}

    def dotenv(path):
        calls.append(("dotenv", path))
        return b"PAIR_TWO_THREE=dotenv\nONLY_DOTENV=dotenv"

    env, standard = _standard(environment=environment, dotenv=dotenv)
    result = standard(
        GeniaMap().put("PAIR_ZERO_ONE", "overrides").put("ALL", "overrides"),
        [
            "--pair-zero-one",
            "arguments",
            "--pair-one-two",
            "arguments",
            "--all",
            "arguments",
        ],
    )

    assert isinstance(result, GeniaOptionSome)
    provider = result.value
    get = env.get("config_get")
    assert get(provider, "PAIR_ZERO_ONE").value == "overrides"
    assert get(provider, "PAIR_ONE_TWO").value == "arguments"
    assert get(provider, "PAIR_TWO_THREE").value == "environment"
    assert get(provider, "ONLY_DOTENV").value == "dotenv"
    assert get(provider, "ALL").value == "overrides"
    assert calls == ["environment", ("dotenv", ".env")]


def test_config_standard_explicit_path_is_required_and_keeps_dotenv_at_index_three():
    seen = []

    def missing(path):
        seen.append(path)
        raise FileNotFoundError("PATH_SENTINEL_674")

    _, standard = _standard(environment=lambda: {}, dotenv=missing)
    result = standard(GeniaMap(), [], "application.env")

    assert isinstance(result, GeniaOptionErr)
    assert result.reason == "config-provider-failure"
    assert result.context.items() == [
        ["source_index", 3],
        ["source_kind", GeniaSymbol("dotenv")],
        ["stage", GeniaSymbol("acquire")],
    ]
    assert seen == ["application.env"]
    assert "PATH_SENTINEL_674" not in format_debug(result)
    assert "application.env" not in format_debug(result)


def test_config_standard_optional_absence_is_an_empty_fixed_position_source():
    def missing(path):
        raise FileNotFoundError(path)

    env, standard = _standard(environment=lambda: {}, dotenv=missing)
    result = standard(GeniaMap(), [])

    assert isinstance(result, GeniaOptionSome)
    missing_result = env.get("config_get")(result.value, "ANY")
    assert format_display(missing_result) == 'none("config-missing")'


def test_config_standard_malformed_args_short_circuit_host_acquisition():
    calls = []
    _, standard = _standard(
        environment=lambda: calls.append("environment") or {},
        dotenv=lambda path: calls.append(path) or b"A=1",
    )

    result = standard(GeniaMap(), ["--bad_name", "value"])

    assert isinstance(result, GeniaOptionErr)
    assert result.reason == "config-source-invalid"
    assert result.context.items() == [
        ["source_kind", GeniaSymbol("arguments")],
        ["stage", GeniaSymbol("parse")],
    ]
    assert calls == []


@pytest.mark.parametrize(
    "overrides,args,path",
    [
        (1, [], None),
        (GeniaMap().put("A", 1), [], None),
        (GeniaMap(), ["--a", 1], None),
        (GeniaMap(), [], ""),
        (GeniaMap(), [], "SAFE\0PATH"),
    ],
)
def test_config_standard_runtime_misuse_precedes_acquisition(overrides, args, path):
    calls = []
    _, standard = _standard(
        environment=lambda: calls.append("environment") or {},
        dotenv=lambda selected: calls.append(selected) or b"",
    )

    with pytest.raises(TypeError, match="config_standard expected") as excinfo:
        if path is None:
            standard(overrides, args)
        else:
            standard(overrides, args, path)

    assert calls == []
    assert "SAFE" not in str(excinfo.value)


def test_config_standard_snapshots_inputs_and_views_consume_provider_unchanged():
    environment_values = {"SERVER_PORT": "environment", "OPENAI_API_KEY": "secret-before"}
    dotenv_bytes = [b"SERVER_PORT=dotenv"]
    env, standard = _standard(
        environment=lambda: environment_values,
        dotenv=lambda path: dotenv_bytes[0],
    )
    overrides = GeniaMap().put("SERVER_PORT", "overrides")
    args = ["--db-port", "5432"]
    provider = standard(overrides, args).value

    overrides = overrides.put("SERVER_PORT", "mutated")
    args[:] = ["--db-port", "9999"]
    environment_values["OPENAI_API_KEY"] = "secret-after"
    dotenv_bytes[0] = b"SERVER_PORT=after"

    assert env.get("config_view")(provider, "SERVER_")("PORT").value == "overrides"
    assert env.get("config_view")(provider, "DB_")("PORT").value == "5432"
    protected = env.get("secret_view")(provider, "OPENAI_", GeniaSymbol("model_call"))(
        "API_KEY"
    ).value
    assert isinstance(protected, GeniaProtected)
    assert format_display(protected) == "<protected>"
    assert "secret-before" not in format_debug(protected)
